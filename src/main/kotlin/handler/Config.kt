package org.github.daymon.handler

import dev.minn.jda.ktx.util.SLF4J
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.io.File
import kotlin.system.exitProcess


@Serializable
data class Config(
    val developerIds: List<String>,
    val token: String,
    val openRouterApiKey: String,
    val alphaVantageApiKey: String

)


private const val CONFIG_NAME = "config.json"

object ConfigHandler
{
    private val formatter = Json { prettyPrint = true; isLenient = true }
    private val logger by SLF4J
    val config = initConfig()

    private fun initConfig(): Config
    {
        val configFile = File(CONFIG_NAME)

        if (!configFile.exists())
        {
            configFile.createNewFile()


            val defaultValues = formatter.encodeToString(
                Config(
                    token = "token",
                    developerIds = listOf("-1".repeat(3)),
                    openRouterApiKey = "",
                    alphaVantageApiKey = ""
                )
            )
            configFile.writeText(defaultValues)
        }
        return loadConfig()
    }


    private fun loadConfig(): Config
    {
        try
        {
            val config: Config = Json.decodeFromString(
                File(CONFIG_NAME)
                    .readLines()
                    .joinToString(separator = "\n")
            )
            return config
        } catch (e: Exception)
        {
            logger.error("An error has occurred while attempting to decode json", e)
            exitProcess(1)
        }
    }


}