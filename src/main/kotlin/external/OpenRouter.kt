package org.github.daymon.external

import com.google.gson.annotations.SerializedName
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
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import org.github.daymon.handler.ConfigHandler


object OpenRouter {

    private val ktorClient: HttpClient = HttpClient(CIO) {
        install(ContentNegotiation) {
            json(Json {
                prettyPrint = true
                isLenient = true
                ignoreUnknownKeys = true
            })
        }
    }
    private val cache: MutableMap<String, Any> = mutableMapOf()
    private val configHandler: ConfigHandler = ConfigHandler

    suspend fun chat(
        model: String,
        messages: List<ChatInteraction>
    ): ChatInteractionResponse {
        val jsonBody = buildJsonObject {
            put("model", model)
            put("messages", buildJsonArray {
                messages.forEach {
                    add(buildJsonObject {
                        put("role", it.role.value)
                        put("content", it.message)
                    })
                }
            })
        }.toString()


        val response = ktorClient.post {
            url("https://openrouter.ai/api/v1/chat/completions")
            header("Authorization", "Bearer ${configHandler.config.openRouterApiKey}")
            header("HTTP-Referer", "damon.systems")
            header("X-Title", "Uncle Ron")
            header("Content-Type", "application/json")
            setBody(jsonBody)
        }

        if (response.status != HttpStatusCode.OK) {
            throw IllegalStateException("Failed to send message to OpenRouter. Response code: ${response.status.value} - Body: ${response.bodyAsText()}}")
        }
        return response.body<ChatInteractionResponse>()
    }

    suspend fun chat(
        model: String,
        prompt: String
    ): ChatInteractionResponse {
        return chat(model, listOf(ChatInteraction(ChatInteractionRole.USER, prompt)))
    }


    suspend fun list(): ListModelResponse {
        if (cache.containsKey("list")) {
            return cache["list"] as ListModelResponse
        }


        val response = ktorClient.get {
            url("https://openrouter.ai/api/v1/models")
        }

        if (response.status != HttpStatusCode.OK) {
            throw IllegalStateException("Failed to get list of models from OpenRouter")
        }


        val body =  response.body<ListModelResponse>()
        cache["list"] = body
        return body
    }

}

enum class ChatInteractionRole(
    val value: String
) {
    SYSTEM("system"),
    USER("user"),
    BOT("assistant")
}


@Serializable
data class ModelUsage(
   @SerialName("completion_tokens") val completionTokens: Int,
   @SerialName("prompt_tokens") val promptTokens: Int,
   @SerialName("total_tokens") val totalTokens: Int,
   @SerialName("total_cost") val totalCost: Double? = null
)
@Serializable
data class ChatInteractionResponseMessage(
    val content: String? = null,
    val role: String

)
@Serializable
data class NonStreamingChoice(
    val finishReason: String? = null,
    val message: ChatInteractionResponseMessage
)
@Serializable
data class ChatInteractionResponse(
    val id: String,
    val created: Int,
    val model: String,
    val choices: List<NonStreamingChoice>,
    val usage: ModelUsage? = null
)

data class ChatInteraction(
    val role: ChatInteractionRole,
    val message: String
)


@Serializable
data class  ListModelResponse(
    @SerializedName("data" ) var data : ArrayList<Data> = arrayListOf()
)
@Serializable
data class TopProvider (
    @SerializedName("max_completion_tokens" ) var maxCompletionTokens : String?  = null,
    @SerializedName("is_moderated"          ) var isModerated         : Boolean? = null
)
@Serializable
data class Architecture (

    @SerializedName("modality"      ) var modality     : String? = null,
    @SerializedName("tokenizer"     ) var tokenizer    : String? = null,
    @SerializedName("instruct_type" ) var instructType : String? = null

)
@Serializable

data class Pricing (

    @SerializedName("prompt"     ) var prompt     : String? = null,
    @SerializedName("completion" ) var completion : String? = null,
    @SerializedName("request"    ) var request    : String? = null,
    @SerializedName("image"      ) var image      : String? = null

)
@Serializable

data class Data (
    @SerializedName("id"                 ) var id               : String?       = null,
    @SerializedName("name"               ) var name             : String?       = null,
    @SerializedName("description"        ) var description      : String?       = null,
    @SerializedName("pricing"            ) var pricing          : Pricing?      = Pricing(),
    @SerializedName("context_length"     ) var contextLength    : Int?          = null,
    @SerializedName("architecture"       ) var architecture     : Architecture? = Architecture(),
    @SerializedName("top_provider"       ) var topProvider      : TopProvider?  = TopProvider(),
    @SerializedName("per_request_limits" ) var perRequestLimits : String?       = null
)