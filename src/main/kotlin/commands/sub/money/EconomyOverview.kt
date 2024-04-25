package org.github.daymon.commands.sub.money

import org.github.daymon.internal.command.CommandEvent
import org.github.daymon.internal.command.SubCommand

class EconomyOverview : SubCommand(
    name = "overview",
    description = "Allows you to see the overview of the economy.",
    options = listOf(),
) {
    override suspend fun onExecuteSuspend(event: CommandEvent) {
       throw NotImplementedError("Not implemented")
    }

}