package org.github.daymon.commands.sub.money

import com.crazzyghost.alphavantage.AlphaVantage
import com.crazzyghost.alphavantage.Config
import com.crazzyghost.alphavantage.parameters.Interval
import com.crazzyghost.alphavantage.parameters.OutputSize
import dev.minn.jda.ktx.coroutines.await
import dev.minn.jda.ktx.messages.Embed
import net.dv8tion.jda.api.interactions.commands.OptionType
import org.github.daymon.handler.ConfigHandler
import org.github.daymon.internal.command.CommandEvent
import org.github.daymon.internal.command.CommandOptionData
import org.github.daymon.internal.command.SubCommand
import java.awt.Color


class SecurityPrice : SubCommand(
    name = "price",
    description = "Gives a price of a given security",
    options = listOf(
        CommandOptionData<String>(
            optionType = OptionType.STRING,
            name = "security_symbol",
            description = "Security you want to get a price of",
            isRequired = true
        )
    )
)
{
    override suspend fun onExecuteSuspend(event: CommandEvent)
    {
        val configHandler = ConfigHandler

        event.slashEvent.deferReply().queue()

        val cfg = Config.builder().key(
            configHandler.config.alphaVantageApiKey
        ).build()
        AlphaVantage.api().init(cfg)

        val symbol = event.getOption("security_symbol")?.asString ?: return event.replyMessage("You must provide a security symbol.")

        val response = AlphaVantage.api()
            .timeSeries()
            .intraday()
            .forSymbol(symbol)
            .interval(Interval.FIVE_MIN)
            .outputSize(OutputSize.FULL)
            .fetchSync();

        val madguy = "https://upload.montague.im/u/UWE27F.png"
        val coolguy = "https://upload.montague.im/u/jYWurg.png"


        val restActionResponse = event.hook.sendMessageEmbeds(
            Embed {
                title = "The price of $symbol is ${response.stockUnits[0].close}"
                color = if (response.stockUnits[0].close > response.stockUnits[1].close) Color.GREEN.rgb else Color.RED.rgb
                thumbnail = if (response.stockUnits[0].close > response.stockUnits[1].close.toDouble()) coolguy else madguy
                field {
                    name = "Open"
                    value = "${response.stockUnits[0].open}"
                    inline = true
                }

                field {
                    name = "High"
                    value = "${response.stockUnits[0].high}"
                    inline = true
                }

                field {
                    name = "Low"
                    value = "${response.stockUnits[0].low}"
                    inline = true
                }

                field {
                    name = "Volume"
                    value = "${response.stockUnits[0].volume}"
                    inline = true
                }

                field {
                    name = "Date"
                    value = "${response.stockUnits[0].date}"
                    inline = true
                }
            }
        ).await()


    }
}