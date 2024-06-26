package org.github.daymon.external

import dev.minn.jda.ktx.util.SLF4J
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import org.jsoup.Jsoup
import java.util.*

data class RawFinancials(
    val incomeStatement: String,
    val balanceSheet: String,
    val cashFlow: String
)

object YahooFinance {
    private val logger by SLF4J
    private fun url(security: String): String {
        return "https://finance.yahoo.com/quote/$security"
    }

    private fun financials(security: String): String {
        return "${url(security)}/financials"
    }

    private fun holders(security: String): String {
        return "${url(security)}/holders"
    }

    private fun balanceSheet(security: String): String {
        return "${url(security)}/balance-sheet"
    }

    private fun cashFlow(security: String): String {
        return "${url(security)}/cash-flow"
    }


    private suspend fun fetchTable(url: String): String? {
        val doc = try { Jsoup.connect(url).get() } catch (
            e: Exception
        ) {
            logger.error("Failed to fetch table from $url", e)
            return null
        }

        val tableContainer = doc.select("div[class^=tableContainer]").first()?.text()

        return tableContainer
    }

    suspend fun getFullFinancialsRaw(security: String): RawFinancials = coroutineScope {
        val financialsDeferred = async { fetchTable(financials(security)) }
        val balanceSheetDeferred = async { fetchTable(balanceSheet(security)) }
        val cashFlowDeferred = async { fetchTable(cashFlow(security)) }

        val financialsTable = financialsDeferred.await()
        val balanceSheetTable = balanceSheetDeferred.await()
        val cashFlowTable = cashFlowDeferred.await()

        RawFinancials(
            financialsTable ?: "No financials found",
            balanceSheetTable ?: "No balance sheet found",
            cashFlowTable ?: "No cash flow found"
        )
    }
}