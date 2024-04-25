package org.github.daymon.external

import com.google.gson.annotations.SerializedName
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.engine.cio.*
import io.ktor.client.plugins.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import org.github.daymon.handler.ConfigHandler


@Serializable
data class LoginRequest(val email: String, val password: String)

@Serializable
data class LoginResponse(val token: String)

object LeetifyClient {
    private var token: String? = null
    private val configHandler = ConfigHandler
    private val ktorClient = HttpClient(CIO) {
        install(ContentNegotiation) {
            json(Json {
                prettyPrint = true
                isLenient = true
                ignoreUnknownKeys = true
            })
        }

        install(DefaultRequest) {

            if (token != null) {
                headers {
                    append("Authorization", "Bearer $token")
                }
            }
            else {
                val internalHttpClient = HttpClient(CIO) {
                    install(ContentNegotiation) {
                        json(Json {
                            prettyPrint = true
                            isLenient = true
                            ignoreUnknownKeys = true
                        })
                    }
                }

                val token = runBlocking {
                    val tokenResponse = internalHttpClient.post("https://api.leetify.com/api/login") {
                        contentType(ContentType.Application.Json)
                        setBody(LoginRequest(email = "spam@montague.im", password = configHandler.config.leetifyPassword))
                    }
                    val token = tokenResponse.body<LoginResponse>().token
                    return@runBlocking token
                }
                this@LeetifyClient.token = token

                headers {
                    append("Authorization", "Bearer $token")
                }
            }
        }
    }





    suspend fun getPlayerStats(
        steam64Id: String
    ): LeetifyPlayerStatsResponse? {
        val response = ktorClient.get(
            "https://api.leetify.com/api/profile/$steam64Id"
        )

        if (response.status != HttpStatusCode.OK) {
            println("Failed to get player stats for $steam64Id with status ${response.status} and reason ${response.bodyAsText()}")
            return null
        }



        val body = response.body<LeetifyPlayerStatsResponse>()
        return body
    }
}

@Serializable
data class LeetifyPlayerStatsResponse (

    @SerializedName("highlights"        ) var highlights        : ArrayList<Highlights>        = arrayListOf(),
    @SerializedName("personalBestsCs2"  ) var personalBestsCs2  : ArrayList<PersonalBestsCs2>  = arrayListOf(),
    @SerializedName("personalBestsCsgo" ) var personalBestsCsgo : ArrayList<PersonalBestsCsgo> = arrayListOf(),
    @SerializedName("recentGameRatings" ) var recentGameRatings : RecentGameRatings?           = RecentGameRatings(),
    @SerializedName("teammates"         ) var teammates         : ArrayList<Teammates>         = arrayListOf(),
    @SerializedName("games"             ) var games             : ArrayList<Games>             = arrayListOf(),
    @SerializedName("meta"              ) var meta              : LeetifyMeta?                 = LeetifyMeta()
)
@Serializable
data class LeetifyMeta (

    @SerializedName("name"           ) var name           : String?           = null,
    @SerializedName("steam64Id"      ) var steam64Id      : String?           = null,
    @SerializedName("steamAvatarUrl" ) var steamAvatarUrl : String?           = null,
    @SerializedName("isCollector"    ) var isCollector    : Boolean?          = null,
    @SerializedName("isLeetifyStaff" ) var isLeetifyStaff : Boolean?          = null,
    @SerializedName("isProPlan"      ) var isProPlan      : Boolean?          = null,
    @SerializedName("leetifyUserId"  ) var leetifyUserId  : String?           = null,
    @SerializedName("faceitNickname" ) var faceitNickname : String?           = null,
    @SerializedName("platformBans"   ) var platformBans   : ArrayList<String> = arrayListOf()

)
@Serializable
data class Highlights (

    @SerializedName("createdAt"    ) var createdAt    : String?  = null,
    @SerializedName("description"  ) var description  : String?  = null,
    @SerializedName("gameId"       ) var gameId       : String?  = null,
    @SerializedName("id"           ) var id           : String?  = null,
    @SerializedName("isPinned"     ) var isPinned     : Boolean? = null,
    @SerializedName("pendingPro"   ) var pendingPro   : Boolean? = null,
    @SerializedName("rankValue"    ) var rankValue    : String?  = null,
    @SerializedName("roundNumber"  ) var roundNumber  : Int?     = null,
    @SerializedName("steam64Id"    ) var steam64Id    : String?  = null,
    @SerializedName("thumbnailUrl" ) var thumbnailUrl : String?  = null,
    @SerializedName("url"          ) var url          : String?  = null,
    @SerializedName("username"     ) var username     : String?  = null,
    @SerializedName("status"       ) var status       : String?  = null
)

@Serializable
data class PersonalBestsCs2 (

    @SerializedName("gameId"  ) var gameId  : String? = null,
    @SerializedName("skillId" ) var skillId : String? = null,
    @SerializedName("value"   ) var value   : String? = null

)

@Serializable
data class Rank (

    @SerializedName("type"       ) var type       : String? = null,
    @SerializedName("dataSource" ) var dataSource : String? = null,
    @SerializedName("skillLevel" ) var skillLevel : Int?    = null

)

@Serializable
data class Games (
    @SerializedName("enemyTeamSteam64Ids"             ) var enemyTeamSteam64Ids             : ArrayList<String>                = arrayListOf(),
    @SerializedName("isCompletedLongMatch"            ) var isCompletedLongMatch            : Boolean?                         = null,
    @SerializedName("ownTeamSteam64Ids"               ) var ownTeamSteam64Ids               : ArrayList<String>                = arrayListOf(),
    @SerializedName("ctLeetifyRating"                 ) var ctLeetifyRating                 : Double?                          = null,
    @SerializedName("ctLeetifyRatingRounds"           ) var ctLeetifyRatingRounds           : Int?                             = null,
    @SerializedName("dataSource"                      ) var dataSource                      : String?                          = null,
    @SerializedName("elo"                             ) var elo                             : String?                          = null,
    @SerializedName("gameFinishedAt"                  ) var gameFinishedAt                  : String?                          = null,
    @SerializedName("gameId"                          ) var gameId                          : String?                          = null,
    @SerializedName("isCs2"                           ) var isCs2                           : Boolean?                         = null,
    @SerializedName("mapName"                         ) var mapName                         : String?                          = null,
    @SerializedName("matchResult"                     ) var matchResult                     : String?                          = null,
    @SerializedName("rankType"                        ) var rankType                        : Int?                             = null,
    @SerializedName("scores"                          ) var scores                          : ArrayList<String>?                          = null,
    @SerializedName("skillLevel"                      ) var skillLevel                      : Int?                             = null,
    @SerializedName("tLeetifyRating"                  ) var tLeetifyRating                  : Double?                          = null,
    @SerializedName("tLeetifyRatingRounds"            ) var tLeetifyRatingRounds            : Int?                             = null,
    @SerializedName("deaths"                          ) var deaths                          : Int?                             = null,
    @SerializedName("hasBannedPlayer"                 ) var hasBannedPlayer                 : Boolean?                         = null,
    @SerializedName("kills"                           ) var kills                           : Int?                             = null,
    @SerializedName("partySize"                       ) var partySize                       : Int?                             = null
)

@Serializable
data class Teammates (

    @SerializedName("isCollector"              ) var isCollector              : Boolean? = null,
    @SerializedName("isProPlan"                ) var isProPlan                : Boolean? = null,
    @SerializedName("leetifyUserId"            ) var leetifyUserId            : String?  = null,
    @SerializedName("isBanned"                 ) var isBanned                 : Boolean? = null,
    @SerializedName("isLeetifyStaff"           ) var isLeetifyStaff           : Boolean? = null,
    @SerializedName("matchesPlayedTogether"    ) var matchesPlayedTogether    : Int?     = null,
    @SerializedName("profileUserLeetifyRating" ) var profileUserLeetifyRating : Double?  = null,
    @SerializedName("rank"                     ) var rank                     : Rank?    = Rank(),
    @SerializedName("steam64Id"                ) var steam64Id                : String?  = null,
    @SerializedName("steamAvatarUrl"           ) var steamAvatarUrl           : String?  = null,
    @SerializedName("steamNickname"            ) var steamNickname            : String?  = null,
    @SerializedName("teammateLeetifyRating"    ) var teammateLeetifyRating    : Double?  = null,
    @SerializedName("winRateTogether"          ) var winRateTogether          : Double?  = null

)

@Serializable
data class RecentGameRatings (

    @SerializedName("aim"                 ) var aim                 : Double? = null,
    @SerializedName("leetifyRatingRounds" ) var leetifyRatingRounds : Int?    = null,
    @SerializedName("positioning"         ) var positioning         : Double? = null,
    @SerializedName("utility"             ) var utility             : Double? = null,
    @SerializedName("gamesPlayed"         ) var gamesPlayed         : Int?    = null,
    @SerializedName("clutch"              ) var clutch              : Double? = null,
    @SerializedName("ctLeetify"           ) var ctLeetify           : Double? = null,
    @SerializedName("leetify"             ) var leetify             : Double? = null,
    @SerializedName("opening"             ) var opening             : Double? = null,
    @SerializedName("tLeetify"            ) var tLeetify            : Double? = null

)

@Serializable
data class PersonalBestsCsgo (
    @SerializedName("gameId"  ) var gameId  : String? = null,
    @SerializedName("skillId" ) var skillId : String? = null,
    @SerializedName("value"   ) var value   : String? = null
)