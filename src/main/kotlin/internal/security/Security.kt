package org.github.daymon.internal.security

import com.crazzyghost.alphavantage.AlphaVantage
import com.crazzyghost.alphavantage.Config
import com.crazzyghost.alphavantage.parameters.Interval
import com.crazzyghost.alphavantage.parameters.OutputSize
import dev.minn.jda.ktx.messages.Embed
import net.dv8tion.jda.api.entities.MessageEmbed
import org.github.daymon.handler.ConfigHandler


data class SecurityOverview(
    val ticker: String,
    val open: Double,
    val high: Double,
    val low: Double,
    val close: Double,
    val volume: Long,
    val adjustedClose: Double,
    val dividendAmount: Double,
    val splitCoefficient: Double
)
class Security(
    val ticker: String
) {

    init {
        val configHandler = ConfigHandler
        val cfg = Config.builder()
            .key(configHandler.config.alphaVantageApiKey)
            .timeOut(45)
            .build()
        AlphaVantage.api().init(cfg)
    }

    private val sadWojak = "https://upload.montague.im/u/UWE27F.png"
    private val happyWojak = "https://upload.montague.im/u/jYWurg.png"


    fun asEmbed(): MessageEmbed  {
        if (overview == null) {
            return Embed {
                title = "Security Overview"
                color = 0xFF0000
                thumbnail = sadWojak
                field {
                    name = "Ticker"
                    value = ticker
                    inline = true
                }
                field {
                    name = "Error"
                    value = "No data found for $ticker"
                    inline = true
                }
            }
        }
        return Embed {
            title = "Security Overview"
            color = if (overview!!.close > overview!!.open) 0x00FF00 else 0xFF0000
            thumbnail = if (overview!!.close > overview!!.open) happyWojak else sadWojak
            field {
                name = "Ticker"
                value = ticker
                inline = true
            }
            field {
                name = "Open"
                value = overview!!.open.toString()
                inline = true
            }
            field {
                name = "High"
                value = overview!!.high.toString()
                inline = true
            }
            field {
                name = "Low"
                value = overview!!.low.toString()
                inline = true
            }
            field {
                name = "Close"
                value = overview!!.close.toString()
                inline = true
            }
            field {
                name = "Volume"
                value = overview!!.volume.toString()
                inline = true
            }
            field {
                name = "Adjusted Close"
                value = overview!!.adjustedClose.toString()
                inline = true
            }
            field {
                name = "Dividend Amount"
                value = overview!!.dividendAmount.toString()
                inline = true
            }
            field {
                name = "Split Coefficient"
                value = overview!!.splitCoefficient.toString()
                inline = true
            }
        }
    }

    private val overview: SecurityOverview?
        get() {
            val response = AlphaVantage.api()
                .timeSeries()
                .intraday()
                .forSymbol(ticker)
                .interval(Interval.FIVE_MIN)
                .outputSize(OutputSize.FULL)
                .fetchSync();

            if (response.stockUnits.isEmpty()) return null

            return SecurityOverview(
                ticker = ticker,
                open = response.stockUnits[0].open,
                high = response.stockUnits[0].high,
                low = response.stockUnits[0].low,
                close = response.stockUnits[0].close,
                volume = response.stockUnits[0].volume,
                adjustedClose = response.stockUnits[0].adjustedClose,
                dividendAmount = response.stockUnits[0].dividendAmount,
                splitCoefficient = response.stockUnits[0].splitCoefficient
            )
        }




}