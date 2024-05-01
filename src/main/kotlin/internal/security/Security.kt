package org.github.daymon.internal.security

import dev.minn.jda.ktx.messages.Embed
import net.dv8tion.jda.api.entities.MessageEmbed
import org.github.daymon.ext.formatComma
import org.github.daymon.external.TwelveData


class Security(
    val ticker: String
) {


    private val sadWojak = "https://upload.montague.im/u/UWE27F.png"
    private val happyWojak = "https://upload.montague.im/u/jYWurg.png"


    suspend fun asEmbed(): MessageEmbed {
        val quote = TwelveData.quote(ticker)


        if (quote.symbol == null) {
            return Embed {
                title = "Error"
                description = "Could not find a security with the symbol $ticker"
                color = 0xFF0000
                thumbnail = sadWojak
            }
        }

        return Embed {
            title = "${quote.symbol} (${quote.exchange})"
            color = if (quote.open!!.toDouble() < quote.close!!.toDouble()) 0x00FF00 else 0xFF0000
            thumbnail = if (quote.open!!.toDouble() < quote.close!!.toDouble()) happyWojak else sadWojak

            field {
                name = "Volume"
                value = quote.volume?.toBigDecimal()?.formatComma() ?: "N/A"
                inline = true
            }

            field {
                name = "Change"
                value = quote.change?.toBigDecimal()?.formatComma() ?: "N/A"
                inline = true
            }

            field {
                name = "Open"
                value = quote.open?.toBigDecimal()?.formatComma() ?: "N/A"
                inline = true
            }
            field {
                name = "High"
                value = quote.high?.toBigDecimal()?.formatComma() ?: "N/A"
                inline = true
            }
            field {
                name = "Low"
                value = quote.low?.toBigDecimal()?.formatComma() ?: "N/A"
                inline = true
            }
            field {
                name = "Previous Close"
                value = quote.previousClose?.toBigDecimal()?.formatComma() ?: "N/A"
                inline = true
            }
            field {
                name = "Volume"
                value = quote.volume?.toBigDecimal()?.formatComma() ?: "N/A"
                inline = true
            }
        }

    }

    suspend fun asEarningsCalenderPaginator(): List<MessageEmbed> {
        val earnings = TwelveData.earningsCalender(ticker)

        if (earnings.meta == null) {
            return listOf(Embed {
                title = "Error"
                description = "Could not find a security with the symbol $ticker"
                color = 0xFF0000
                thumbnail = sadWojak
            })
        }

        val pages = earnings.earnings.map {
            Embed {
                title = it.date
                color = if (it.epsActual!! > it.epsEstimate!!) 0x00FF00 else 0xFF0000
                thumbnail = if (it.epsActual!! > it.epsEstimate!!) happyWojak else sadWojak

                field {
                    name = "EPS Estimate"
                    value = it.epsEstimate.toString()
                    inline = true
                }
                field {
                    name = "Reported EPS"
                    value = it.epsActual.toString()
                    inline = true
                }
                field {
                    name = "Surprise Percent"
                    value = it.surprisePrc.toString()
                    inline = true
                }

            }
        }
        return pages

    }
}