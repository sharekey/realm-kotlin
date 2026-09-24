package io.realm.kotlin.entities

import io.realm.kotlin.types.RealmObject

class FactoryCompanionModel : RealmObject {
    var value: String = ""

    companion object Factory {
        fun create(value: String): FactoryCompanionModel = FactoryCompanionModel().apply {
            this.value = value
        }
    }
}

class CreatorCompanionModel : RealmObject {
    var value: String = ""

    companion object CREATOR
}
