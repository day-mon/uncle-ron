package org.github.daymon.commands.sub.money

import com.crazzyghost.alphavantage.AlphaVantage
import com.crazzyghost.alphavantage.Config
import dev.minn.jda.ktx.messages.Embed
import org.github.daymon.handler.ConfigHandler
import org.github.daymon.internal.command.CommandEvent
import org.github.daymon.internal.command.SubCommand

class EconomyOverview : SubCommand(
    name = "overview",
    description = "Allows you to see the overview of the economy.",
    options = listOf(),
) {
    override suspend fun onExecuteSuspend(event: CommandEvent) {
        val cfg = ConfigHandler


        val alphaVantageConfig = Config.builder().key(
            cfg.config.alphaVantageApiKey
        ).build()

        AlphaVantage.api().init(alphaVantageConfig)

        val economicIndicators = AlphaVantage.api()
            .economicIndicator()

        val cpi = economicIndicators
            .cpi()
            .fetchSync()

        val gdp = economicIndicators
            .realGdp()
            .fetchSync()

        val gdpPerCap = economicIndicators
            .realGdpPerCapita()
            .fetchSync()


        println(
            """
            CPI: ${cpi.data}
            GDP: ${gdp.data}
            GDP Per Capita: ${gdpPerCap.data}
            """
        )

        event.replyEmbed(
            Embed {
                title = "Economic Overview"
                field {
                    name = cpi.name
                    value = cpi.data.toString()
                    inline = true
                }
                field {
                    name = gdpPerCap.name
                    value = gdpPerCap.data.toString()
                    inline = true
                }
                field {
                    name = gdp.name
                    value = gdp.data.toString()
                    inline = true
                }

            }
        )
    }

}