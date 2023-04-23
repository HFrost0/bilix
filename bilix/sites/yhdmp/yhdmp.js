function __getplay_rev_data(_in_data) {
    if (_in_data.indexOf('{') < 0) {
        ;var encode_version = 'jsjiami.com.v5', unthu = '__0xb5aef',
            __0xb5aef = ['wohHHQdR', 'dyXDlMOIw5M=', 'dA9wwoRS', 'U8K2w7FvETZ9csKtEFTCjQ==', 'wo7ChVE=', 'VRrDhMOnw6I=', 'wr5LwoQkKBbDkcKwwqk='];
        (function (_0x22b97e, _0x2474ca) {
            var _0x5b074e = function (_0x5864d0) {
                while (--_0x5864d0) {
                    _0x22b97e['push'](_0x22b97e['shift']());
                }
            };
            _0x5b074e(++_0x2474ca);
        }(__0xb5aef, 0x1ae));
        var _0x2c0f = function (_0x19a33a, _0x9a1ebf) {
            _0x19a33a = _0x19a33a - 0x0;
            var _0x40a3ce = __0xb5aef[_0x19a33a];
            if (_0x2c0f['initialized'] === undefined) {
                (function () {
                    var _0x4d044c = typeof window !== 'undefined' ? window : typeof process === 'object' && typeof require === 'function' && typeof global === 'object' ? global : this;
                    var _0x1268d6 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=';
                    _0x4d044c['atob'] || (_0x4d044c['atob'] = function (_0x2993de) {
                        var _0x467e1d = String(_0x2993de)['replace'](/=+$/, '');
                        for (var _0x22a01d = 0x0, _0x1ee2a1, _0x2cf5ea, _0x3a84f7 = 0x0, _0x5c0e64 = ''; _0x2cf5ea = _0x467e1d['charAt'](_0x3a84f7++); ~_0x2cf5ea && (_0x1ee2a1 = _0x22a01d % 0x4 ? _0x1ee2a1 * 0x40 + _0x2cf5ea : _0x2cf5ea, _0x22a01d++ % 0x4) ? _0x5c0e64 += String['fromCharCode'](0xff & _0x1ee2a1 >> (-0x2 * _0x22a01d & 0x6)) : 0x0) {
                            _0x2cf5ea = _0x1268d6['indexOf'](_0x2cf5ea);
                        }
                        return _0x5c0e64;
                    });
                }());
                var _0x3c81da = function (_0x457f21, _0x6cb980) {
                    var _0x133a9b = [], _0x749ec5 = 0x0, _0x3ceeee, _0x1df5a4 = '', _0x35a2a6 = '';
                    _0x457f21 = atob(_0x457f21);
                    for (var _0x9a0e47 = 0x0, _0x4a71aa = _0x457f21['length']; _0x9a0e47 < _0x4a71aa; _0x9a0e47++) {
                        _0x35a2a6 += '%' + ('00' + _0x457f21['charCodeAt'](_0x9a0e47)['toString'](0x10))['slice'](-0x2);
                    }
                    _0x457f21 = decodeURIComponent(_0x35a2a6);
                    for (var _0x2ef02e = 0x0; _0x2ef02e < 0x100; _0x2ef02e++) {
                        _0x133a9b[_0x2ef02e] = _0x2ef02e;
                    }
                    for (_0x2ef02e = 0x0; _0x2ef02e < 0x100; _0x2ef02e++) {
                        _0x749ec5 = (_0x749ec5 + _0x133a9b[_0x2ef02e] + _0x6cb980['charCodeAt'](_0x2ef02e % _0x6cb980['length'])) % 0x100;
                        _0x3ceeee = _0x133a9b[_0x2ef02e];
                        _0x133a9b[_0x2ef02e] = _0x133a9b[_0x749ec5];
                        _0x133a9b[_0x749ec5] = _0x3ceeee;
                    }
                    _0x2ef02e = 0x0;
                    _0x749ec5 = 0x0;
                    for (var _0xa5d5ef = 0x0; _0xa5d5ef < _0x457f21['length']; _0xa5d5ef++) {
                        _0x2ef02e = (_0x2ef02e + 0x1) % 0x100;
                        _0x749ec5 = (_0x749ec5 + _0x133a9b[_0x2ef02e]) % 0x100;
                        _0x3ceeee = _0x133a9b[_0x2ef02e];
                        _0x133a9b[_0x2ef02e] = _0x133a9b[_0x749ec5];
                        _0x133a9b[_0x749ec5] = _0x3ceeee;
                        _0x1df5a4 += String['fromCharCode'](_0x457f21['charCodeAt'](_0xa5d5ef) ^ _0x133a9b[(_0x133a9b[_0x2ef02e] + _0x133a9b[_0x749ec5]) % 0x100]);
                    }
                    return _0x1df5a4;
                };
                _0x2c0f['rc4'] = _0x3c81da;
                _0x2c0f['data'] = {};
                _0x2c0f['initialized'] = !![];
            }
            var _0x4222af = _0x2c0f['data'][_0x19a33a];
            if (_0x4222af === undefined) {
                if (_0x2c0f['once'] === undefined) {
                    _0x2c0f['once'] = !![];
                }
                _0x40a3ce = _0x2c0f['rc4'](_0x40a3ce, _0x9a1ebf);
                _0x2c0f['data'][_0x19a33a] = _0x40a3ce;
            } else {
                _0x40a3ce = _0x4222af;
            }
            return _0x40a3ce;
        };
        var panurl = _in_data;
        var hf_panurl = '';
        const keyMP = 0x100000;
        const panurl_len = panurl['length'];
        for (var i = 0x0; i < panurl_len; i += 0x2) {
            var mn = parseInt(panurl[i] + panurl[i + 0x1], 0x10);
            mn = (mn + keyMP - (panurl_len / 0x2 - 0x1 - i / 0x2)) % 0x100;
            hf_panurl = String[_0x2c0f('0x0', '1JYE')](mn) + hf_panurl;
        }
        _in_data = hf_panurl;
        ;(function (_0x5be96b, _0x58d96a, _0x2d2c35) {
            var _0x13ecbc = {
                'luTaD': function _0x478551(_0x58d2f3, _0x3c17c5) {
                    return _0x58d2f3 !== _0x3c17c5;
                }, 'dkPfD': function _0x52a07f(_0x5999d5, _0x5de375) {
                    return _0x5999d5 === _0x5de375;
                }, 'NJDNu': function _0x386503(_0x39f385, _0x251b7b) {
                    return _0x39f385 + _0x251b7b;
                }, 'mNqKE': '版本号，js会定期弹窗，还请支持我们的工作', 'GllzR': '删除版本号，js会定期弹窗'
            };
            _0x2d2c35 = 'al';
            try {
                _0x2d2c35 += _0x2c0f('0x1', 's^Zc');
                _0x58d96a = encode_version;
                if (!(_0x13ecbc[_0x2c0f('0x2', '(fbB')](typeof _0x58d96a, _0x2c0f('0x3', '*OI!')) && _0x13ecbc[_0x2c0f('0x4', '8iw%')](_0x58d96a, 'jsjiami.com.v5'))) {
                    _0x5be96b[_0x2d2c35](_0x13ecbc[_0x2c0f('0x5', '(fbB')]('删除', _0x13ecbc['mNqKE']));
                }
            } catch (_0x57623d) {
                _0x5be96b[_0x2d2c35](_0x13ecbc[_0x2c0f('0x6', '126j')]);
            }
        }("undefined"));
        ;encode_version = 'jsjiami.com.v5';
    }
    return decodeURIComponent(_in_data);
}


function __getplay_pck() {
    ;var encode_version = 'sojson.v5', yqpcz = '__0x6d4a1',
        __0x6d4a1 = ['wq4mw7/CmF4=', 'w6XDrMOmwprCgg==', 'eRfDo8OoZQ==', 'IUnCmSzDgyfDjw==', 'S0pEJ8KxUMOSwqlq', 'asOow5tBwqk=', '5Lqc6ICk5Yi16ZuCw7A4wqEAwqHCisKHwr0/', 'TjpSwqZ3WMOmG8Oz', 'MhvDm8OOwqk=', 'XsKOwrAgwrFzwoU=', 'UyHCmcOyREsv', 'N2DDnXUC', 'BcOIwowrdgc=', 'GcOwNxbDqg==', 'JcKMw4ZORw==', 'Jm/ChVfDhw==', 'w7U3w4PCksKm', 'w7jDnHDCpcOF', 'wrgOw5PDlcO7', 'w4HDkMODYcK/D8O0PMKjShFZcw==', 'F8KFT8Ktwp3Ckw/CqXI=', 'M8O0dUFY', 'e1zDtMOGZg==', 'w6LChsKLCBo=', 'EMKJXSbDjQ==', 'T8KPWMK2wp3ChA==', 'wpRjw5BEZQ==', 'JHsWwq3DoQ==', 'HsKKUAvDqw==', 'wopnw5BzZA3DgQ==', 'wqAkw5PCpmw=', 'w68MBSvDow==', 'MljDsVQq', 'FMKIw6xETQ=='];
    (function (_0x3aee46, _0x59ba69) {
        var _0x3ea520 = function (_0x1dd9c6) {
            while (--_0x1dd9c6) {
                _0x3aee46['push'](_0x3aee46['shift']());
            }
        };
        _0x3ea520(++_0x59ba69);
    }(__0x6d4a1, 0x15b));
    var _0x15f5 = function (_0x36bc78, _0xbd2420) {
        _0x36bc78 = _0x36bc78 - 0x0;
        var _0xfd0a5f = __0x6d4a1[_0x36bc78];
        if (_0x15f5['initialized'] === undefined) {
            (function () {
                var _0x4b7bb1 = typeof window !== 'undefined' ? window : typeof process === 'object' && typeof require === 'function' && typeof global === 'object' ? global : this;
                var _0x531bb8 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=';
                _0x4b7bb1['atob'] || (_0x4b7bb1['atob'] = function (_0x1870ad) {
                    var _0x576c80 = String(_0x1870ad)['replace'](/=+$/, '');
                    for (var _0x44d56e = 0x0, _0x1a3ebb, _0x42d2dc, _0x1cf4b1 = 0x0, _0x2af9b7 = ''; _0x42d2dc = _0x576c80['charAt'](_0x1cf4b1++); ~_0x42d2dc && (_0x1a3ebb = _0x44d56e % 0x4 ? _0x1a3ebb * 0x40 + _0x42d2dc : _0x42d2dc, _0x44d56e++ % 0x4) ? _0x2af9b7 += String['fromCharCode'](0xff & _0x1a3ebb >> (-0x2 * _0x44d56e & 0x6)) : 0x0) {
                        _0x42d2dc = _0x531bb8['indexOf'](_0x42d2dc);
                    }
                    return _0x2af9b7;
                });
            }());
            var _0x1897b8 = function (_0x3c0b9b, _0x2579f3) {
                var _0x5a0327 = [], _0x330679 = 0x0, _0x12b19f, _0x3ebfbf = '', _0x20630f = '';
                _0x3c0b9b = atob(_0x3c0b9b);
                for (var _0x514228 = 0x0, _0x4f7f74 = _0x3c0b9b['length']; _0x514228 < _0x4f7f74; _0x514228++) {
                    _0x20630f += '%' + ('00' + _0x3c0b9b['charCodeAt'](_0x514228)['toString'](0x10))['slice'](-0x2);
                }
                _0x3c0b9b = decodeURIComponent(_0x20630f);
                for (var _0x53cc80 = 0x0; _0x53cc80 < 0x100; _0x53cc80++) {
                    _0x5a0327[_0x53cc80] = _0x53cc80;
                }
                for (_0x53cc80 = 0x0; _0x53cc80 < 0x100; _0x53cc80++) {
                    _0x330679 = (_0x330679 + _0x5a0327[_0x53cc80] + _0x2579f3['charCodeAt'](_0x53cc80 % _0x2579f3['length'])) % 0x100;
                    _0x12b19f = _0x5a0327[_0x53cc80];
                    _0x5a0327[_0x53cc80] = _0x5a0327[_0x330679];
                    _0x5a0327[_0x330679] = _0x12b19f;
                }
                _0x53cc80 = 0x0;
                _0x330679 = 0x0;
                for (var _0x25c772 = 0x0; _0x25c772 < _0x3c0b9b['length']; _0x25c772++) {
                    _0x53cc80 = (_0x53cc80 + 0x1) % 0x100;
                    _0x330679 = (_0x330679 + _0x5a0327[_0x53cc80]) % 0x100;
                    _0x12b19f = _0x5a0327[_0x53cc80];
                    _0x5a0327[_0x53cc80] = _0x5a0327[_0x330679];
                    _0x5a0327[_0x330679] = _0x12b19f;
                    _0x3ebfbf += String['fromCharCode'](_0x3c0b9b['charCodeAt'](_0x25c772) ^ _0x5a0327[(_0x5a0327[_0x53cc80] + _0x5a0327[_0x330679]) % 0x100]);
                }
                return _0x3ebfbf;
            };
            _0x15f5['rc4'] = _0x1897b8;
            _0x15f5['data'] = {};
            _0x15f5['initialized'] = !![];
        }
        var _0x597ef6 = _0x15f5['data'][_0x36bc78];
        if (_0x597ef6 === undefined) {
            if (_0x15f5['once'] === undefined) {
                _0x15f5['once'] = !![];
            }
            _0xfd0a5f = _0x15f5['rc4'](_0xfd0a5f, _0xbd2420);
            _0x15f5['data'][_0x36bc78] = _0xfd0a5f;
        } else {
            _0xfd0a5f = _0x597ef6;
        }
        return _0xfd0a5f;
    };
    if (!![]) {
        var _0x36d031 = _0x15f5('0x0', 'CuZW')[_0x15f5('0x1', '^Ou5')]('|'), _0x5a77e0 = 0x0;
        while (!![]) {
            switch (_0x36d031[_0x5a77e0++]) {
                case'0':
                    f2 = function (_0x369589, _0x22305e) {
                        var _0x3df411 = {
                            'DUWem': function _0x172fb9(_0x5ec61c, _0x564208) {
                                return _0x5ec61c + _0x564208;
                            }, 'chgqL': function _0xdabcda(_0x221552, _0x9f16bb) {
                                return _0x221552 * _0x9f16bb;
                            }, 'ueYPD': function _0x42de89(_0x168663, _0x45775b) {
                                return _0x168663 + _0x45775b;
                            }, 'FyVON': function _0x132543(_0x14cf95, _0x5f0613) {
                                return _0x14cf95 + _0x5f0613;
                            }, 'rImkg': function _0x3ee8de(_0x50917a, _0x5aa05b) {
                                return _0x50917a + _0x5aa05b;
                            }, 'EhXgt': ';expires=', 'eglgt': _0x15f5('0x2', 'y4Vs')
                        };
                        var _0x355c8f = 0x1e;
                        var _0x36f590 = new Date();
                        _0x36f590['setTime'](_0x3df411['DUWem'](_0x36f590[_0x15f5('0x3', 'wmgi')](), _0x3df411[_0x15f5('0x4', 'Put*')](_0x3df411['chgqL'](_0x3df411['chgqL'](_0x355c8f, 0x18), 0x3c) * 0x3c, 0x3e8)));
                        var cookie = _0x3df411['DUWem'](_0x3df411[_0x15f5('0x6', 'PIK)')](_0x3df411['FyVON'](_0x3df411['rImkg'](_0x3df411[_0x15f5('0x7', 'MDzc')](_0x369589, '='), escape(_0x22305e)), _0x3df411[_0x15f5('0x8', 'bDPL')]), _0x36f590['toGMTString']()), _0x3df411[_0x15f5('0x9', 'Doro')])
                        updateDoc(cookie)
                    };
                    continue;
                case'1':
                    t1 = Math[_0x15f5('0xa', 'Q5gT')](Number(f('t1')) / 0x3e8) >> 0x5;
                    continue;
                case'2':
                    f = function (_0x30755b) {
                        var _0x2061a3 = {
                            'JwcjB': function _0x4d63cc(_0x53138c, _0x57679f) {
                                return _0x53138c + _0x57679f;
                            },
                            'zWwUP': _0x15f5('0xb', 'Doro'),
                            'zMNwJ': _0x15f5('0xc', 'mu(g'),
                            'QLLCz': function _0xcf9e5b(_0x22b423, _0x4bb2df) {
                                return _0x22b423(_0x4bb2df);
                            },
                            'tNCZl': 'BSp',
                            'fPKPd': function _0x1e8a5f(_0x1b5aa9, _0x4db818) {
                                return _0x1b5aa9 + _0x4db818;
                            },
                            'BbKyG': function _0x1758f2(_0x471863, _0x128f5e) {
                                return _0x471863 * _0x128f5e;
                            },
                            'xIvIx': function _0x25258e(_0xf7b32b, _0x717bc1) {
                                return _0xf7b32b * _0x717bc1;
                            },
                            'CMGam': function _0x5cb526(_0x32dc57, _0x589dad) {
                                return _0x32dc57 + _0x589dad;
                            },
                            'hRgnV': function _0x30a4e5(_0x401fb4, _0x49024c) {
                                return _0x401fb4 + _0x49024c;
                            },
                            'QNctg': _0x15f5('0xd', 'KvKZ')
                        };
                        var _0x583897,
                            _0x3a66ce = new RegExp(_0x2061a3[_0x15f5('0xe', 'Ox#l')](_0x2061a3[_0x15f5('0xf', 'v78#')](_0x2061a3[_0x15f5('0x10', '7jQL')], _0x30755b), _0x2061a3[_0x15f5('0x11', '6O7p')]));
                        if (_0x583897 = document[_0x15f5('0x12', 'KvKZ')][_0x15f5('0x13', 'Z@&Q')](_0x3a66ce)) {
                            return _0x2061a3[_0x15f5('0x14', 'g#CQ')](unescape, _0x583897[0x2]);
                        } else {
                            if (_0x2061a3['tNCZl'] !== _0x2061a3[_0x15f5('0x15', '6O7p')]) {
                                var _0x2856c4 = 0x1e;
                                var _0x412bd3 = new Date();
                                _0x412bd3[_0x15f5('0x16', 'Z@&Q')](_0x2061a3[_0x15f5('0x17', '0USv')](_0x412bd3['getTime'](), _0x2061a3['BbKyG'](_0x2061a3[_0x15f5('0x18', 'x]l]')](_0x2856c4, 0x18) * 0x3c * 0x3c, 0x3e8)));
                                var key = _0x2061a3[_0x15f5('0x19', 'Put*')](_0x2061a3['fPKPd'](_0x2061a3[_0x15f5('0x1a', 'MDzc')](_0x2061a3[_0x15f5('0x1b', '0USv')](_0x30755b + '=', _0x2061a3[_0x15f5('0x1c', 'd$Fs')](escape, value)), _0x2061a3[_0x15f5('0x1d', 's1ve')]), _0x412bd3['toGMTString']()), ';path=/')
                                updateDoc(key)
                            } else {
                                return null;
                            }
                        }
                    };
                    continue;
                case'3':
                    f2('t2', new Date()[_0x15f5('0x1e', '9k4F')]());
                    continue;
                case'4':
                    f2('k2', (t1 * (t1 % 0x1000) + 0x99d6) * (t1 % 0x1000) + t1);
                    continue;
            }
            break;
        }
    }
    ;
    if (!(typeof encode_version !== 'undefined' && encode_version === _0x15f5('0x1f', 'wZ(I'))) {
        window[_0x15f5('0x20', 'KbZ5')](_0x15f5('0x21', 'YAu4'));
    }
    ;encode_version = 'sojson.v5';
}


function __getplay_pck2() {
    ;var encode_version = 'sojson.v5', woaew = '__0x6d4a2',
        __0x6d4a2 = ['w4TCkxtLwofCuBE=', 'YsKYwok/w5M=', 'DWwZJDPDksOi', 'wocjwrkSXQ==', 'XG5tw6Y2', 'OMOpSErDhw==', 'AA7DksO/w4gM', 'w5prw6vCrFI=', 'w7U3L8K1bQ==', 'Z8K5wrJIwrE=', 'L8OKZcKaGcOoTcOUwqIFYw==', 'YCPDs1bDrQPDvg==', 'dcOrVsOlwoA=', 'OcORb2nDtg==', 'FcKQdxtY', 'dsKSQz8V', 'McKZVzd2Xg==', 'VyEpUy4=', 'ASUlQC97HGdz', 'wqzDryzCjMKSWAE='];
    (function (_0x57c88f, _0x2383d8) {
        var _0x4b2391 = function (_0x58c926) {
            while (--_0x58c926) {
                _0x57c88f['push'](_0x57c88f['shift']());
            }
        };
        _0x4b2391(++_0x2383d8);
    }(__0x6d4a2, 0xad));
    var _0x1691 = function (_0x3c08d1, _0xc096f) {
        _0x3c08d1 = _0x3c08d1 - 0x0;
        var _0x2babb8 = __0x6d4a2[_0x3c08d1];
        if (_0x1691['initialized'] === undefined) {
            (function () {
                var _0x2f1e69 = typeof window !== 'undefined' ? window : typeof process === 'object' && typeof require === 'function' && typeof global === 'object' ? global : this;
                var _0x4f603c = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=';
                _0x2f1e69['atob'] || (_0x2f1e69['atob'] = function (_0x2c68bb) {
                    var _0x492998 = String(_0x2c68bb)['replace'](/=+$/, '');
                    for (var _0x5ee61a = 0x0, _0x2ac634, _0x1d1013, _0x6f4d80 = 0x0, _0x4a006d = ''; _0x1d1013 = _0x492998['charAt'](_0x6f4d80++); ~_0x1d1013 && (_0x2ac634 = _0x5ee61a % 0x4 ? _0x2ac634 * 0x40 + _0x1d1013 : _0x1d1013, _0x5ee61a++ % 0x4) ? _0x4a006d += String['fromCharCode'](0xff & _0x2ac634 >> (-0x2 * _0x5ee61a & 0x6)) : 0x0) {
                        _0x1d1013 = _0x4f603c['indexOf'](_0x1d1013);
                    }
                    return _0x4a006d;
                });
            }());
            var _0xa0b1f0 = function (_0x2fa32b, _0x4608dc) {
                var _0x4f2019 = [], _0x4a28e8 = 0x0, _0x19767d, _0x4cf800 = '', _0x4bb512 = '';
                _0x2fa32b = atob(_0x2fa32b);
                for (var _0x36c759 = 0x0, _0x20d6ad = _0x2fa32b['length']; _0x36c759 < _0x20d6ad; _0x36c759++) {
                    _0x4bb512 += '%' + ('00' + _0x2fa32b['charCodeAt'](_0x36c759)['toString'](0x10))['slice'](-0x2);
                }
                _0x2fa32b = decodeURIComponent(_0x4bb512);
                for (var _0x3ac32b = 0x0; _0x3ac32b < 0x100; _0x3ac32b++) {
                    _0x4f2019[_0x3ac32b] = _0x3ac32b;
                }
                for (_0x3ac32b = 0x0; _0x3ac32b < 0x100; _0x3ac32b++) {
                    _0x4a28e8 = (_0x4a28e8 + _0x4f2019[_0x3ac32b] + _0x4608dc['charCodeAt'](_0x3ac32b % _0x4608dc['length'])) % 0x100;
                    _0x19767d = _0x4f2019[_0x3ac32b];
                    _0x4f2019[_0x3ac32b] = _0x4f2019[_0x4a28e8];
                    _0x4f2019[_0x4a28e8] = _0x19767d;
                }
                _0x3ac32b = 0x0;
                _0x4a28e8 = 0x0;
                for (var _0x3b73f2 = 0x0; _0x3b73f2 < _0x2fa32b['length']; _0x3b73f2++) {
                    _0x3ac32b = (_0x3ac32b + 0x1) % 0x100;
                    _0x4a28e8 = (_0x4a28e8 + _0x4f2019[_0x3ac32b]) % 0x100;
                    _0x19767d = _0x4f2019[_0x3ac32b];
                    _0x4f2019[_0x3ac32b] = _0x4f2019[_0x4a28e8];
                    _0x4f2019[_0x4a28e8] = _0x19767d;
                    _0x4cf800 += String['fromCharCode'](_0x2fa32b['charCodeAt'](_0x3b73f2) ^ _0x4f2019[(_0x4f2019[_0x3ac32b] + _0x4f2019[_0x4a28e8]) % 0x100]);
                }
                return _0x4cf800;
            };
            _0x1691['rc4'] = _0xa0b1f0;
            _0x1691['data'] = {};
            _0x1691['initialized'] = !![];
        }
        var _0x4cce77 = _0x1691['data'][_0x3c08d1];
        if (_0x4cce77 === undefined) {
            if (_0x1691['once'] === undefined) {
                _0x1691['once'] = !![];
            }
            _0x2babb8 = _0x1691['rc4'](_0x2babb8, _0xc096f);
            _0x1691['data'][_0x3c08d1] = _0x2babb8;
        } else {
            _0x2babb8 = _0x4cce77;
        }
        return _0x2babb8;
    };
    if (!![]) {
        f = function (_0x1d75de) {
            var _0x37083b = {
                'QPnEZ': function _0x60d408(_0x47b907, _0x1e139b) {
                    return _0x47b907 + _0x1e139b;
                }, 'GfOGG': function _0x3d3c72(_0x1f55be, _0x4a6029) {
                    return _0x1f55be + _0x4a6029;
                }, 'HMzQD': '=([^;]*)(;|$)'
            };
            var _0x4d0811,
                _0x524d79 = new RegExp(_0x37083b[_0x1691('0x0', 'H$R$')](_0x37083b[_0x1691('0x1', '@5Y)')]('(^|\x20)', _0x1d75de), _0x37083b[_0x1691('0x2', '&6Xe')]));
            if (_0x4d0811 = document[_0x1691('0x3', '@5Y)')][_0x1691('0x4', 'wcel')](_0x524d79)) {
                return unescape(_0x4d0811[0x2]);
            } else {
                return null;
            }
        };
        f2 = function (_0x5059ad, _0x4d7bb0) {
            var _0x372740 = {
                'wGmSQ': function _0x495870(_0x1e22e5, _0x5a96b1) {
                    return _0x1e22e5 + _0x5a96b1;
                }, 'zPYil': function _0x53f643(_0x30ccee, _0x194f17) {
                    return _0x30ccee * _0x194f17;
                }, 'PhIfk': function _0x5a75c7(_0x5ebe8a, _0x59b8e9) {
                    return _0x5ebe8a * _0x59b8e9;
                }, 'HidQG': function _0x579a67(_0x374d40, _0x1e0498) {
                    return _0x374d40 + _0x1e0498;
                }, 'bUfLy': function _0xd9d4c3(_0x490eda, _0xb0910e) {
                    return _0x490eda(_0xb0910e);
                }, 'DYZHd': _0x1691('0x5', 'wcel'), 'cDGyM': _0x1691('0x6', 'mI%7')
            };
            var _0x2d5246 = 0x1e;
            var _0x11d22b = new Date();
            _0x11d22b[_0x1691('0x7', 'V55E')](_0x372740[_0x1691('0x8', 'cvmk')](_0x11d22b[_0x1691('0x9', '2v0z')](), _0x372740[_0x1691('0xa', ']ZR@')](_0x372740[_0x1691('0xb', 'hPNq')](_0x372740[_0x1691('0xc', 'H$R$')](_0x372740['PhIfk'](_0x2d5246, 0x18), 0x3c), 0x3c), 0x3e8)));
            var key = _0x372740['HidQG'](_0x372740[_0x1691('0xe', ']o&s')](_0x372740[_0x1691('0xf', 'd%V$')](_0x5059ad, '='), _0x372740['bUfLy'](escape, _0x4d7bb0)), _0x372740[_0x1691('0x10', 'nG4r')]) + _0x11d22b[_0x1691('0x11', 'U8Zj')]() + _0x372740['cDGyM']
            updateDoc(key)
            // document[_0x1691('0xd', 'h%Wr')] = _0x372740['HidQG'](_0x372740[_0x1691('0xe', ']o&s')](_0x372740[_0x1691('0xf', 'd%V$')](_0x5059ad, '='), _0x372740['bUfLy'](escape, _0x4d7bb0)), _0x372740[_0x1691('0x10', 'nG4r')]) + _0x11d22b[_0x1691('0x11', 'U8Zj')]() + _0x372740['cDGyM'];
        };
        try {
            ksub = f('k2')['slice'](-0x1);
            while (!![]) {
                t2 = new Date()['getTime']();
                if (t2['toString']()['slice'](-0x3)[_0x1691('0x12', '9f@X')](ksub) >= 0x0) {
                    f2('t2', t2);
                    break;
                }
            }
        } catch (_0x5e3bb4) {
        }
    }
    ;
    if (!(typeof encode_version !== 'undefined' && encode_version === 'sojson.v5')) {
        window[_0x1691('0x13', 'EPWy')]('不能删除sojson.v5');
    }
    ;encode_version = 'sojson.v5';
}

let document = {data: {}}

function updateDoc(cookie) {
    cookie = cookie.split(';')[0]
    let a = cookie.split("=")
    document.data[a[0]] = a[1]
    let tmp = []
    for (const key in document.data) {
        tmp.push(`${key}=${document.data[key]}`)
    }
    document.cookie = tmp.join('; ')
}

function get_t2_k2(t1, k1) {
    updateDoc(`t1=${t1}`)
    updateDoc(`k1=${k1}`)
    __getplay_pck();
    __getplay_pck2();
    return {t2: document.data.t2, k2: document.data.k2}
}

// console.logger(get_data(1660410066753, 54244870492));

