#!/usr/bin/env python3
#
# Copyright 2011-2016 Google Inc.
# Copyright 2019-2020 Tim Hatch
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import itertools
import unittest

from sre_yield.fastdivmod import (
    divmod_iter,
    divmod_iter_basic,
    divmod_iter_chunking,
    find_largest_power,
    powersum,
)
from sre_yield.testing_utils import UnitTest, data_provider

BIG_NUMBERS_1 = [
    3280387013,
    1095513149,
    1930549412,
    2798570524,
    3387541015,
    403123853,
    3589583795,
    1912923438,
    4059906723,
    3871601466,
    131383005,
    2325348895,
    1001090106,
    92297590,
    2758633300,
    3693442238,
    2878940491,
    1302957854,
    3790218437,
    2170177478,
    148287320,
    3424825177,
    743061145,
    1609337232,
    2183675158,
    3343385572,
    1689017786,
    127023495,
    186776493,
    731644239,
    2157098197,
    4217987068,
    3309371710,
    997188872,
    2206632490,
    2481609807,
    24520514,
    3475229417,
    2411013677,
    241047739,
    3736665165,
    2167757908,
    1532401220,
    1486393353,
    2630463311,
    2510240338,
    3698004908,
    1096479554,
    2891000578,
    71685719,
    3245220485,
    1071848708,
    2683504528,
    1479284938,
    298566281,
    685586412,
    3056255487,
    1382987044,
    2034831020,
    101509732,
    1660250125,
    807622669,
    467127924,
    2601241111,
    89413097,
    76727542,
    629048405,
    688172269,
    2912742879,
    2218778024,
    2785313880,
    2709900431,
    1282502806,
    4157113077,
    3760390974,
    1315920533,
    3687291313,
    4034213119,
    3194777578,
    1083869817,
    3519356807,
    2449336413,
    2185596105,
    1623363793,
    1490056821,
    833733247,
    2860265804,
    2146624322,
    3743585873,
    3864088758,
    77708773,
    3361672519,
    1456404717,
    914956012,
    2896762490,
    3597898711,
    1007773002,
    3115849270,
    363698846,
    728830788,
]

BIG_NUMBERS_2 = [
    563135587954077565464163053623990250244363813542408020885273996854876267441441391008145673052789883846076897089872619443564,
    2007273141358993952672385041115124091595426495785740901791314810991369151061943532668661908090566083242815316368166202208310,
    2224141829638175177515471502929992697612797568920485431623738696756995865183242506696740255396541114021746706644195255545985,
    973359961993983112081682526708367995286540900591953247307798204695857894002711822112830426004406105962343916352234340504429,
    899790349747673068327744943308763762169915928371732420305130801536569472071119235416470119806902776727592607801425274924783,
    770038426542332919310096281438989278856819613662552896352789838247842258207308888325353366786955958988744012088787428251097,
    2346127576788887084653625341303468477418584541096844908994180123452696593545064433052424475826588911218196470657565178711637,
    275726442864485220280678656305877539433689656222710574502555008861502100233311942103944104814076921778515218663017863562288,
    103489099001693846190348188516764165017673481667440115358869336937831198587011943194944926194248634181189746774300623695689,
    193539785478113506791795247377648651336289568803100302655817683272207217560113649179904031579260379348369431181608479411660,
]


class FastDivmodTest(UnitTest):
    def test_find_largest_power(self):
        inputs = list(range(20))
        outputs = [find_largest_power(n, 2) for n in inputs]
        self.assertEqual(
            [0, 1, 2, 2, 4, 4, 4, 4, 8, 8, 8, 8, 8, 8, 8, 8, 16, 16, 16, 16], outputs
        )
        for (n, r) in zip(inputs[1:], outputs[1:]):
            self.assertLessEqual(r, n)

    def test_divmod_iter_switching(self):
        n = 2 ** 999 - 1
        count = 0
        v1 = []
        for v in divmod_iter(n, 2):
            count += 1
            v1.append(v)
        self.assertEqual(999, count)

        n = 2 ** 5000 - 1
        count = 0
        for v in divmod_iter(n, 2):
            count += 1
        self.assertEqual(5000, count)

    def test_divmod_iter_basic(self):
        v = divmod_iter_basic(1234, 10)
        self.assertEqual([4, 3, 2, 1], list(v))

    def test_basics(self):
        v = divmod_iter_chunking(1234, 10, 10)
        self.assertEqual([4, 3, 2, 1], list(v))

        v = divmod_iter_chunking(1234, 10, 100)
        self.assertEqual([4, 3, 2, 1], list(v))

        v = divmod_iter_chunking(1234, 10, 1000)
        self.assertEqual([4, 3, 2, 1], list(v))

    def test_bad_chunk_sizes(self):
        g = divmod_iter_chunking(1234, 10, 11)
        self.assertRaises(ValueError, lambda: next(g))

    def test_huge_number_1(self):
        v = divmod_iter_chunking(70110209207109374, 255)
        self.assertEqual([254, 254, 254, 254, 254, 254, 254], list(v))

    def test_huge_number_2(self):
        bignum = 1162523670191533212890624

        assert 255 ** 11 > bignum
        v = divmod_iter_chunking(bignum, 255, 255 ** 11)
        self.assertEqual(
            [254, 254, 254, 254, 254, 254, 254, 254, 254, 254], list(map(int, v))
        )

        assert 255 ** 9 < bignum
        v = divmod_iter_chunking(bignum, 255, 255 ** 9)
        self.assertEqual(
            [254, 254, 254, 254, 254, 254, 254, 254, 254, 254], list(map(int, v))
        )

    def test_huge_number_3(self):
        # this comes from '(?:[a-z]{,100}){,1000}'
        bignum = """
    139213503685244597631306906207129822718492493625765750638187
    422145221183403064209962632287600238213133585396115931858640
    397088297104215182062999160404977511404583694567955555693092
    391036971333019826503501322158903350288733318674828830355923
    498349990520184425817007399901916816311858669171276285561444
    611974044222858238401727502198428055979152449344112286300623
    398354626165755088011934430203904483146569680889715180212280
    311248065736587077721378474313074197745251681417858985013997
    376497357630123665969920348446238536919778668008199819062912
    209813948299604964182291901185954692403715976394605180757601
    560022975631875217270554188664960698779556224408710087910153
    388864065024676909905249179066904314719710199479087036266636
    486812383614637270104664243861433698340337270580924018081122
    972273102228069375608688078248241826230313720562480029591592
    545905659922877348183737039792218885258459176312595646776711
    788617588135808104772314342665930082373643028802685991791918
    926674139428325541968355964156198980323655477930065908769084
    934150892324757190759583195473467803980939672995083413559493
    917611589310185589660702265554321021096049823204800056794809
    973664250322419064982583391166478099231214825415574566705912
    248472806014274543228627658095513550473626381033015045051724
    852199012031842402809388416425577314128095191867797687492456
    679728567750494783710131249615739065586686514755989308471095
    118505256601463774083310772237026000
    """.replace(
            " ", ""
        ).replace(
            "\n", ""
        )
        bignum = int(bignum)
        bignum2 = 3268647867246256383381332100041691484373976788312974266629140102414955744756908184404049903032490380904202638084876187965749304595652472251350

        v = divmod_iter_chunking(bignum, bignum2)
        # there are at least 3 terms
        next(v)
        next(v)
        next(v)
        for i in v:
            pass
        # ...and it finishes

    def test_errors(self):
        with self.assertRaises(TypeError):
            divmod_iter("a", 1)
        with self.assertRaises(TypeError):
            divmod_iter(1, "a")
        with self.assertRaises(TypeError):
            divmod_iter(1, 1, "a")

    def test_divmod_iter_special_case(self):
        self.assertEqual([0], list(divmod_iter(0, 1)))
        with self.assertRaises(ValueError):
            list(divmod_iter(1, 1))

    @data_provider(
        [
            (num, base, chunk)
            for num in BIG_NUMBERS_1
            for base in (2, 10, 255, 256)
            for chunk in (base, base ** 2, base ** 3, base ** 4)
        ],
        test_limit=1601,
    )
    def test_correctness_big_numbers(self, num, base, chunk):
        self._runner(num, base, chunk)

    @data_provider(
        [
            (num, base, chunk)
            for num in BIG_NUMBERS_2
            for base in (2, 10, 255, 256)
            for chunk in (base, base ** 2, base ** 3, base ** 4)
        ]
    )
    def test_correctness_bigger_numbers(self, num, base, chunk):
        self._runner(num, base, chunk)

    def _runner(self, x, base, chunk):
        try:
            zip_longest = itertools.izip_longest
        except AttributeError:
            zip_longest = itertools.zip_longest
        for i, j in zip_longest(
            divmod_iter_chunking(x, base, chunk), divmod_iter_basic(x, base)
        ):
            if i is None:
                print("phooey")
                self.fail()
            else:
                self.assertEqual(i, j)

    @data_provider(
        [
            (base, low, high)
            for base in (1, 2, 7, 256)
            for low, high in ((0, 0), (1, 1), (1, 2), (1, 10), (99, 104),)
            # very slow, can include (1, 2 ** 14)
        ]
    )
    def test_powersum(self, base, low, high):
        expected = sum([base ** i for i in range(low, high + 1)])
        actual = powersum(base, low, high)
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
