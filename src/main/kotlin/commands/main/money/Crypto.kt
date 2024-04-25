package org.github.daymon.commands.main.money

import org.github.daymon.commands.sub.money.CryptoPrice
import org.github.daymon.internal.command.Command

class Crypto : Command(
    name = "Crypto",
    description = "Allows you to see the price or quote of a given cryptocurrency",
    children = listOf(
        CryptoPrice(),
    )
)