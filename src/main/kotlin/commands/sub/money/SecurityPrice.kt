package org.github.daymon.commands.sub.money

import com.crazzyghost.alphavantage.AlphaVantage
import com.crazzyghost.alphavantage.Config
import com.crazzyghost.alphavantage.parameters.Interval
import com.crazzyghost.alphavantage.parameters.OutputSize
import dev.minn.jda.ktx.coroutines.await
import dev.minn.jda.ktx.messages.Embed
import net.dv8tion.jda.api.interactions.commands.OptionType
import org.github.daymon.handler.ConfigHandler
import org.github.daymon.internal.command.CommandEvent
import org.github.daymon.internal.command.CommandOptionData
import org.github.daymon.internal.command.SubCommand
import org.github.daymon.internal.security.Security
import java.awt.Color


class SecurityPrice : SubCommand(
    name = "price",
    description = "Gives a price of a given security",
    deferredReplyEnabled = true,

    options = listOf(
        CommandOptionData<String>(
            optionType = OptionType.STRING,
            name = "security_symbol",
            description = "Security you want to get a price of",
            isRequired = true
        )
    )
)
{
    override suspend fun onExecuteSuspend(event: CommandEvent)
    {
        val security = Security(
            event.getOption("security_symbol")?.asString ?: return event.replyMessage("You must provide a security symbol.")
        )
        event.replyEmbed(
            security.asEmbed()
        )

    }


}