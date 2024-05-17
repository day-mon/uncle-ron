package org.github.daymon.ext

import dev.jacobandersen.ddg4j.api.ResultItem
import dev.minn.jda.ktx.messages.Embed
import net.dv8tion.jda.api.entities.Message
import net.dv8tion.jda.api.entities.MessageEmbed
import net.dv8tion.jda.api.events.interaction.command.CommandAutoCompleteInteractionEvent
import net.dv8tion.jda.api.interactions.InteractionHook
import net.dv8tion.jda.api.interactions.callbacks.IReplyCallback
import net.dv8tion.jda.api.interactions.commands.Command
import net.dv8tion.jda.api.interactions.components.buttons.Button
import net.dv8tion.jda.api.requests.restaction.WebhookMessageCreateAction
import org.github.daymon.Constants
import org.github.daymon.internal.misc.Emoji
import java.math.BigDecimal
import java.time.Instant
import java.util.*


private val logger = org.slf4j.LoggerFactory.getLogger("Rand")
val String.Companion.empty: String
    get() { return "" }

inline fun <reified T: Enum<T>> emptyEnumSet(): EnumSet<T> = EnumSet.noneOf(T::class.java)
inline fun <reified T: Enum<T>> enumSetOf(vararg elements: T): EnumSet<T> = EnumSet.copyOf(elements.toList())
inline fun <reified T: Enum<T>> enumSetOf(collection: Collection<T>): EnumSet<T> = EnumSet.copyOf(collection)

private fun errorEmbed(
    errorString: String
) =  Embed {
    this.title = "${Emoji.STOP_SIGN.getAsChat()} $title"
    this.description = errorString
    this.color = Constants.RED
}

fun <T: IReplyCallback> T.replyErrorEmbed(errorString: String, title: String = "Error has occurred", color: Int = Constants.YELLOW): WebhookMessageCreateAction<Message> {
    val embed = Embed {
        this.title = "${Emoji.STOP_SIGN.getAsChat()} $title"
        this.description = errorString
        this.color = color
    }

    if (this.isAcknowledged.not())
        this.deferReply().queue()

    return this.hook.sendMessageEmbeds(embed)
}


fun InteractionHook.replyErrorEmbed(mainTitle: String = "Error has occurred", body: String, actionRows: List<Button> = emptyList(), content: String = String.empty) = this.editOriginalEmbeds(
    Embed {
        title = mainTitle
        description = body
        color = Constants.RED
    }
).setActionRow(actionRows)
    .setContent(content)
    .queue()


fun BigDecimal.formatComma(): String {
    val formatter = java.text.DecimalFormat("#,###.00")
    return formatter.format(this)
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

fun ResultItem.toEmbed(): MessageEmbed {
    val disambiguationName = this.disambiguationName().ifEmpty { "No title" }
    val url = this.url()
    val description = this.instantInformation()

    return Embed {
        this.title = disambiguationName
        this.url = url
        field {
            name = "Snippet"
            value = description
            inline = false
        }

    }
}

fun Instant.toDiscordTimeZone() = "<t:${this.epochSecond}>"
fun Instant.toDiscordTimeZoneRelative() = "<t:${this.epochSecond}:R>"
fun Instant.toDiscordTimeZoneLDST() = "<t:${this.epochSecond}:F>"
fun BigDecimal.toHumanTime(): String {
    // takes time that is in ms and converts it to days, hours, minutes, seconds
    val days = this.toLong() / 86400000
    val hours = this.toLong() % 86400000 / 3600000
    val minutes = this.toLong() % 86400000 % 3600000 / 60000
    val seconds = this.toLong() % 86400000 % 3600000 % 60000 / 1000
    val milliseconds = this.toLong() % 86400000 % 3600000 % 60000 % 1000

    val builder = StringBuilder()
    if (days > 0) builder.append("$days days, ")
    if (hours > 0) builder.append("$hours hours, ")
    if (minutes > 0) builder.append("$minutes minutes, ")
    if (seconds > 0) builder.append("$seconds seconds, ")
    if (milliseconds > 0) builder.append("$milliseconds milliseconds")
    return builder.toString()


}

fun <T: IReplyCallback> T.replyEmbed(embed: MessageEmbed, content: String = String.empty) = when {
    this.isAcknowledged -> this.hook.sendMessageEmbeds(embed).setContent(content).queue(null) {
        logger.error(
            "Error has occurred while attempting to send embeds",
        )
        hook.editOriginal("Error has occurred while attempting to send embeds").queue()
    }
    else -> this.replyEmbeds(embed).setContent(content).queue(null) {
        logger.error(
            "Error has occurred while attempting to send embeds", it
        )
        this.reply("Error has occurred while attempting to send embeds").queue()

    }
}

