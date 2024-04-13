package org.github.daymon.internal.command

import net.dv8tion.jda.api.Permission
import org.github.daymon.ext.emptyEnumSet
import java.util.*


abstract class Command(
    override val name: String,
    override val description: String,
    override val memberPermissions: EnumSet<Permission> = emptyEnumSet(),
    override val selfPermissions: EnumSet<Permission> = emptyEnumSet(),
    override val children: List<SubCommand> = listOf(),
    override val options: List<CommandOptionData<*>> = listOf(),
    override val id: Int = "$name$children".hashCode(),
    override val deferredReplyEnabled: Boolean = false,
    val group: Map<String, List<SubCommand>> = mapOf()

) : AbstractCommand()