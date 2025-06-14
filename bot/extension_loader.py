import os
import discord
from discord.ext import commands
import logging
import importlib
import traceback
from dotenv import load_dotenv
import asyncio
import sys
import colorama
from colorama import Fore, Style, Back


colorama.init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    FORMATS = {
        logging.DEBUG: Fore.CYAN + "%(asctime)s - %(levelname)s - %(message)s" + Style.RESET_ALL,
        logging.INFO: Fore.GREEN + "%(asctime)s - %(levelname)s - %(message)s" + Style.RESET_ALL,
        logging.WARNING: Fore.YELLOW + "%(asctime)s - %(levelname)s - %(message)s" + Style.RESET_ALL,
        logging.ERROR: Fore.RED + "%(asctime)s - %(levelname)s - %(message)s" + Style.RESET_ALL,
        logging.CRITICAL: Back.RED + Fore.WHITE + "%(asctime)s - %(levelname)s - %(message)s" + Style.RESET_ALL
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


root_logger = logging.getLogger()
root_logger.handlers = []
root_handler = logging.StreamHandler()
root_handler.setFormatter(ColoredFormatter())
root_logger.addHandler(root_handler)
root_logger.setLevel(logging.WARNING)


logger = logging.getLogger('extension_loader')
logger.setLevel(logging.INFO)
logger.propagate = False


for handler in logger.handlers[:]:
    logger.removeHandler(handler)


handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter())
logger.addHandler(handler)

class ExtensionLoader(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.extensions_dir = "Extensions"
        self.loaded_extensions = []
        

        load_dotenv()
        

        self.auto_load = os.getenv("AutoExtension", "Off").lower() == "on"
    
    @commands.Cog.listener()
    async def on_ready(self):

        if self.auto_load:
            await self.load_all_extensions()
    
    async def load_all_extensions(self):

        logger.info(f"{Fore.CYAN}╔══════════════════════════════════════╗")
        logger.info(f"{Fore.CYAN}║      Auto-loading Extensions...      ║")
        logger.info(f"{Fore.CYAN}╚══════════════════════════════════════╝")
        

        if not os.path.exists(self.extensions_dir):
            logger.warning(f"Extensions directory '{self.extensions_dir}' not found.")
            return
            
        extension_files = [f[:-3] for f in os.listdir(self.extensions_dir) 
                          if f.endswith('.py') and not f.startswith('_')]
        

        success_count = 0
        fail_count = 0
        
        for extension in extension_files:
            try:
                extension_path = f"{self.extensions_dir}.{extension}"
                

                module = importlib.import_module(extension_path)
                

                if hasattr(module, 'setup'):

                    module.setup(self.bot)
                    
                    self.loaded_extensions.append(extension_path)
                    success_count += 1
                    logger.info(f"{Fore.GREEN}✓ Successfully loaded: {extension}")
                else:
                    raise ValueError(f"Extension {extension} has no setup function")
                    
            except Exception as e:
                fail_count += 1
                logger.error(f"{Fore.RED}✗ Failed to load: {extension}")
                logger.error(f"{Fore.RED}  Error: {str(e)}")
        

        logger.info(f"{Fore.CYAN}╔══════════════════════════════════════╗")
        logger.info(f"{Fore.CYAN}║      Extension Loading Summary       ║")
        logger.info(f"{Fore.CYAN}╠══════════════════════════════════════╣")
        logger.info(f"{Fore.CYAN}║ {Fore.GREEN}Loaded: {success_count}{Fore.CYAN} | {Fore.RED}Failed: {fail_count}{Fore.CYAN} | Total: {len(extension_files)} ║")
        logger.info(f"{Fore.CYAN}╚══════════════════════════════════════╝")
    
    async def load_extension(self, extension_name):

        try:

            module = importlib.import_module(extension_name)
            

            if hasattr(module, 'setup'):

                module.setup(self.bot)
                
                self.loaded_extensions.append(extension_name)
                return True
            else:
                raise ValueError(f"Extension {extension_name} has no setup function")
                
        except Exception as e:
            logger.error(f"{Fore.RED}Error loading {extension_name}: {str(e)}")
            return False
    
    async def unload_extension(self, extension_name):

        try:

            module_name = extension_name.split('.')[-1]
            

            for name, cog in list(self.bot.cogs.items()):

                if hasattr(cog, '__module__') and cog.__module__ == extension_name:
                    await self.bot.remove_cog(name)
            
            self.loaded_extensions.remove(extension_name)
            return True
        except Exception as e:
            logger.error(f"{Fore.RED}Error unloading {extension_name}: {str(e)}")
            return False
    
    async def reload_extension(self, extension_name):

        try:

            await self.unload_extension(extension_name)
            

            if extension_name in sys.modules:
                importlib.reload(sys.modules[extension_name])
            

            return await self.load_extension(extension_name)
        except Exception as e:
            logger.error(f"{Fore.RED}Error reloading {extension_name}: {str(e)}")
            return False
    
    @commands.group(name="extension", aliases=["ext"], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def extension_group(self, ctx):

        embed = discord.Embed(
            title="🧩 Extension Management",
            description="Use these commands to manage bot extensions",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Commands",
            value="`!extension list` - List all extensions\n"
                  "`!extension load <name>` - Load an extension\n"
                  "`!extension unload <name>` - Unload an extension\n"
                  "`!extension reload <name>` - Reload an extension\n"
                  "`!extension reloadall` - Reload all extensions",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @extension_group.command(name="list")
    @commands.has_permissions(administrator=True)
    async def list_extensions(self, ctx):


        if not os.path.exists(self.extensions_dir):
            await ctx.send("❌ Extensions directory not found.")
            return
            
        available_extensions = [f[:-3] for f in os.listdir(self.extensions_dir) 
                               if f.endswith('.py') and not f.startswith('_')]
        

        embed = discord.Embed(
            title="🧩 Extensions Status",
            description="List of available and loaded extensions",
            color=discord.Color.blue()
        )
        

        loaded_list = ""
        for ext in self.loaded_extensions:
            ext_name = ext.split('.')[-1]
            loaded_list += f"✅ {ext_name}\n"
        
        if loaded_list:
            embed.add_field(name="Loaded Extensions", value=loaded_list, inline=False)
        else:
            embed.add_field(name="Loaded Extensions", value="No extensions loaded", inline=False)
        

        not_loaded = [ext for ext in available_extensions 
                     if f"{self.extensions_dir}.{ext}" not in self.loaded_extensions]
        
        not_loaded_list = ""
        for ext in not_loaded:
            not_loaded_list += f"❌ {ext}\n"
        
        if not_loaded_list:
            embed.add_field(name="Available Extensions", value=not_loaded_list, inline=False)
        

        embed.set_footer(text=f"Auto-loading is {'enabled' if self.auto_load else 'disabled'}")
        
        await ctx.send(embed=embed)
    
    @extension_group.command(name="load")
    @commands.has_permissions(administrator=True)
    async def load_extension_cmd(self, ctx, extension_name: str):

        extension_path = f"{self.extensions_dir}.{extension_name}"
        

        if extension_path in self.loaded_extensions:
            await ctx.send(f"❌ Extension `{extension_name}` is already loaded.")
            return
        

        success = await self.load_extension(extension_path)
        
        if success:
            await ctx.send(f"✅ Successfully loaded extension `{extension_name}`.")
        else:
            await ctx.send(f"❌ Failed to load extension `{extension_name}`. Check logs for details.")
    
    @extension_group.command(name="unload")
    @commands.has_permissions(administrator=True)
    async def unload_extension_cmd(self, ctx, extension_name: str):

        extension_path = f"{self.extensions_dir}.{extension_name}"
        

        if extension_path not in self.loaded_extensions:
            await ctx.send(f"❌ Extension `{extension_name}` is not loaded.")
            return
        
        success = await self.unload_extension(extension_path)
        
        if success:
            await ctx.send(f"✅ Successfully unloaded extension `{extension_name}`.")
        else:
            await ctx.send(f"❌ Failed to unload extension `{extension_name}`. Check logs for details.")
    
    @extension_group.command(name="reload")
    @commands.has_permissions(administrator=True)
    async def reload_extension_cmd(self, ctx, extension_name: str):
       
        extension_path = f"{self.extensions_dir}.{extension_name}"
        
        if extension_path not in self.loaded_extensions:
            await ctx.send(f"❌ Extension `{extension_name}` is not loaded. Use `!extension load {extension_name}` first.")
            return
        
        success = await self.reload_extension(extension_path)
        
        if success:
            await ctx.send(f"✅ Successfully reloaded extension `{extension_name}`.")
        else:
            await ctx.send(f"❌ Failed to reload extension `{extension_name}`. Check logs for details.")
    
    @extension_group.command(name="reloadall")
    @commands.has_permissions(administrator=True)
    async def reload_all_extensions(self, ctx):
        
        if not self.loaded_extensions:
            await ctx.send("❌ No extensions are currently loaded.")
            return
        
        extensions_to_reload = self.loaded_extensions.copy()
        
        success_count = 0
        fail_count = 0
        
        for extension in extensions_to_reload:
            success = await self.reload_extension(extension)
            if success:
                success_count += 1
            else:
                fail_count += 1
        
        await ctx.send(f"✅ Reloaded {success_count} extensions. Failed: {fail_count}")

def configure_all_loggers():
    
    for name, logger_instance in logging.Logger.manager.loggerDict.items():
        if isinstance(logger_instance, logging.Logger):
       
            logger_instance.handlers = []  
            logger_instance.propagate = False  
            
            custom_handler = logging.StreamHandler()
            custom_handler.setFormatter(ColoredFormatter())
            logger_instance.addHandler(custom_handler)

configure_all_loggers()

async def setup(bot):
    await bot.add_cog(ExtensionLoader(bot))
