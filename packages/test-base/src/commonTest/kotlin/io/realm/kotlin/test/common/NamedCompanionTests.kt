package io.realm.kotlin.test.common

import io.realm.kotlin.Realm
import io.realm.kotlin.RealmConfiguration
import io.realm.kotlin.entities.CreatorCompanionModel
import io.realm.kotlin.entities.FactoryCompanionModel
import io.realm.kotlin.ext.query
import io.realm.kotlin.test.platform.PlatformUtils
import io.realm.kotlin.test.util.use
import kotlin.test.AfterTest
import kotlin.test.BeforeTest
import kotlin.test.Test
import kotlin.test.assertEquals

class NamedCompanionTests {
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
    fun namedCompanionsSupportManagedAccessorsAndEncryptedReopen() {
        val configuration = RealmConfiguration.Builder(
            setOf(FactoryCompanionModel::class, CreatorCompanionModel::class)
        ).directory(directory)
            .encryptionKey(ByteArray(64) { it.toByte() })
            .build()

        val unmanaged = FactoryCompanionModel.create("unmanaged")
        assertEquals("unmanaged", unmanaged.value)

        Realm.open(configuration).use { realm ->
            realm.writeBlocking {
                val factory = copyToRealm(unmanaged)
                factory.value = "factory"
                val creator = copyToRealm(CreatorCompanionModel())
                creator.value = "creator"
                assertEquals("factory", factory.value)
                assertEquals("creator", creator.value)
            }
        }

        Realm.open(configuration).use { realm ->
            assertEquals("factory", realm.query<FactoryCompanionModel>().find().single().value)
            assertEquals("creator", realm.query<CreatorCompanionModel>().find().single().value)
        }
    }
}
