package org.github.daymon.commands.sub.money

import dev.minn.jda.ktx.coroutines.await
import net.dv8tion.jda.api.events.interaction.command.CommandAutoCompleteInteractionEvent
import net.dv8tion.jda.api.interactions.commands.OptionType
import org.github.daymon.commands.main.money.Security
import org.github.daymon.ext.replyChoiceAndLimit
import org.github.daymon.ext.replyChoiceStringAndLimit
import org.github.daymon.external.*
import org.github.daymon.internal.command.CommandEvent
import org.github.daymon.internal.command.CommandOptionData
import org.github.daymon.internal.command.SubCommand

class SecurityAskFinancials: SubCommand(
    name = "financials",
    description = "Uses an LLM to answer your question about a security's financials.",
    deferredReplyEnabled = true,
    options = listOf(
        CommandOptionData<String>(
            optionType = OptionType.STRING,
            name = "security_symbol",
            description = "The security you want to get financials for",
            isRequired = true,
            autoCompleteEnabled = true
        ),
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
        ),

    )
) {

    private suspend fun buildPrompt(security: String, prompt: String): String {
        val yhFinance = YahooFinance
        val data = yhFinance.getFullFinancialsRaw(security)

        return """
            |The financials for $security are as follows:
            
            |Cash Flow
            |${data.cashFlow}
            
            |Income Statement
            |${data.incomeStatement}
            
            |Balance Sheet
            |${data.balanceSheet}
            
            
            User Prompt:
            $prompt
        """.trimIndent()
    }

    override suspend fun onExecuteSuspend(event: CommandEvent) {
        val security = event.getOption<String>("security_symbol")
        val model = event.getOption<String>("model")
        val prompt = event.getOption<String>("prompt")

        val promptString = buildPrompt(security, prompt)

        val client = OpenRouter
        val response = try {
            client.chat(
                model = model,
                messages = listOf(
                    ChatInteraction(
                        role = ChatInteractionRole.SYSTEM,
                        message = """You are a friendly AI that is here to help to answer questions about a security's financials. 
                            |Just a reminder you are responding in the context of a discord. So format your messages accordingly. 
                            |Do not make anything up. 
                            |Make sure all the numbers you see will be in thousands so keep that in mind when you are looking at the financials.
                            |If the user uses any words like "it" or "they", they are referring to the security in question.
                            |Always give exact citations of where you got your information and use footnotes to cite your sources. When using footnotes only use the number of the footnote and the source.
                            |""".trimMargin()
                    ),
                    ChatInteraction(
                        role = ChatInteractionRole.USER,
                        message = promptString

                    )
                )
            )
        } catch (e: Exception) {
            event.logger.error("An error occurred while trying to get a response.", e)
            return event.replyErrorEmbed(
                embedTitle = "An error occurred while trying to get a response.",
                error = "An error occurred while trying to get a response. Error: ${e.message}"
            )
        }

        val responseMessage = response.choices[0].message.content
        if ((responseMessage?.length ?: 0) > 2000) {
            val pastecordClient = Pastecord
            val uploadKey = try {
                pastecordClient.upload(responseMessage!!)
            } catch (e: Exception) {
                event.logger.error("An error occurred while trying to upload the response to pastecord.", e)
                return event.replyMessage("An error occurred while trying to upload the response to pastecord.")
            }

            return event.replyMessage("The response was too long, so it has been uploaded to pastecord: https://pastecord.com/$uploadKey")
        }



        event.slashEvent.hook.sendMessage("${response.choices[0].message.content}")
            .queue()


    }

    override suspend fun onAutoCompleteSuspend(event: CommandAutoCompleteInteractionEvent) {

        if (event.focusedOption.name == "security_symbol") {
            val twelveData = TwelveData
            val tickers = twelveData.getTickers()

            event.replyChoiceStringAndLimit(tickers).queue()
        } else if (event.focusedOption.name == "model") {
            val client = OpenRouter
            val modelNames = client.list().data.filter {
                it.name != null && it.id != null
            }.map {
                net.dv8tion.jda.api.interactions.commands.Command.Choice(
                    it.name!!,
                    it.id!!

                )
            }
            event.replyChoiceAndLimit(modelNames).await()
        }
    }

}