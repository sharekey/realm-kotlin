package io.realm.kotlin.test.common

import io.realm.kotlin.Realm
import io.realm.kotlin.RealmConfiguration
import io.realm.kotlin.UpdatePolicy
import io.realm.kotlin.entities.SharekeyCompatibilityChannel
import io.realm.kotlin.entities.SharekeyCompatibilityParticipant
import io.realm.kotlin.entities.SharekeyCompatibilityProfile
import io.realm.kotlin.entities.SharekeyCompatibilityUser
import io.realm.kotlin.ext.query
import io.realm.kotlin.ext.realmListOf
import io.realm.kotlin.test.platform.PlatformUtils
import io.realm.kotlin.test.util.use
import kotlin.test.AfterTest
import kotlin.test.BeforeTest
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertNull

// Covers generated Kotlin models only, not Realm JS/Core shared-file interoperability.
class SharekeyCompatibilityTests {
    private lateinit var directory: String

    @BeforeTest
    fun setup() {
        directory = PlatformUtils.createTempDir()
    }

    @AfterTest
    fun tearDown() {
        PlatformUtils.deleteTempDir(directory)
    }

    @Test
    fun encryptedChannelGraphSurvivesNativeStyleUpdateAndReopen() {
        val configuration = RealmConfiguration.Builder(
            setOf(
                SharekeyCompatibilityChannel::class,
                SharekeyCompatibilityParticipant::class,
                SharekeyCompatibilityUser::class,
                SharekeyCompatibilityProfile::class
            )
        ).directory(directory)
            .encryptionKey(ByteArray(64) { it.toByte() })
            .build()

        val channel = SharekeyCompatibilityChannel("channel", "Original").apply {
            isDirect = true
            lastUpdate = 1
            key = byteArrayOf(1, 2, 3)
            samples = realmListOf(2, 4)
            participants = realmListOf(SharekeyCompatibilityParticipant().apply { id = "peer" })
            user = SharekeyCompatibilityUser.create("peer").apply {
                profile = SharekeyCompatibilityProfile().apply {
                    name = "Peer"
                    channels = realmListOf("channel", null)
                }
            }
        }
        assertEquals("Original", channel.name)
        assertEquals("peer", channel.user?._id)

        Realm.open(configuration).use { realm ->
            realm.writeBlocking { copyToRealm(channel, updatePolicy = UpdatePolicy.ALL) }
        }

        Realm.open(configuration).use { realm ->
            realm.writeBlocking {
                val existing = query<SharekeyCompatibilityChannel>(
                    "isDirect == true AND participants.id == $0", "peer"
                ).find().single()
                assertNull(existing.optionalKey)
                existing.name = "Renamed"
                existing.lastUpdate = 2
                existing.optionalKey = byteArrayOf(4, 5)
                assertNotNull(assertNotNull(existing.user).profile).name = "Updated peer"
                // The native consumer changes an existing object before its UpdatePolicy.ALL upsert.
                copyToRealm(existing, updatePolicy = UpdatePolicy.ALL)
            }
        }

        Realm.open(configuration).use { realm ->
            val stored = realm.query<SharekeyCompatibilityChannel>(
                "isDirect == true AND participants.id == $0 AND lastUpdate == $1", "peer", 2L
            ).find().single()
            assertEquals("Renamed", stored.name)
            assertContentEquals(byteArrayOf(1, 2, 3), stored.key)
            assertContentEquals(byteArrayOf(4, 5), stored.optionalKey)
            assertEquals(listOf(2, 4), stored.samples.toList())
            assertEquals("peer", stored.participants.single().id)
            val user = realm.query<SharekeyCompatibilityUser>("_id == $0", "peer").find().single()
            assertEquals(user._id, assertNotNull(stored.user)._id)
            val profile = assertNotNull(user.profile)
            assertEquals("Updated peer", profile.name)
            assertEquals(listOf("channel", null), profile.channels.toList())
            assertEquals(1, realm.query<SharekeyCompatibilityChannel>().find().size)
        }
    }
}
