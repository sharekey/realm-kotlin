/*
 * Copyright 2021 Realm Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package io.realm.kotlin.test.android

import io.realm.kotlin.internal.platform.OS_NAME
import io.realm.kotlin.types.RealmInstant
import java.util.concurrent.TimeUnit
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class PlatformInfoTest {
    @Test
    fun realmInstantNowMatchesWallClock() {
        val before = System.currentTimeMillis()
        val instant = RealmInstant.now()
        val after = System.currentTimeMillis()
        val actual = TimeUnit.SECONDS.toMillis(instant.epochSeconds) +
            TimeUnit.NANOSECONDS.toMillis(instant.nanosecondsOfSecond.toLong())
        assertTrue(actual in before..after, "Expected $actual to be between $before and $after")
    }

    @Test
    fun platformInfo() {
        assertEquals("Android", OS_NAME)
    }
}
