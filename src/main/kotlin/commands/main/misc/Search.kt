package org.github.daymon.commands.main.misc

import dev.jacobandersen.ddg4j.DuckDuckGo
import dev.minn.jda.ktx.messages.Embed
import net.dv8tion.jda.api.interactions.commands.OptionType
import org.github.daymon.Constants
import org.github.daymon.ext.toEmbed
import org.github.daymon.internal.command.Command
import org.github.daymon.internal.command.CommandEvent
import org.github.daymon.internal.command.CommandOptionData

class Search : Command(
    name = "search",
    description = "Searches for a given query on the internet",
    deferredReplyEnabled = true,
    options = listOf(
        CommandOptionData<String>(
            optionType = OptionType.STRING,
            name = "query",
            description = "The query you want to search for",
            isRequired = true
        )
    )
) {

    private val BANNED_WORDS = listOf(
        "porn",
        "p0rn",

    )

    private fun checkQuery(query: String) {

        if (query.length > 100) {
            throw IllegalArgumentException("Query is too long")
        }

        if (query.isBlank()) {
            throw IllegalArgumentException("Query is blank")
        }

        if (BANNED_WORDS.any { query.contains(it, ignoreCase = true) }) {
            throw IllegalArgumentException("Query contains banned words")
        }

    }
    override suspend fun onExecuteSuspend(event: CommandEvent) {

        val query =
            event.getOption("query")?.asString ?: return event.replyMessage("You must provide a query to search for.")

        try {
            checkQuery(query)
        } catch (e: IllegalArgumentException) {
            return event.replyEmbed(
                Embed {
                    title = "Invalid query"
                    description = e.message ?: "An error occurred while checking the query."
                    color = Constants.RED
                    footer {
                        this.name = "Requested by ${event.user.name}"
                    }
                    timestamp = event.createdAt
                }
            )
        }

        val searchResult = DuckDuckGo.search(query)


        if (searchResult?.results()?.isEmpty() == true) {
            return event.replyEmbed(
                Embed {
                    title = "No results found"
                    description = "No results were found for the given query."
                    color = Constants.RED
                    footer {
                        this.name = "Requested by ${event.user.name}"
                    }
                    timestamp = event.createdAt
                }
            )
        }

        val embeds = searchResult.results().take(5).map {
            it.toEmbed()
        }
        event.sendPaginator(*embeds.toTypedArray())
    }
}