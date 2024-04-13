package org.github.daymon.commands.main.money

import org.github.daymon.commands.sub.money.EconomyOverview
import org.github.daymon.internal.command.Command

class Economy: Command(
    name = "Economy",
    description = "Allows you to see that state of the economy.",
    children = listOf(
        EconomyOverview()
    )
) {
}