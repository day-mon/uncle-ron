package org.github.daymon.handler

import dev.minn.jda.ktx.events.CoroutineEventListener
import io.ktor.http.*
import net.dv8tion.jda.api.events.GenericEvent
import net.dv8tion.jda.api.events.message.MessageReceivedEvent


object TwitterLinkConverter : CoroutineEventListener {
    override suspend fun onEvent(event: GenericEvent) {
        when (event) {
            is MessageReceivedEvent -> handleGuildMessage(event)
        }
    }

    suspend fun handleGuildMessage(event: MessageReceivedEvent) {
        val message = event.message.contentRaw
        val url = try { Url(message) }
        catch (e: Exception) { return }

        if (url.host != "x.com") {
            return
        }


        val path = url.toString().substringBefore("?")

        val fixedUrl = path.replace(url.host, "fixupx.com")
        event.channel.sendMessage("Fixed URL: $fixedUrl").queue()
    }


}
