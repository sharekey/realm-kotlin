package io.realm.kotlin.entities

import io.realm.kotlin.ext.realmListOf
import io.realm.kotlin.types.EmbeddedRealmObject
import io.realm.kotlin.types.RealmList
import io.realm.kotlin.types.RealmObject
import io.realm.kotlin.types.annotations.Index
import io.realm.kotlin.types.annotations.PrimaryKey

// Synthetic shapes representing the mobile consumer; these are not copies of its schemas.
class SharekeyCompatibilityChannel() : RealmObject {
    @PrimaryKey
    var _id: String = ""
    var name: String = ""
    var isDirect: Boolean = false
    @Index
    var lastUpdate: Long = 0
    var key: ByteArray = byteArrayOf()
    var optionalKey: ByteArray? = null
    var user: SharekeyCompatibilityUser? = null
    var participants: RealmList<SharekeyCompatibilityParticipant> = realmListOf()
    var samples: RealmList<Int> = realmListOf()

    constructor(id: String, name: String) : this() {
        this._id = id
        this.name = name
    }
}

class SharekeyCompatibilityParticipant : EmbeddedRealmObject {
    var id: String = ""
}

class SharekeyCompatibilityUser : RealmObject {
    @PrimaryKey
    var _id: String = ""
    var profile: SharekeyCompatibilityProfile? = null

    companion object {
        fun create(id: String): SharekeyCompatibilityUser = SharekeyCompatibilityUser().apply {
            _id = id
        }
    }
}

class SharekeyCompatibilityProfile : EmbeddedRealmObject {
    var name: String = ""
    var channels: RealmList<String?> = realmListOf()
}
