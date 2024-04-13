package org.github.daymon.internal.command

import net.dv8tion.jda.api.Permission
import net.dv8tion.jda.api.interactions.commands.build.SubcommandData
import org.github.daymon.ext.emptyEnumSet
import java.util.*

abstract class SubCommand(
    override val name: String,
    override val description: String,
    override val memberPermissions: EnumSet<Permission> = emptyEnumSet(),
    override val selfPermissions: EnumSet<Permission> = emptyEnumSet(),
    override val children: List<SubCommand> = listOf(),
    override val options: List<CommandOptionData<*>> = listOf(),
    override val id: Int = "$name$children".hashCode(),
    override val deferredReplyEnabled: Boolean= false,
    val subCommandData: SubcommandData
    = SubcommandData(name, description)
        .addOptions(options.map { it.asOptionData() })
) : AbstractCommand()