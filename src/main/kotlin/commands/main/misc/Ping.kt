package org.github.daymon.commands.main.misc

import dev.minn.jda.ktx.messages.reply_
import net.dv8tion.jda.api.EmbedBuilder
import org.github.daymon.internal.command.Command
import org.github.daymon.internal.command.CommandEvent

class Ping : Command(
    name = "ping",
    description = "Responds with pong."
) {
    override suspend fun onExecuteSuspend(event: CommandEvent)
    {
        val jda = event.jda

        jda.restPing
            .queue {
                event.replyEmbed(
                    EmbedBuilder()
                        .addField("Gateway Ping", "${jda.gatewayPing} ms", false)
                        .addField("Rest Ping", "$it ms", false)
                        .build()
                )
            }
    }
}
