package org.github.daymon.commands.sub.money

import net.dv8tion.jda.api.interactions.commands.OptionType
import org.github.daymon.internal.command.CommandEvent
import org.github.daymon.internal.command.CommandOptionData
import org.github.daymon.internal.command.SubCommand
import org.github.daymon.internal.security.Security

class CryptoPrice: SubCommand(
    name = "price",
    description = "Gives a price of a given cryptocurrency",
    deferredReplyEnabled = true,
    options = listOf(
        CommandOptionData<String>(
            optionType = OptionType.STRING,
            name = "crypto_symbol",
            description = "Security you want to get a price of",
            isRequired = true
        )
    )
) {
    override suspend fun onExecuteSuspend(event: CommandEvent) {
//        val security = Security(
//            event.getOption("crypto_symbol")?.asString ?: return event.replyMessage("You must provide a security symbol.")
//        )
//        event.replyEmbed(
//            security.asCryptoEmbed()
//        )
//    }
    }
}