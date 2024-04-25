package org.github.daymon

import dev.minn.jda.ktx.events.CoroutineEventManager
import dev.minn.jda.ktx.jdabuilder.light
import io.github.freya022.botcommands.api.core.BotCommands
import io.github.freya022.botcommands.api.core.JDAService.Companion.defaultIntents
import io.github.freya022.botcommands.api.core.utils.namedDefaultScope
import kotlinx.coroutines.cancel
import net.dv8tion.jda.api.entities.Activity
import net.dv8tion.jda.api.events.session.ShutdownEvent
import org.github.daymon.handler.CommandHandler
import org.github.daymon.handler.ConfigHandler
import kotlin.time.Duration.Companion.minutes



fun main() {
    val commandHandler = CommandHandler
    val cfgHandler = ConfigHandler

    light(cfgHandler.config.token, intents = defaultIntents, enableCoroutines = true) {
        enableCache(emptySet())
        setEventManager(CoroutineEventManager())
        addEventListeners(commandHandler)
        setActivity(Activity.customStatus("In Kotlin with \u2764\uFE0F"))
    }
}