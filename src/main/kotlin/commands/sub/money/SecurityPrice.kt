package org.github.daymon.commands.sub.money

import net.dv8tion.jda.api.interactions.commands.OptionType
import org.github.daymon.internal.command.CommandEvent
import org.github.daymon.internal.command.CommandOptionData
import org.github.daymon.internal.command.SubCommand
import org.github.daymon.internal.security.Security
import net.dv8tion.jda.api.interactions.components.buttons.Button
import net.dv8tion.jda.api.utils.messages.MessageCreateBuilder


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

        val symbol = event.getOption("security_symbol")?.asString?.uppercase() ?: return event.replyMessage("You must provide a security symbol.")

        val security = Security(
            symbol
        )


        val embed = security.asEmbed() ?: return event.replyMessage("Could not find a security with the symbol $symbol")


        val message = MessageCreateBuilder().also {
            it.addActionRow(
                Button.link("https://finance.yahoo.com/quote/$symbol/press-releases/", "View $symbol Press Releases"),
                Button.link("https://finance.yahoo.com/quote/$symbol/profile", "View $symbol Profile"),
                Button.link("https://finance.yahoo.com/quote/$symbol/analysis", "View $symbol Analysis"),
                )
            it.addActionRow(
                Button.link("https://finance.yahoo.com/quote/$symbol/holders", "View $symbol Holders"),
                Button.link("https://finance.yahoo.com/quote/$symbol/financials", "View $symbol Financials"),
                )
            it.addEmbeds(
                embed
            )
        }.build()

        event.hook.sendMessage(message).queue()


    }


}