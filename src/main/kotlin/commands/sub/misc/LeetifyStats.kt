package org.github.daymon.commands.sub.misc

import dev.minn.jda.ktx.messages.Embed
import net.dv8tion.jda.api.interactions.commands.OptionType
import org.github.daymon.external.LeetifyClient
import org.github.daymon.internal.command.CommandEvent
import org.github.daymon.internal.command.CommandOptionData
import org.github.daymon.internal.command.SubCommand

class LeetifyStats: SubCommand(
    name = "stats",
    description = "Leetify stats",
    options = listOf(
        CommandOptionData<String>(
            name = "steam_id",
            description = "Steam ID of the user you want to get stats for",
            isRequired = true,
            optionType = OptionType.STRING
        )
    )
) {
    override suspend fun onExecuteSuspend(event: CommandEvent) {

        val client = LeetifyClient
        val stats = client.getPlayerStats(
            event.getOption("steam_id")?.asString
                ?: return event.replyMessage("You must provide a steam id.")
        ) ?: return event.replyMessage("Could not find stats for this user.")



        val embed = Embed {
            title = "${stats.meta?.name}'s stats"
            description = "Here are some stats for ${stats.meta?.name}"
            thumbnail = stats.meta?.steamAvatarUrl ?: ""
            field {
                name = "Aim"
                value = stats.recentGameRatings?.aim.toString()
                inline = true
            }
            field {
                name = "Positioning"
                value = stats.recentGameRatings?.positioning.toString()
                inline = true
            }
            field {
                name = "Utility"
                value = stats.recentGameRatings?.utility.toString()
                inline = true
            }
            field {
                name = "Games Played"
                value = stats.recentGameRatings?.gamesPlayed.toString()
                inline = true
            }
            field {
                name = "Clutch"
                value = stats.recentGameRatings?.clutch.toString()
                inline = true
            }
            field {
                name = "Leetify Rating"
                value = stats.recentGameRatings?.leetify.toString()
                inline = true
            }
            field {
                name = "Opening"
                value = stats.recentGameRatings?.opening.toString()
                inline = true
            }
            field {
                name = "T Leetify"
                value = stats.recentGameRatings?.tLeetify.toString()
                inline = true
            }
        }
        event.replyEmbed(
            embed
        )

    }
}