package org.github.daymon.internal.command


import dev.minn.jda.ktx.util.SLF4J
import net.dv8tion.jda.api.Permission
import net.dv8tion.jda.api.entities.Member
import net.dv8tion.jda.api.entities.MessageEmbed
import net.dv8tion.jda.api.interactions.commands.OptionMapping
import net.dv8tion.jda.api.interactions.commands.SlashCommandInteraction
import org.github.daymon.ext.empty
import org.github.daymon.ext.replyEmbed
import org.github.daymon.internal.misc.Pagable
import java.util.*


class CommandEvent(
    val slashEvent: SlashCommandInteraction,
    val command: AbstractCommand
)
{
    val logger by SLF4J
    val jda = slashEvent.jda
    val user = slashEvent.user
    val guild = slashEvent.guild!!
    val guildId = slashEvent.guild!!.idLong
    val member = slashEvent.member!!
    val hook = slashEvent.hook
    val options: MutableList<OptionMapping> = slashEvent.options



    fun replyMessage(message: String) = when  {
        slashEvent.isAcknowledged -> hook.sendMessage(message).queue()
        else -> slashEvent.reply(message).queue()
    }

    fun replyMessageAndClear(message: String) = when  {
        slashEvent.isAcknowledged -> hook.editOriginal(message).setActionRow(emptyList()).setEmbeds(emptyList()).queue()
        else -> slashEvent.reply(message).addActionRow(emptyList()).addActionRow(emptyList()).queue()
    }



    fun hasSelfPermissions(permissions: EnumSet<Permission>) = guild.selfMember.hasPermission(permissions)
    fun hasMemberPermissions(permissions: EnumSet<Permission>) = member.hasPermission(permissions)
    fun sentWithOption(option: String) = slashEvent.getOption(option) != null
    inline fun <reified T> getOption(name: String): T = when (T::class)
    {
        String::class -> slashEvent.getOption(name)?.asString as T
        // Could break if number is over 2.147 billion lol
        Int::class -> slashEvent.getOption(name)?.asLong?.toInt() as T
        Long::class -> slashEvent.getOption(name)?.asLong as T
        Double::class -> slashEvent.getOption(name)?.asDouble as T
        Boolean::class -> slashEvent.getOption(name)?.asBoolean as T
        Member::class -> slashEvent.getOption(name)?.asMember as T
        else -> throw IllegalArgumentException("Unknown type ${T::class}")
    }


    fun getOption(option: String) = slashEvent.getOption(option)


    fun sentWithAnyOptions() = slashEvent.options.isNotEmpty()
    fun replyEmbed(embed: MessageEmbed, content: String = String.empty) = slashEvent.replyEmbed(embed, content)



}