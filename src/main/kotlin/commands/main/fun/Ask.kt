package org.github.daymon.commands.main.`fun`

import dev.minn.jda.ktx.coroutines.await
import net.dv8tion.jda.api.events.interaction.command.CommandAutoCompleteInteractionEvent
import net.dv8tion.jda.api.interactions.commands.OptionType
import org.github.daymon.ext.replyChoiceAndLimit
import org.github.daymon.external.ChatInteractionResponse
import org.github.daymon.external.OpenRouter
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

        val response: ChatInteractionResponse = try { client.chat(
            model=event.getOption("model")?.asString ?: return event.replyMessage("You must provide a model."),
            prompt = event.getOption("prompt")?.asString ?: return event.replyMessage("You must provide a prompt.")
        ) } catch (e: Exception) {
            event.logger.error("An error occurred while trying to get a response.", e)
            return event.replyMessage("An error occurred while trying to get a response.")
        }


        val responseMessage = response.choices[0].message.content
        if ((responseMessage?.length ?: 0) > 2000) {
            return event.replyMessage("The response is too long to send.")
        }



        event.slashEvent.hook.sendMessage("${response.choices[0].message.content}").queue()
    }

    override suspend fun onAutoCompleteSuspend(event: CommandAutoCompleteInteractionEvent) {
        val client = OpenRouter
        val modelNames = client.list().data.
        filter {
            it.name != null && it.id != null
        }.map { net.dv8tion.jda.api.interactions.commands.Command.Choice(
            it.name!!,
            it.id!!

        ) }


        event.replyChoiceAndLimit(modelNames).await()
    }
}