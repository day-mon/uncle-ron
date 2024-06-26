package org.github.daymon.external

import dev.minn.jda.ktx.util.SLF4J
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.engine.cio.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import kotlinx.serialization.SerialName
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
        val response =  ktorClient.get("https://api.twelvedata.com/quote?symbol=$symbol&apikey=${configHandler.config.twelveDataApiKey}") {

        }
        if (response.status != HttpStatusCode.OK) {
            logger.error("Failed to get quote for $symbol - ${response.status} - ${response.bodyAsText()}")
            throw Exception("Failed to get quote for $symbol")
        }

        logger.info("Quote response: ${response.bodyAsText()}")

        return response.body<TwelveDataQuoteResponse>()
    }
}

@Serializable
data class FiftyTwoWeek (
    @SerialName("low"                 ) var low               : Double? = null,
    @SerialName("high"                ) var high              : Double? = null,
    @SerialName("low_change"          ) var lowChange         : Double? = null,
    @SerialName("high_change"         ) var highChange        : Double? = null,
    @SerialName("low_change_percent"  ) var lowChangePercent  : Double? = null,
    @SerialName("high_change_percent" ) var highChangePercent : Double? = null,
    @SerialName("range"               ) var range             : String? = null
)
@Serializable
data class TwelveDataQuoteResponse (

    @SerialName("symbol"                  ) var symbol                : String?       = null,
    @SerialName("name"                    ) var name                  : String?       = null,
    @SerialName("exchange"                ) var exchange              : String?       = null,
    @SerialName("mic_code"                ) var micCode               : String?       = null,
    @SerialName("currency"                ) var currency              : String?       = null,
    @SerialName("datetime"                ) var datetime              : String?       = null,
    @SerialName("timestamp"               ) var timestamp             : Int?          = null,
    @SerialName("open"                    ) var open                  : String?       = null,
    @SerialName("high"                    ) var high                  : String?       = null,
    @SerialName("low"                     ) var low                   : String?       = null,
    @SerialName("close"                   ) var close                 : String?       = null,
    @SerialName("volume"                  ) var volume                : String?       = null,
    @SerialName("previous_close"          ) var previousClose         : String?       = null,
    @SerialName("change"                  ) var change                : String?       = null,
    @SerialName("percent_change"          ) var percentChange         : String?       = null,
    @SerialName("average_volume"          ) var averageVolume         : String?       = null,
    @SerialName("rolling_1d_change"       ) var rolling1dChange       : String?       = null,
    @SerialName("rolling_7d_change"       ) var rolling7dChange       : String?       = null,
    @SerialName("rolling_period_change"   ) var rollingPeriodChange   : String?       = null,
    @SerialName("is_market_open"          ) var isMarketOpen          : Boolean?      = null,
    @SerialName("fifty_two_week"          ) var fiftyTwoWeek          : FiftyTwoWeek? = FiftyTwoWeek(),
    @SerialName("extended_change"         ) var extendedChange        : String?       = null,
    @SerialName("extended_percent_change" ) var extendedPercentChange : String?       = null,
    @SerialName("extended_price"          ) var extendedPrice         : String?       = null,
    @SerialName("extended_timestamp"      ) var extendedTimestamp     : Int?          = null

)

data class TwelveDataEarningsCalenderResponse (

    @SerialName("meta"     ) var meta     : Meta?               = Meta(),
    @SerialName("earnings" ) var earnings : ArrayList<Earnings> = arrayListOf(),
    @SerialName("status"   ) var status   : String?             = null

)
data class Meta (

    @SerialName("symbol"            ) var symbol           : String? = null,
    @SerialName("name"              ) var name             : String? = null,
    @SerialName("currency"          ) var currency         : String? = null,
    @SerialName("exchange"          ) var exchange         : String? = null,
    @SerialName("mic_code"          ) var micCode          : String? = null,
    @SerialName("exchange_timezone" ) var exchangeTimezone : String? = null
)
data class Earnings (

    @SerialName("date"         ) var date        : String? = null,
    @SerialName("time"         ) var time        : String? = null,
    @SerialName("eps_estimate" ) var epsEstimate : Double? = null,
    @SerialName("eps_actual"   ) var epsActual   : Double? = null,
    @SerialName("difference"   ) var difference  : Double? = null,
    @SerialName("surprise_prc" ) var surprisePrc : Double? = null

)



