package io.realm.sample.minandroidsample

import io.realm.kotlin.Realm
import io.realm.kotlin.RealmConfiguration
import io.realm.kotlin.ext.query
import io.realm.kotlin.types.RealmObject

class Sample : RealmObject {
    var name: String = ""

    companion object Factory {
        fun create(name: String): Sample = Sample().apply { this.name = name }
    }
}

actual class Platform actual constructor() {
    init {
        val configuration = RealmConfiguration.create(schema = setOf(Sample::class))
        val realm = Realm.open(configuration)
        try {
            // Exercise generated accessors and named companion lookup after R8 shrinking.
            realm.writeBlocking {
                val sample = copyToRealm(Sample.create("unmanaged"))
                sample.name = "managed"
                check(sample.name == "managed")
            }
            check(realm.query<Sample>("name == $0", "managed").find().single().name == "managed")
            realm.writeBlocking {
                delete(query<Sample>("name == $0", "managed").find())
            }
            check(realm.query<Sample>("name == $0", "managed").find().isEmpty())
        } finally {
            realm.close()
        }
    }

    actual val platform: String = "Android ${android.os.Build.VERSION.SDK_INT}"
}
