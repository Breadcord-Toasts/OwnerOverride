import asyncio
import contextlib

import discord
from discord.ext import commands

import breadcord


class OwnerOverride(breadcord.module.ModuleCog):
    LOCKED = "\N{LOCK}"
    UNLOCKED = "\N{OPEN LOCK}"

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, exception: Exception) -> None:
        if not isinstance(exception, commands.NotOwner):
            raise exception

        await ctx.message.add_reaction(self.LOCKED)

        modified_ctx = ctx
        await self.bot.is_owner(ctx.author)  # Make sure `bot.owner_ids` is populated and up-to-date

        def check(reaction: discord.Reaction, user: discord.User) -> bool:
            if (
                reaction.message.id == ctx.message.id
                and reaction.emoji == self.LOCKED
                and user.id in (self.bot.owner_id, *self.bot.owner_ids)
            ):
                nonlocal modified_ctx
                # noinspection PyPropertyAccess
                modified_ctx.author = user
                return True
            return False

        try:
            await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
        except asyncio.TimeoutError:
            return
        finally:
            await ctx.message.remove_reaction(self.LOCKED, ctx.me)

        await ctx.message.add_reaction(self.UNLOCKED)
        with contextlib.suppress(discord.Forbidden):
            await ctx.message.remove_reaction(self.LOCKED, modified_ctx.author)
        await self.bot.invoke(modified_ctx)


async def setup(bot: breadcord.Bot):
    await bot.add_cog(OwnerOverride("owner_override"))
