package org.github.daymon.ext

import net.dv8tion.jda.api.entities.MessageEmbed
import net.dv8tion.jda.api.events.interaction.command.CommandAutoCompleteInteractionEvent
import net.dv8tion.jda.api.interactions.callbacks.IReplyCallback
import net.dv8tion.jda.api.interactions.commands.Command
import java.util.*


private val logger = org.slf4j.LoggerFactory.getLogger("Rand")
val String.Companion.empty: String
    get() { return "" }

inline fun <reified T: Enum<T>> emptyEnumSet(): EnumSet<T> = EnumSet.noneOf(T::class.java)
inline fun <reified T: Enum<T>> enumSetOf(vararg elements: T): EnumSet<T> = EnumSet.copyOf(elements.toList())
inline fun <reified T: Enum<T>> enumSetOf(collection: Collection<T>): EnumSet<T> = EnumSet.copyOf(collection)
fun <T: IReplyCallback> T.replyEmbed(embed: MessageEmbed, content: String = String.empty) = when {
    this.isAcknowledged -> this.hook.sendMessageEmbeds(embed).setContent(content).queue(null) {
        logger.error(
            "Error has occurred while attempting to send embeds",
        )
    }
    else -> this.replyEmbeds(embed).setContent(content).queue(null) {
        logger.error(
            "Error has occurred while attempting to send embeds", it
        )

    }
}

private const val interactionLimit: Int = 25
fun CommandAutoCompleteInteractionEvent.replyChoiceAndLimit(commands: Collection<Command.Choice>) = this.replyChoices(
    commands
        .filter { it.name.startsWith(this.focusedOption.value, ignoreCase = true) }.take(interactionLimit)
)
fun CommandAutoCompleteInteractionEvent.replyChoiceStringAndLimit(commands: Collection<String>) = this.replyChoiceStrings(
    commands
        .filter { it.startsWith(this.focusedOption.value, ignoreCase = true) }
        .take(interactionLimit)
)
fun CommandAutoCompleteInteractionEvent.replyChoiceStringAndLimit(vararg choices: String) = this.replyChoiceStrings(
    choices
        .filter { it.startsWith(this.focusedOption.value, ignoreCase = true) }
        .take(interactionLimit)
)