package org.github.daymon.commands.main.money

import org.github.daymon.commands.sub.money.SecurityPrice
import org.github.daymon.internal.command.Command




class Security : Command(
    name = "Security",
    description = "Allows you to see the price or quote of a given security",
    children = listOf(
        SecurityPrice(),
    )
)