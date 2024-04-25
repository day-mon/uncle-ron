package org.github.daymon.external

import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.engine.cio.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.request.*
import io.ktor.serialization.kotlinx.json.*
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json




object Pastecord {

    private val ktorClient: HttpClient = HttpClient(CIO) {
        install(ContentNegotiation) {
            json(Json {
                prettyPrint = true
                isLenient = true
                ignoreUnknownKeys = true
            })
        }
    }

    /**
     * Uploads content to Pastecord and returns the key.
     * @throws IllegalStateException if the upload fails.
     * @return The key of the uploaded content.
     */
    suspend fun upload(content: String): String {
        val response = ktorClient.post {
            url("https://pastecord.com/documents")
            setBody(content)
        }

        if (response.status.value != 200) {
            throw IllegalStateException("Failed to upload content to Pastecord.")
        }

        val pastecordResponse = response.body<PastecordResponse>()
        return pastecordResponse.key


    }
}


@Serializable
data class PastecordResponse(
    val key: String
)