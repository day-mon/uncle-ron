package org.github.daymon.commands.main.`fun`

import dev.minn.jda.ktx.coroutines.await
import net.dv8tion.jda.api.events.interaction.command.CommandAutoCompleteInteractionEvent
import net.dv8tion.jda.api.interactions.commands.OptionType
import org.github.daymon.commands.sub.money.SecurityAskFinancials
import org.github.daymon.ext.replyChoiceAndLimit
import org.github.daymon.external.*
import org.github.daymon.internal.command.Command
import org.github.daymon.internal.command.CommandEvent
import org.github.daymon.internal.command.CommandOptionData


class Ask : Command(
    name = "ask",
    description = "Uses an LLM to answer your question.",
    deferredReplyEnabled = true,
    options = listOf(
        CommandOptionData<String>(
            optionType = OptionType.STRING,
            name = "model",
            description = "The model you want to use",
            isRequired = true,
            autoCompleteEnabled = true
        ),
        CommandOptionData<String>(
            optionType = OptionType.STRING,
            name = "prompt",
            description = "The prompt you want to ask the LLM",
            isRequired = true
        )
    )
) {


    override suspend fun onExecuteSuspend(event: CommandEvent) {
        val client = OpenRouter

        val prompt = event.getOption(
            "prompt"
        )?.asString ?: return event.replyMessage("You must provide a prompt.")

        val model = event.getOption(
            "model"
        )?.asString ?: return event.replyMessage("You must provide a model.")


        val response: ChatInteractionResponse = try {
            client.chat(
                model = model,
                messages = listOf(
                    ChatInteraction(
                        role = ChatInteractionRole.SYSTEM,
                        message = "You are a friendly AI that is here to help to answer questions. Just a reminder you are responding in the context of a discord. So format your messages accordingly.",
                    ),
                    ChatInteraction(
                        role = ChatInteractionRole.USER,
                        message = prompt
                    )
                )
            )
        } catch (e: Exception) {
            event.logger.error("An error occurred while trying to get a response.", e)
            return event.replyMessage("An error occurred while trying to get a response. Error: ${e.message}")
        }

        val responseMessage = response.choices[0].message.content ?: return event.replyErrorEmbed(
            embedTitle = "An error occurred while trying to get a response.",
            error = "An error occurred while trying to get a response. Error: Response was null."
        )

        event.replyMessageWithOverflow(responseMessage)
    }

    override suspend fun onAutoCompleteSuspend(event: CommandAutoCompleteInteractionEvent) {
        val client = OpenRouter
        val modelNames = client.list().data.filter {
            it.name != null && it.id != null
        }.map {
            net.dv8tion.jda.api.interactions.commands.Command.Choice(
                it.name!!,
                it.id!!

            )
        }
        println(

        )


        event.replyChoiceAndLimit(modelNames).await()
    }
}