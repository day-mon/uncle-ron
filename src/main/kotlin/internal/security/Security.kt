package org.github.daymon.internal.security

import dev.minn.jda.ktx.messages.Embed
import net.dv8tion.jda.api.entities.MessageEmbed
import org.github.daymon.ext.formatComma
import org.github.daymon.external.TwelveData
import java.time.Instant
import java.time.LocalDateTime
import java.time.ZoneId
import java.time.temporal.TemporalAccessor


class Security(
    val ticker: String
) {


    private val sadWojak = "https://upload.montague.im/u/UWE27F.png"
    private val happyWojak = "https://upload.montague.im/u/jYWurg.png"


    suspend fun asEmbed(): MessageEmbed? {
        val quote = try {
            TwelveData.quote(ticker)
        } catch (e: Exception) {
            return null
        }


        if (quote.symbol == null) {
            return null
        }


        val timestampInSeconds = quote.timestamp
        val instant = Instant.ofEpochSecond(timestampInSeconds!!.toLong())


        return Embed {
            title = "${quote.name} (${quote.symbol})"
            color = if (quote.change?.contains("-") == true) 0xFF0000 else 0x00FF00
            thumbnail = if (quote.change?.contains("-") == true) sadWojak else happyWojak
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
                name = "Previous Close"
                value = quote.previousClose?.toBigDecimal()?.formatComma() ?: "N/A"
                inline = true
            }

            field {
                name = "Fifty Two Week Range"
                value = quote.fiftyTwoWeek?.range ?: "N/A"
                inline = true
            }

            field {
                name = "Fifty Two Week Low"
                value = quote.fiftyTwoWeek?.low ?: "N/A"
                inline = true
            }
            field {
                name = "Fifty Two Week High"
                value = quote.fiftyTwoWeek?.high ?: "N/A"
                inline = true
            }
            field {
                name = "Exchange"
                value = quote.exchange ?: "N/A"
                inline = true
            }

            timestamp = instant

            footer {
                name = "Data provided by Twelve Data"

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