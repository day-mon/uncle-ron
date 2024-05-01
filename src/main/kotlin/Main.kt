package org.github.daymon

import dev.minn.jda.ktx.events.CoroutineEventManager
import dev.minn.jda.ktx.jdabuilder.light
import net.dv8tion.jda.api.entities.Activity
import net.dv8tion.jda.api.requests.GatewayIntent
import org.github.daymon.handler.CommandHandler
import org.github.daymon.handler.ConfigHandler
import org.github.daymon.handler.TwitterLinkConverter


fun main() {
    val commandHandler = CommandHandler
    val cfgHandler = ConfigHandler
    val twitterConverter = TwitterLinkConverter

    light(cfgHandler.config.token, intents = listOf(GatewayIntent.MESSAGE_CONTENT, GatewayIntent.GUILD_MESSAGES), enableCoroutines = true) {
        enableCache(emptySet())
        setEventManager(CoroutineEventManager())
        addEventListeners(commandHandler, twitterConverter)
        setActivity(Activity.customStatus("In Kotlin with \u2764\uFE0F"))
    }
}