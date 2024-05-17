package org.github.daymon.external

import com.google.gson.annotations.SerializedName
import dev.minn.jda.ktx.util.SLF4J
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.engine.cio.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import org.github.daymon.handler.ConfigHandler
import java.sql.Struct

object TwelveData {
    private val ktorClient: HttpClient = HttpClient(CIO) {
        install(ContentNegotiation) {
            json(Json {
                prettyPrint = true
                isLenient = true
                ignoreUnknownKeys = true
            })
        }
    }
    private val configHandler: ConfigHandler = ConfigHandler
    private val logger by SLF4J
    private val cache: MutableMap<String, Any> = mutableMapOf()

    suspend fun earningsCalender(
        symbol: String
    ): TwelveDataEarningsCalenderResponse {
        val response =  ktorClient.get("https://api.twelvedata.com/earnings?symbol=$symbol&apikey=${configHandler.config.twelveDataApiKey}")
        if (response.status != HttpStatusCode.OK) {
            logger.error("Failed to get earnings calender for $symbol - ${response.status} - ${response.bodyAsText()}")
            throw Exception("Failed to get earnings calender for $symbol")
        }

        return response.body<TwelveDataEarningsCalenderResponse>()
    }

    suspend fun getTickers(): List<String> {
        if (cache.containsKey("tickers")) {
            return cache["tickers"] as List<String>
        }
        val tickersUrl = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/all/all_tickers.txt"


        val response = ktorClient.get(tickersUrl)
        if (response.status != HttpStatusCode.OK) {
            logger.error("Failed to get tickers - ${response.status} - ${response.bodyAsText()}")
            throw Exception("Failed to get tickers")
        }

        val tickers = response.body<String>().split("\n")
        cache["tickers"] = tickers
        return tickers

    }



    suspend fun quote(
        symbol: String
    ): TwelveDataQuoteResponse {
        val response =  ktorClient.get("https://api.twelvedata.com/quote?symbol=$symbol&apikey=${configHandler.config.twelveDataApiKey}")
        if (response.status != HttpStatusCode.OK) {
            logger.error("Failed to get quote for $symbol - ${response.status} - ${response.bodyAsText()}")
            throw Exception("Failed to get quote for $symbol")
        }

        logger.info("Quote response: ${response.bodyAsText()}")

        val body =  response.body<TwelveDataQuoteResponse>()
        return body
    }
}

@Serializable
data class FiftyTwoWeek (
    @SerializedName("low"                 ) var low               : Double? = null,
    @SerializedName("high"                ) var high              : Double? = null,
    @SerializedName("low_change"          ) var lowChange         : Double? = null,
    @SerializedName("high_change"         ) var highChange        : Double? = null,
    @SerializedName("low_change_percent"  ) var lowChangePercent  : Double? = null,
    @SerializedName("high_change_percent" ) var highChangePercent : Double? = null,
    @SerializedName("range"               ) var range             : String? = null
)
@Serializable
data class TwelveDataQuoteResponse (

    @SerializedName("symbol"                  ) var symbol                : String?       = null,
    @SerializedName("name"                    ) var name                  : String?       = null,
    @SerializedName("exchange"                ) var exchange              : String?       = null,
    @SerializedName("mic_code"                ) var micCode               : String?       = null,
    @SerializedName("currency"                ) var currency              : String?       = null,
    @SerializedName("datetime"                ) var datetime              : String?       = null,
    @SerializedName("timestamp"               ) var timestamp             : Int?          = null,
    @SerializedName("open"                    ) var open                  : String?       = null,
    @SerializedName("high"                    ) var high                  : String?       = null,
    @SerializedName("low"                     ) var low                   : String?       = null,
    @SerializedName("close"                   ) var close                 : String?       = null,
    @SerializedName("volume"                  ) var volume                : String?       = null,
    @SerializedName("previous_close"          ) var previousClose         : String?       = null,
    @SerializedName("change"                  ) var change                : String?       = null,
    @SerializedName("percent_change"          ) var percentChange         : String?       = null,
    @SerializedName("average_volume"          ) var averageVolume         : String?       = null,
    @SerializedName("rolling_1d_change"       ) var rolling1dChange       : String?       = null,
    @SerializedName("rolling_7d_change"       ) var rolling7dChange       : String?       = null,
    @SerializedName("rolling_period_change"   ) var rollingPeriodChange   : String?       = null,
    @SerializedName("is_market_open"          ) var isMarketOpen          : Boolean?      = null,
    @SerializedName("fifty_two_week"          ) var fiftyTwoWeek          : FiftyTwoWeek? = FiftyTwoWeek(),
    @SerializedName("extended_change"         ) var extendedChange        : String?       = null,
    @SerializedName("extended_percent_change" ) var extendedPercentChange : String?       = null,
    @SerializedName("extended_price"          ) var extendedPrice         : String?       = null,
    @SerializedName("extended_timestamp"      ) var extendedTimestamp     : Int?          = null

) {
    fun change(): Double? {
        val close = this.close?.toDouble() ?: return null
        val previousClose = this.previousClose?.toDouble() ?: return null
        val left = close - previousClose
        val right = previousClose
        return (left / right) * 100
    }
}

data class TwelveDataEarningsCalenderResponse (

    @SerializedName("meta"     ) var meta     : Meta?               = Meta(),
    @SerializedName("earnings" ) var earnings : ArrayList<Earnings> = arrayListOf(),
    @SerializedName("status"   ) var status   : String?             = null

)
data class Meta (

    @SerializedName("symbol"            ) var symbol           : String? = null,
    @SerializedName("name"              ) var name             : String? = null,
    @SerializedName("currency"          ) var currency         : String? = null,
    @SerializedName("exchange"          ) var exchange         : String? = null,
    @SerializedName("mic_code"          ) var micCode          : String? = null,
    @SerializedName("exchange_timezone" ) var exchangeTimezone : String? = null
)
data class Earnings (

    @SerializedName("date"         ) var date        : String? = null,
    @SerializedName("time"         ) var time        : String? = null,
    @SerializedName("eps_estimate" ) var epsEstimate : Double? = null,
    @SerializedName("eps_actual"   ) var epsActual   : Double? = null,
    @SerializedName("difference"   ) var difference  : Double? = null,
    @SerializedName("surprise_prc" ) var surprisePrc : Double? = null

)



