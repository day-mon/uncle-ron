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
            name = "prompt",
            description = "The prompt you want to ask the LLM",
            isRequired = true
        ),

    )
) {

    private val model = "anthropic/claude-3.5-sonnet"

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
                            |Do not make anything up. 
                            |Make sure all the numbers you see will be in thousands so keep that in mind when you are looking at the financials.
                            |If the user uses any words like "it" or "they", they are referring to the security in question.
                            |
                            |When giving your response make sure you keep this formatting guide available for markdown:
                            |
                            |Element 	Support 	Notes
                            Headings 	Yes 	
                            Paragraphs 	No 	
                            Line Breaks 	No 	The Markdown syntax is not supported, but you can press the Shift and Return keys to go to the next line.
                            Bold 	Yes 	Use asterisks. Underscores aren’t supported.
                            Italic 	Yes 	
                            Blockquotes 	Yes 	You can use >>> to create a multi-line blockquote. All text from the >>> to the end of the message will be included in the quote.
                            Ordered Lists 	Yes 	
                            Unordered Lists 	Yes 	
                            Code 	Yes 	
                            Horizontal Rules 	No 	
                            Links 	Partial 	Not fully supported. See this GitHub issue for more information.
                            Images 	No 	
                            Tables 	No 	
                            Fenced Code Blocks 	Yes 	
                            Syntax Highlighting 	Yes 	
                            Footnotes 	No 	
                            Heading IDs 	No 	
                            Definition Lists 	No 	
                            Strikethrough 	Yes 	
                            Task Lists 	No 	
                            Emoji (copy and paste) 	Yes 	
                            Emoji (shortcodes) 	Yes 	
                            Highlight 	No 	
                            Subscript 	No 	
                            Superscript 	No 	
                            Automatic URL Linking 	Yes 	
                            Disabling Automatic URL Linking 	Yes 	
                            HTML 	No 	
                            |
                            |ALWAYS use markdown and make sure you give excerpts from the financials to back up your response, but make sure you keep the excerpts short and sweet
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

        val responseMessage = response.choices[0].message.content ?: return event.replyErrorEmbed(
            embedTitle = "An error occurred while trying to get a response.",
            error = "An error occurred while trying to get a response. Error: Response was null."
        )

        event.replyMessageWithOverflow(responseMessage)



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