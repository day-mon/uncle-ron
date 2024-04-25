package org.github.daymon.commands.main.misc

import org.github.daymon.commands.sub.misc.LeetifyStats
import org.github.daymon.internal.command.Command

class Leetify: Command(
    name = "leetify",
    description = "Leetify stats",
    children = listOf(
        LeetifyStats(),
    )
)