package org.github.daymon.commands.sub.money

import net.dv8tion.jda.api.interactions.commands.OptionType
import org.github.daymon.internal.command.CommandEvent
import org.github.daymon.internal.command.CommandOptionData
import org.github.daymon.internal.command.SubCommand
import org.github.daymon.internal.security.Security

class SecurityEarningsCalender : SubCommand(
    name = "earnings",
    description = "Gives a earnings calender of a given security",
    deferredReplyEnabled = true,

    options = listOf(
        CommandOptionData<String>(
            optionType = OptionType.STRING,
            name = "security_symbol",
            description = "Security you want to get a price of",
            isRequired = true
        )
    )
) {
    override suspend fun onExecuteSuspend(event: CommandEvent) {
        val security = Security(
            event.getOption("security_symbol")?.asString
                ?: return event.replyMessage("You must provide a security symbol.")
        )
        val earningsCalender = security.asEarningsCalenderPaginator()
        event.replyMessage("s")
    }
}