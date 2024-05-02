package org.github.daymon.handler

import dev.minn.jda.ktx.events.CoroutineEventListener
import dev.minn.jda.ktx.messages.invoke
import io.ktor.http.*
import net.dv8tion.jda.api.events.GenericEvent
import net.dv8tion.jda.api.events.message.MessageReceivedEvent
import net.dv8tion.jda.api.interactions.components.buttons.Button
import net.dv8tion.jda.api.utils.messages.MessageCreateBuilder


object TwitterLinkConverter : CoroutineEventListener {
    override suspend fun onEvent(event: GenericEvent) {
        when (event) {
            is MessageReceivedEvent -> handleGuildMessage(event)
        }
    }

    private fun handleGuildMessage(event: MessageReceivedEvent) {
        if (event.author.isBot) return
        val message = event.message.contentRaw



        val url = try { Url(message) }
        catch (e: Exception) { return }

        if (url.host != "x.com") {
            return
        }


        val path = url.toString().substringBefore("?")

        val fixedUpXURL = path.replace(url.host, "vxtwitter.com")
        val nitterUrl = path.replace(url.host, "nitter.net")
        val builder = MessageCreateBuilder().also { messageCreateBuilder ->
            messageCreateBuilder.setContent("$fixedUpXURL\n*Originally Posted by ${event.author.asMention}*")
            messageCreateBuilder.addActionRow(
                Button.link(fixedUpXURL, "See on Twitter"),
                Button.link(nitterUrl, "See on Nitter")
            )
        }.build()

        event.message.delete().queue()
        event.channel.sendMessage(builder).queue()
    }
}
