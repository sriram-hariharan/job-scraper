//#region \0rolldown/runtime.js
var e = Object.create, t = Object.defineProperty, n = Object.getOwnPropertyDescriptor, r = Object.getOwnPropertyNames, i = Object.getPrototypeOf, a = Object.prototype.hasOwnProperty, o = (e, t) => () => (t || (e((t = { exports: {} }).exports, t), e = null), t.exports), s = (e, n) => {
	let r = {};
	for (var i in e) t(r, i, {
		get: e[i],
		enumerable: !0
	});
	return n || t(r, Symbol.toStringTag, { value: "Module" }), r;
}, c = (e, i, o, s) => {
	if (i && typeof i == "object" || typeof i == "function") for (var c = r(i), l = 0, u = c.length, d; l < u; l++) d = c[l], !a.call(e, d) && d !== o && t(e, d, {
		get: ((e) => i[e]).bind(null, d),
		enumerable: !(s = n(i, d)) || s.enumerable
	});
	return e;
}, l = (n, r, a) => (a = n == null ? {} : e(i(n)), c(r || !n || !n.__esModule ? t(a, "default", {
	value: n,
	enumerable: !0
}) : a, n)), u = /* @__PURE__ */ o(((e) => {
	var t = Symbol.for("react.element"), n = Symbol.for("react.portal"), r = Symbol.for("react.fragment"), i = Symbol.for("react.strict_mode"), a = Symbol.for("react.profiler"), o = Symbol.for("react.provider"), s = Symbol.for("react.context"), c = Symbol.for("react.forward_ref"), l = Symbol.for("react.suspense"), u = Symbol.for("react.memo"), d = Symbol.for("react.lazy"), f = Symbol.iterator;
	function p(e) {
		return typeof e != "object" || !e ? null : (e = f && e[f] || e["@@iterator"], typeof e == "function" ? e : null);
	}
	var m = {
		isMounted: function() {
			return !1;
		},
		enqueueForceUpdate: function() {},
		enqueueReplaceState: function() {},
		enqueueSetState: function() {}
	}, h = Object.assign, g = {};
	function _(e, t, n) {
		this.props = e, this.context = t, this.refs = g, this.updater = n || m;
	}
	_.prototype.isReactComponent = {}, _.prototype.setState = function(e, t) {
		if (typeof e != "object" && typeof e != "function" && e != null) throw Error("setState(...): takes an object of state variables to update or a function which returns an object of state variables.");
		this.updater.enqueueSetState(this, e, t, "setState");
	}, _.prototype.forceUpdate = function(e) {
		this.updater.enqueueForceUpdate(this, e, "forceUpdate");
	};
	function v() {}
	v.prototype = _.prototype;
	function y(e, t, n) {
		this.props = e, this.context = t, this.refs = g, this.updater = n || m;
	}
	var b = y.prototype = new v();
	b.constructor = y, h(b, _.prototype), b.isPureReactComponent = !0;
	var x = Array.isArray, S = Object.prototype.hasOwnProperty, C = { current: null }, w = {
		key: !0,
		ref: !0,
		__self: !0,
		__source: !0
	};
	function T(e, n, r) {
		var i, a = {}, o = null, s = null;
		if (n != null) for (i in n.ref !== void 0 && (s = n.ref), n.key !== void 0 && (o = "" + n.key), n) S.call(n, i) && !w.hasOwnProperty(i) && (a[i] = n[i]);
		var c = arguments.length - 2;
		if (c === 1) a.children = r;
		else if (1 < c) {
			for (var l = Array(c), u = 0; u < c; u++) l[u] = arguments[u + 2];
			a.children = l;
		}
		if (e && e.defaultProps) for (i in c = e.defaultProps, c) a[i] === void 0 && (a[i] = c[i]);
		return {
			$$typeof: t,
			type: e,
			key: o,
			ref: s,
			props: a,
			_owner: C.current
		};
	}
	function E(e, n) {
		return {
			$$typeof: t,
			type: e.type,
			key: n,
			ref: e.ref,
			props: e.props,
			_owner: e._owner
		};
	}
	function D(e) {
		return typeof e == "object" && !!e && e.$$typeof === t;
	}
	function O(e) {
		var t = {
			"=": "=0",
			":": "=2"
		};
		return "$" + e.replace(/[=:]/g, function(e) {
			return t[e];
		});
	}
	var k = /\/+/g;
	function A(e, t) {
		return typeof e == "object" && e && e.key != null ? O("" + e.key) : t.toString(36);
	}
	function j(e, r, i, a, o) {
		var s = typeof e;
		(s === "undefined" || s === "boolean") && (e = null);
		var c = !1;
		if (e === null) c = !0;
		else switch (s) {
			case "string":
			case "number":
				c = !0;
				break;
			case "object": switch (e.$$typeof) {
				case t:
				case n: c = !0;
			}
		}
		if (c) return c = e, o = o(c), e = a === "" ? "." + A(c, 0) : a, x(o) ? (i = "", e != null && (i = e.replace(k, "$&/") + "/"), j(o, r, i, "", function(e) {
			return e;
		})) : o != null && (D(o) && (o = E(o, i + (!o.key || c && c.key === o.key ? "" : ("" + o.key).replace(k, "$&/") + "/") + e)), r.push(o)), 1;
		if (c = 0, a = a === "" ? "." : a + ":", x(e)) for (var l = 0; l < e.length; l++) {
			s = e[l];
			var u = a + A(s, l);
			c += j(s, r, i, u, o);
		}
		else if (u = p(e), typeof u == "function") for (e = u.call(e), l = 0; !(s = e.next()).done;) s = s.value, u = a + A(s, l++), c += j(s, r, i, u, o);
		else if (s === "object") throw r = String(e), Error("Objects are not valid as a React child (found: " + (r === "[object Object]" ? "object with keys {" + Object.keys(e).join(", ") + "}" : r) + "). If you meant to render a collection of children, use an array instead.");
		return c;
	}
	function M(e, t, n) {
		if (e == null) return e;
		var r = [], i = 0;
		return j(e, r, "", "", function(e) {
			return t.call(n, e, i++);
		}), r;
	}
	function N(e) {
		if (e._status === -1) {
			var t = e._result;
			t = t(), t.then(function(t) {
				(e._status === 0 || e._status === -1) && (e._status = 1, e._result = t);
			}, function(t) {
				(e._status === 0 || e._status === -1) && (e._status = 2, e._result = t);
			}), e._status === -1 && (e._status = 0, e._result = t);
		}
		if (e._status === 1) return e._result.default;
		throw e._result;
	}
	var P = { current: null }, ee = { transition: null }, te = {
		ReactCurrentDispatcher: P,
		ReactCurrentBatchConfig: ee,
		ReactCurrentOwner: C
	};
	function ne() {
		throw Error("act(...) is not supported in production builds of React.");
	}
	e.Children = {
		map: M,
		forEach: function(e, t, n) {
			M(e, function() {
				t.apply(this, arguments);
			}, n);
		},
		count: function(e) {
			var t = 0;
			return M(e, function() {
				t++;
			}), t;
		},
		toArray: function(e) {
			return M(e, function(e) {
				return e;
			}) || [];
		},
		only: function(e) {
			if (!D(e)) throw Error("React.Children.only expected to receive a single React element child.");
			return e;
		}
	}, e.Component = _, e.Fragment = r, e.Profiler = a, e.PureComponent = y, e.StrictMode = i, e.Suspense = l, e.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED = te, e.act = ne, e.cloneElement = function(e, n, r) {
		if (e == null) throw Error("React.cloneElement(...): The argument must be a React element, but you passed " + e + ".");
		var i = h({}, e.props), a = e.key, o = e.ref, s = e._owner;
		if (n != null) {
			if (n.ref !== void 0 && (o = n.ref, s = C.current), n.key !== void 0 && (a = "" + n.key), e.type && e.type.defaultProps) var c = e.type.defaultProps;
			for (l in n) S.call(n, l) && !w.hasOwnProperty(l) && (i[l] = n[l] === void 0 && c !== void 0 ? c[l] : n[l]);
		}
		var l = arguments.length - 2;
		if (l === 1) i.children = r;
		else if (1 < l) {
			c = Array(l);
			for (var u = 0; u < l; u++) c[u] = arguments[u + 2];
			i.children = c;
		}
		return {
			$$typeof: t,
			type: e.type,
			key: a,
			ref: o,
			props: i,
			_owner: s
		};
	}, e.createContext = function(e) {
		return e = {
			$$typeof: s,
			_currentValue: e,
			_currentValue2: e,
			_threadCount: 0,
			Provider: null,
			Consumer: null,
			_defaultValue: null,
			_globalName: null
		}, e.Provider = {
			$$typeof: o,
			_context: e
		}, e.Consumer = e;
	}, e.createElement = T, e.createFactory = function(e) {
		var t = T.bind(null, e);
		return t.type = e, t;
	}, e.createRef = function() {
		return { current: null };
	}, e.forwardRef = function(e) {
		return {
			$$typeof: c,
			render: e
		};
	}, e.isValidElement = D, e.lazy = function(e) {
		return {
			$$typeof: d,
			_payload: {
				_status: -1,
				_result: e
			},
			_init: N
		};
	}, e.memo = function(e, t) {
		return {
			$$typeof: u,
			type: e,
			compare: t === void 0 ? null : t
		};
	}, e.startTransition = function(e) {
		var t = ee.transition;
		ee.transition = {};
		try {
			e();
		} finally {
			ee.transition = t;
		}
	}, e.unstable_act = ne, e.useCallback = function(e, t) {
		return P.current.useCallback(e, t);
	}, e.useContext = function(e) {
		return P.current.useContext(e);
	}, e.useDebugValue = function() {}, e.useDeferredValue = function(e) {
		return P.current.useDeferredValue(e);
	}, e.useEffect = function(e, t) {
		return P.current.useEffect(e, t);
	}, e.useId = function() {
		return P.current.useId();
	}, e.useImperativeHandle = function(e, t, n) {
		return P.current.useImperativeHandle(e, t, n);
	}, e.useInsertionEffect = function(e, t) {
		return P.current.useInsertionEffect(e, t);
	}, e.useLayoutEffect = function(e, t) {
		return P.current.useLayoutEffect(e, t);
	}, e.useMemo = function(e, t) {
		return P.current.useMemo(e, t);
	}, e.useReducer = function(e, t, n) {
		return P.current.useReducer(e, t, n);
	}, e.useRef = function(e) {
		return P.current.useRef(e);
	}, e.useState = function(e) {
		return P.current.useState(e);
	}, e.useSyncExternalStore = function(e, t, n) {
		return P.current.useSyncExternalStore(e, t, n);
	}, e.useTransition = function() {
		return P.current.useTransition();
	}, e.version = "18.3.1";
})), d = /* @__PURE__ */ o(((e, t) => {
	t.exports = u();
})), f = /* @__PURE__ */ o(((e) => {
	function t(e, t) {
		var n = e.length;
		e.push(t);
		a: for (; 0 < n;) {
			var r = n - 1 >>> 1, a = e[r];
			if (0 < i(a, t)) e[r] = t, e[n] = a, n = r;
			else break a;
		}
	}
	function n(e) {
		return e.length === 0 ? null : e[0];
	}
	function r(e) {
		if (e.length === 0) return null;
		var t = e[0], n = e.pop();
		if (n !== t) {
			e[0] = n;
			a: for (var r = 0, a = e.length, o = a >>> 1; r < o;) {
				var s = 2 * (r + 1) - 1, c = e[s], l = s + 1, u = e[l];
				if (0 > i(c, n)) l < a && 0 > i(u, c) ? (e[r] = u, e[l] = n, r = l) : (e[r] = c, e[s] = n, r = s);
				else if (l < a && 0 > i(u, n)) e[r] = u, e[l] = n, r = l;
				else break a;
			}
		}
		return t;
	}
	function i(e, t) {
		var n = e.sortIndex - t.sortIndex;
		return n === 0 ? e.id - t.id : n;
	}
	if (typeof performance == "object" && typeof performance.now == "function") {
		var a = performance;
		e.unstable_now = function() {
			return a.now();
		};
	} else {
		var o = Date, s = o.now();
		e.unstable_now = function() {
			return o.now() - s;
		};
	}
	var c = [], l = [], u = 1, d = null, f = 3, p = !1, m = !1, h = !1, g = typeof setTimeout == "function" ? setTimeout : null, _ = typeof clearTimeout == "function" ? clearTimeout : null, v = typeof setImmediate < "u" ? setImmediate : null;
	typeof navigator < "u" && navigator.scheduling !== void 0 && navigator.scheduling.isInputPending !== void 0 && navigator.scheduling.isInputPending.bind(navigator.scheduling);
	function y(e) {
		for (var i = n(l); i !== null;) {
			if (i.callback === null) r(l);
			else if (i.startTime <= e) r(l), i.sortIndex = i.expirationTime, t(c, i);
			else break;
			i = n(l);
		}
	}
	function b(e) {
		if (h = !1, y(e), !m) if (n(c) !== null) m = !0, M(x);
		else {
			var t = n(l);
			t !== null && N(b, t.startTime - e);
		}
	}
	function x(t, i) {
		m = !1, h && (h = !1, _(w), w = -1), p = !0;
		var a = f;
		try {
			for (y(i), d = n(c); d !== null && (!(d.expirationTime > i) || t && !D());) {
				var o = d.callback;
				if (typeof o == "function") {
					d.callback = null, f = d.priorityLevel;
					var s = o(d.expirationTime <= i);
					i = e.unstable_now(), typeof s == "function" ? d.callback = s : d === n(c) && r(c), y(i);
				} else r(c);
				d = n(c);
			}
			if (d !== null) var u = !0;
			else {
				var g = n(l);
				g !== null && N(b, g.startTime - i), u = !1;
			}
			return u;
		} finally {
			d = null, f = a, p = !1;
		}
	}
	var S = !1, C = null, w = -1, T = 5, E = -1;
	function D() {
		return !(e.unstable_now() - E < T);
	}
	function O() {
		if (C !== null) {
			var t = e.unstable_now();
			E = t;
			var n = !0;
			try {
				n = C(!0, t);
			} finally {
				n ? k() : (S = !1, C = null);
			}
		} else S = !1;
	}
	var k;
	if (typeof v == "function") k = function() {
		v(O);
	};
	else if (typeof MessageChannel < "u") {
		var A = new MessageChannel(), j = A.port2;
		A.port1.onmessage = O, k = function() {
			j.postMessage(null);
		};
	} else k = function() {
		g(O, 0);
	};
	function M(e) {
		C = e, S || (S = !0, k());
	}
	function N(t, n) {
		w = g(function() {
			t(e.unstable_now());
		}, n);
	}
	e.unstable_IdlePriority = 5, e.unstable_ImmediatePriority = 1, e.unstable_LowPriority = 4, e.unstable_NormalPriority = 3, e.unstable_Profiling = null, e.unstable_UserBlockingPriority = 2, e.unstable_cancelCallback = function(e) {
		e.callback = null;
	}, e.unstable_continueExecution = function() {
		m || p || (m = !0, M(x));
	}, e.unstable_forceFrameRate = function(e) {
		0 > e || 125 < e ? console.error("forceFrameRate takes a positive int between 0 and 125, forcing frame rates higher than 125 fps is not supported") : T = 0 < e ? Math.floor(1e3 / e) : 5;
	}, e.unstable_getCurrentPriorityLevel = function() {
		return f;
	}, e.unstable_getFirstCallbackNode = function() {
		return n(c);
	}, e.unstable_next = function(e) {
		switch (f) {
			case 1:
			case 2:
			case 3:
				var t = 3;
				break;
			default: t = f;
		}
		var n = f;
		f = t;
		try {
			return e();
		} finally {
			f = n;
		}
	}, e.unstable_pauseExecution = function() {}, e.unstable_requestPaint = function() {}, e.unstable_runWithPriority = function(e, t) {
		switch (e) {
			case 1:
			case 2:
			case 3:
			case 4:
			case 5: break;
			default: e = 3;
		}
		var n = f;
		f = e;
		try {
			return t();
		} finally {
			f = n;
		}
	}, e.unstable_scheduleCallback = function(r, i, a) {
		var o = e.unstable_now();
		switch (typeof a == "object" && a ? (a = a.delay, a = typeof a == "number" && 0 < a ? o + a : o) : a = o, r) {
			case 1:
				var s = -1;
				break;
			case 2:
				s = 250;
				break;
			case 5:
				s = 1073741823;
				break;
			case 4:
				s = 1e4;
				break;
			default: s = 5e3;
		}
		return s = a + s, r = {
			id: u++,
			callback: i,
			priorityLevel: r,
			startTime: a,
			expirationTime: s,
			sortIndex: -1
		}, a > o ? (r.sortIndex = a, t(l, r), n(c) === null && r === n(l) && (h ? (_(w), w = -1) : h = !0, N(b, a - o))) : (r.sortIndex = s, t(c, r), m || p || (m = !0, M(x))), r;
	}, e.unstable_shouldYield = D, e.unstable_wrapCallback = function(e) {
		var t = f;
		return function() {
			var n = f;
			f = t;
			try {
				return e.apply(this, arguments);
			} finally {
				f = n;
			}
		};
	};
})), p = /* @__PURE__ */ o(((e, t) => {
	t.exports = f();
})), m = /* @__PURE__ */ o(((e) => {
	var t = d(), n = p();
	function r(e) {
		for (var t = "https://reactjs.org/docs/error-decoder.html?invariant=" + e, n = 1; n < arguments.length; n++) t += "&args[]=" + encodeURIComponent(arguments[n]);
		return "Minified React error #" + e + "; visit " + t + " for the full message or use the non-minified dev environment for full errors and additional helpful warnings.";
	}
	var i = /* @__PURE__ */ new Set(), a = {};
	function o(e, t) {
		s(e, t), s(e + "Capture", t);
	}
	function s(e, t) {
		for (a[e] = t, e = 0; e < t.length; e++) i.add(t[e]);
	}
	var c = !(typeof window > "u" || window.document === void 0 || window.document.createElement === void 0), l = Object.prototype.hasOwnProperty, u = /^[:A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD][:A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\-.0-9\u00B7\u0300-\u036F\u203F-\u2040]*$/, f = {}, m = {};
	function h(e) {
		return l.call(m, e) ? !0 : l.call(f, e) ? !1 : u.test(e) ? m[e] = !0 : (f[e] = !0, !1);
	}
	function g(e, t, n, r) {
		if (n !== null && n.type === 0) return !1;
		switch (typeof t) {
			case "function":
			case "symbol": return !0;
			case "boolean": return r ? !1 : n === null ? (e = e.toLowerCase().slice(0, 5), e !== "data-" && e !== "aria-") : !n.acceptsBooleans;
			default: return !1;
		}
	}
	function _(e, t, n, r) {
		if (t == null || g(e, t, n, r)) return !0;
		if (r) return !1;
		if (n !== null) switch (n.type) {
			case 3: return !t;
			case 4: return !1 === t;
			case 5: return isNaN(t);
			case 6: return isNaN(t) || 1 > t;
		}
		return !1;
	}
	function v(e, t, n, r, i, a, o) {
		this.acceptsBooleans = t === 2 || t === 3 || t === 4, this.attributeName = r, this.attributeNamespace = i, this.mustUseProperty = n, this.propertyName = e, this.type = t, this.sanitizeURL = a, this.removeEmptyString = o;
	}
	var y = {};
	"children dangerouslySetInnerHTML defaultValue defaultChecked innerHTML suppressContentEditableWarning suppressHydrationWarning style".split(" ").forEach(function(e) {
		y[e] = new v(e, 0, !1, e, null, !1, !1);
	}), [
		["acceptCharset", "accept-charset"],
		["className", "class"],
		["htmlFor", "for"],
		["httpEquiv", "http-equiv"]
	].forEach(function(e) {
		var t = e[0];
		y[t] = new v(t, 1, !1, e[1], null, !1, !1);
	}), [
		"contentEditable",
		"draggable",
		"spellCheck",
		"value"
	].forEach(function(e) {
		y[e] = new v(e, 2, !1, e.toLowerCase(), null, !1, !1);
	}), [
		"autoReverse",
		"externalResourcesRequired",
		"focusable",
		"preserveAlpha"
	].forEach(function(e) {
		y[e] = new v(e, 2, !1, e, null, !1, !1);
	}), "allowFullScreen async autoFocus autoPlay controls default defer disabled disablePictureInPicture disableRemotePlayback formNoValidate hidden loop noModule noValidate open playsInline readOnly required reversed scoped seamless itemScope".split(" ").forEach(function(e) {
		y[e] = new v(e, 3, !1, e.toLowerCase(), null, !1, !1);
	}), [
		"checked",
		"multiple",
		"muted",
		"selected"
	].forEach(function(e) {
		y[e] = new v(e, 3, !0, e, null, !1, !1);
	}), ["capture", "download"].forEach(function(e) {
		y[e] = new v(e, 4, !1, e, null, !1, !1);
	}), [
		"cols",
		"rows",
		"size",
		"span"
	].forEach(function(e) {
		y[e] = new v(e, 6, !1, e, null, !1, !1);
	}), ["rowSpan", "start"].forEach(function(e) {
		y[e] = new v(e, 5, !1, e.toLowerCase(), null, !1, !1);
	});
	var b = /[\-:]([a-z])/g;
	function x(e) {
		return e[1].toUpperCase();
	}
	"accent-height alignment-baseline arabic-form baseline-shift cap-height clip-path clip-rule color-interpolation color-interpolation-filters color-profile color-rendering dominant-baseline enable-background fill-opacity fill-rule flood-color flood-opacity font-family font-size font-size-adjust font-stretch font-style font-variant font-weight glyph-name glyph-orientation-horizontal glyph-orientation-vertical horiz-adv-x horiz-origin-x image-rendering letter-spacing lighting-color marker-end marker-mid marker-start overline-position overline-thickness paint-order panose-1 pointer-events rendering-intent shape-rendering stop-color stop-opacity strikethrough-position strikethrough-thickness stroke-dasharray stroke-dashoffset stroke-linecap stroke-linejoin stroke-miterlimit stroke-opacity stroke-width text-anchor text-decoration text-rendering underline-position underline-thickness unicode-bidi unicode-range units-per-em v-alphabetic v-hanging v-ideographic v-mathematical vector-effect vert-adv-y vert-origin-x vert-origin-y word-spacing writing-mode xmlns:xlink x-height".split(" ").forEach(function(e) {
		var t = e.replace(b, x);
		y[t] = new v(t, 1, !1, e, null, !1, !1);
	}), "xlink:actuate xlink:arcrole xlink:role xlink:show xlink:title xlink:type".split(" ").forEach(function(e) {
		var t = e.replace(b, x);
		y[t] = new v(t, 1, !1, e, "http://www.w3.org/1999/xlink", !1, !1);
	}), [
		"xml:base",
		"xml:lang",
		"xml:space"
	].forEach(function(e) {
		var t = e.replace(b, x);
		y[t] = new v(t, 1, !1, e, "http://www.w3.org/XML/1998/namespace", !1, !1);
	}), ["tabIndex", "crossOrigin"].forEach(function(e) {
		y[e] = new v(e, 1, !1, e.toLowerCase(), null, !1, !1);
	}), y.xlinkHref = new v("xlinkHref", 1, !1, "xlink:href", "http://www.w3.org/1999/xlink", !0, !1), [
		"src",
		"href",
		"action",
		"formAction"
	].forEach(function(e) {
		y[e] = new v(e, 1, !1, e.toLowerCase(), null, !0, !0);
	});
	function S(e, t, n, r) {
		var i = y.hasOwnProperty(t) ? y[t] : null;
		(i === null ? r || !(2 < t.length) || t[0] !== "o" && t[0] !== "O" || t[1] !== "n" && t[1] !== "N" : i.type !== 0) && (_(t, n, i, r) && (n = null), r || i === null ? h(t) && (n === null ? e.removeAttribute(t) : e.setAttribute(t, "" + n)) : i.mustUseProperty ? e[i.propertyName] = n === null ? i.type !== 3 && "" : n : (t = i.attributeName, r = i.attributeNamespace, n === null ? e.removeAttribute(t) : (i = i.type, n = i === 3 || i === 4 && !0 === n ? "" : "" + n, r ? e.setAttributeNS(r, t, n) : e.setAttribute(t, n))));
	}
	var C = t.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED, w = Symbol.for("react.element"), T = Symbol.for("react.portal"), E = Symbol.for("react.fragment"), D = Symbol.for("react.strict_mode"), O = Symbol.for("react.profiler"), k = Symbol.for("react.provider"), A = Symbol.for("react.context"), j = Symbol.for("react.forward_ref"), M = Symbol.for("react.suspense"), N = Symbol.for("react.suspense_list"), P = Symbol.for("react.memo"), ee = Symbol.for("react.lazy"), te = Symbol.for("react.offscreen"), ne = Symbol.iterator;
	function re(e) {
		return typeof e != "object" || !e ? null : (e = ne && e[ne] || e["@@iterator"], typeof e == "function" ? e : null);
	}
	var ie = Object.assign, ae;
	function oe(e) {
		if (ae === void 0) try {
			throw Error();
		} catch (e) {
			var t = e.stack.trim().match(/\n( *(at )?)/);
			ae = t && t[1] || "";
		}
		return "\n" + ae + e;
	}
	var se = !1;
	function ce(e, t) {
		if (!e || se) return "";
		se = !0;
		var n = Error.prepareStackTrace;
		Error.prepareStackTrace = void 0;
		try {
			if (t) if (t = function() {
				throw Error();
			}, Object.defineProperty(t.prototype, "props", { set: function() {
				throw Error();
			} }), typeof Reflect == "object" && Reflect.construct) {
				try {
					Reflect.construct(t, []);
				} catch (e) {
					var r = e;
				}
				Reflect.construct(e, [], t);
			} else {
				try {
					t.call();
				} catch (e) {
					r = e;
				}
				e.call(t.prototype);
			}
			else {
				try {
					throw Error();
				} catch (e) {
					r = e;
				}
				e();
			}
		} catch (t) {
			if (t && r && typeof t.stack == "string") {
				for (var i = t.stack.split("\n"), a = r.stack.split("\n"), o = i.length - 1, s = a.length - 1; 1 <= o && 0 <= s && i[o] !== a[s];) s--;
				for (; 1 <= o && 0 <= s; o--, s--) if (i[o] !== a[s]) {
					if (o !== 1 || s !== 1) do
						if (o--, s--, 0 > s || i[o] !== a[s]) {
							var c = "\n" + i[o].replace(" at new ", " at ");
							return e.displayName && c.includes("<anonymous>") && (c = c.replace("<anonymous>", e.displayName)), c;
						}
					while (1 <= o && 0 <= s);
					break;
				}
			}
		} finally {
			se = !1, Error.prepareStackTrace = n;
		}
		return (e = e ? e.displayName || e.name : "") ? oe(e) : "";
	}
	function le(e) {
		switch (e.tag) {
			case 5: return oe(e.type);
			case 16: return oe("Lazy");
			case 13: return oe("Suspense");
			case 19: return oe("SuspenseList");
			case 0:
			case 2:
			case 15: return e = ce(e.type, !1), e;
			case 11: return e = ce(e.type.render, !1), e;
			case 1: return e = ce(e.type, !0), e;
			default: return "";
		}
	}
	function ue(e) {
		if (e == null) return null;
		if (typeof e == "function") return e.displayName || e.name || null;
		if (typeof e == "string") return e;
		switch (e) {
			case E: return "Fragment";
			case T: return "Portal";
			case O: return "Profiler";
			case D: return "StrictMode";
			case M: return "Suspense";
			case N: return "SuspenseList";
		}
		if (typeof e == "object") switch (e.$$typeof) {
			case A: return (e.displayName || "Context") + ".Consumer";
			case k: return (e._context.displayName || "Context") + ".Provider";
			case j:
				var t = e.render;
				return e = e.displayName, e || (e = t.displayName || t.name || "", e = e === "" ? "ForwardRef" : "ForwardRef(" + e + ")"), e;
			case P: return t = e.displayName || null, t === null ? ue(e.type) || "Memo" : t;
			case ee:
				t = e._payload, e = e._init;
				try {
					return ue(e(t));
				} catch (e) {}
		}
		return null;
	}
	function de(e) {
		var t = e.type;
		switch (e.tag) {
			case 24: return "Cache";
			case 9: return (t.displayName || "Context") + ".Consumer";
			case 10: return (t._context.displayName || "Context") + ".Provider";
			case 18: return "DehydratedFragment";
			case 11: return e = t.render, e = e.displayName || e.name || "", t.displayName || (e === "" ? "ForwardRef" : "ForwardRef(" + e + ")");
			case 7: return "Fragment";
			case 5: return t;
			case 4: return "Portal";
			case 3: return "Root";
			case 6: return "Text";
			case 16: return ue(t);
			case 8: return t === D ? "StrictMode" : "Mode";
			case 22: return "Offscreen";
			case 12: return "Profiler";
			case 21: return "Scope";
			case 13: return "Suspense";
			case 19: return "SuspenseList";
			case 25: return "TracingMarker";
			case 1:
			case 0:
			case 17:
			case 2:
			case 14:
			case 15:
				if (typeof t == "function") return t.displayName || t.name || null;
				if (typeof t == "string") return t;
		}
		return null;
	}
	function fe(e) {
		switch (typeof e) {
			case "boolean":
			case "number":
			case "string":
			case "undefined": return e;
			case "object": return e;
			default: return "";
		}
	}
	function pe(e) {
		var t = e.type;
		return (e = e.nodeName) && e.toLowerCase() === "input" && (t === "checkbox" || t === "radio");
	}
	function me(e) {
		var t = pe(e) ? "checked" : "value", n = Object.getOwnPropertyDescriptor(e.constructor.prototype, t), r = "" + e[t];
		if (!e.hasOwnProperty(t) && n !== void 0 && typeof n.get == "function" && typeof n.set == "function") {
			var i = n.get, a = n.set;
			return Object.defineProperty(e, t, {
				configurable: !0,
				get: function() {
					return i.call(this);
				},
				set: function(e) {
					r = "" + e, a.call(this, e);
				}
			}), Object.defineProperty(e, t, { enumerable: n.enumerable }), {
				getValue: function() {
					return r;
				},
				setValue: function(e) {
					r = "" + e;
				},
				stopTracking: function() {
					e._valueTracker = null, delete e[t];
				}
			};
		}
	}
	function he(e) {
		e._valueTracker || (e._valueTracker = me(e));
	}
	function ge(e) {
		if (!e) return !1;
		var t = e._valueTracker;
		if (!t) return !0;
		var n = t.getValue(), r = "";
		return e && (r = pe(e) ? e.checked ? "true" : "false" : e.value), e = r, e === n ? !1 : (t.setValue(e), !0);
	}
	function _e(e) {
		if (e = e || (typeof document < "u" ? document : void 0), e === void 0) return null;
		try {
			return e.activeElement || e.body;
		} catch (t) {
			return e.body;
		}
	}
	function ve(e, t) {
		var n = t.checked;
		return ie({}, t, {
			defaultChecked: void 0,
			defaultValue: void 0,
			value: void 0,
			checked: n == null ? e._wrapperState.initialChecked : n
		});
	}
	function ye(e, t) {
		var n = t.defaultValue == null ? "" : t.defaultValue, r = t.checked == null ? t.defaultChecked : t.checked;
		n = fe(t.value == null ? n : t.value), e._wrapperState = {
			initialChecked: r,
			initialValue: n,
			controlled: t.type === "checkbox" || t.type === "radio" ? t.checked != null : t.value != null
		};
	}
	function be(e, t) {
		t = t.checked, t != null && S(e, "checked", t, !1);
	}
	function xe(e, t) {
		be(e, t);
		var n = fe(t.value), r = t.type;
		if (n != null) r === "number" ? (n === 0 && e.value === "" || e.value != n) && (e.value = "" + n) : e.value !== "" + n && (e.value = "" + n);
		else if (r === "submit" || r === "reset") {
			e.removeAttribute("value");
			return;
		}
		t.hasOwnProperty("value") ? Ce(e, t.type, n) : t.hasOwnProperty("defaultValue") && Ce(e, t.type, fe(t.defaultValue)), t.checked == null && t.defaultChecked != null && (e.defaultChecked = !!t.defaultChecked);
	}
	function Se(e, t, n) {
		if (t.hasOwnProperty("value") || t.hasOwnProperty("defaultValue")) {
			var r = t.type;
			if (!(r !== "submit" && r !== "reset" || t.value !== void 0 && t.value !== null)) return;
			t = "" + e._wrapperState.initialValue, n || t === e.value || (e.value = t), e.defaultValue = t;
		}
		n = e.name, n !== "" && (e.name = ""), e.defaultChecked = !!e._wrapperState.initialChecked, n !== "" && (e.name = n);
	}
	function Ce(e, t, n) {
		(t !== "number" || _e(e.ownerDocument) !== e) && (n == null ? e.defaultValue = "" + e._wrapperState.initialValue : e.defaultValue !== "" + n && (e.defaultValue = "" + n));
	}
	var we = Array.isArray;
	function Te(e, t, n, r) {
		if (e = e.options, t) {
			t = {};
			for (var i = 0; i < n.length; i++) t["$" + n[i]] = !0;
			for (n = 0; n < e.length; n++) i = t.hasOwnProperty("$" + e[n].value), e[n].selected !== i && (e[n].selected = i), i && r && (e[n].defaultSelected = !0);
		} else {
			for (n = "" + fe(n), t = null, i = 0; i < e.length; i++) {
				if (e[i].value === n) {
					e[i].selected = !0, r && (e[i].defaultSelected = !0);
					return;
				}
				t !== null || e[i].disabled || (t = e[i]);
			}
			t !== null && (t.selected = !0);
		}
	}
	function Ee(e, t) {
		if (t.dangerouslySetInnerHTML != null) throw Error(r(91));
		return ie({}, t, {
			value: void 0,
			defaultValue: void 0,
			children: "" + e._wrapperState.initialValue
		});
	}
	function De(e, t) {
		var n = t.value;
		if (n == null) {
			if (n = t.children, t = t.defaultValue, n != null) {
				if (t != null) throw Error(r(92));
				if (we(n)) {
					if (1 < n.length) throw Error(r(93));
					n = n[0];
				}
				t = n;
			}
			t == null && (t = ""), n = t;
		}
		e._wrapperState = { initialValue: fe(n) };
	}
	function Oe(e, t) {
		var n = fe(t.value), r = fe(t.defaultValue);
		n != null && (n = "" + n, n !== e.value && (e.value = n), t.defaultValue == null && e.defaultValue !== n && (e.defaultValue = n)), r != null && (e.defaultValue = "" + r);
	}
	function ke(e) {
		var t = e.textContent;
		t === e._wrapperState.initialValue && t !== "" && t !== null && (e.value = t);
	}
	function Ae(e) {
		switch (e) {
			case "svg": return "http://www.w3.org/2000/svg";
			case "math": return "http://www.w3.org/1998/Math/MathML";
			default: return "http://www.w3.org/1999/xhtml";
		}
	}
	function je(e, t) {
		return e == null || e === "http://www.w3.org/1999/xhtml" ? Ae(t) : e === "http://www.w3.org/2000/svg" && t === "foreignObject" ? "http://www.w3.org/1999/xhtml" : e;
	}
	var Me, Ne = function(e) {
		return typeof MSApp < "u" && MSApp.execUnsafeLocalFunction ? function(t, n, r, i) {
			MSApp.execUnsafeLocalFunction(function() {
				return e(t, n, r, i);
			});
		} : e;
	}(function(e, t) {
		if (e.namespaceURI !== "http://www.w3.org/2000/svg" || "innerHTML" in e) e.innerHTML = t;
		else {
			for (Me = Me || document.createElement("div"), Me.innerHTML = "<svg>" + t.valueOf().toString() + "</svg>", t = Me.firstChild; e.firstChild;) e.removeChild(e.firstChild);
			for (; t.firstChild;) e.appendChild(t.firstChild);
		}
	});
	function Pe(e, t) {
		if (t) {
			var n = e.firstChild;
			if (n && n === e.lastChild && n.nodeType === 3) {
				n.nodeValue = t;
				return;
			}
		}
		e.textContent = t;
	}
	var Fe = {
		animationIterationCount: !0,
		aspectRatio: !0,
		borderImageOutset: !0,
		borderImageSlice: !0,
		borderImageWidth: !0,
		boxFlex: !0,
		boxFlexGroup: !0,
		boxOrdinalGroup: !0,
		columnCount: !0,
		columns: !0,
		flex: !0,
		flexGrow: !0,
		flexPositive: !0,
		flexShrink: !0,
		flexNegative: !0,
		flexOrder: !0,
		gridArea: !0,
		gridRow: !0,
		gridRowEnd: !0,
		gridRowSpan: !0,
		gridRowStart: !0,
		gridColumn: !0,
		gridColumnEnd: !0,
		gridColumnSpan: !0,
		gridColumnStart: !0,
		fontWeight: !0,
		lineClamp: !0,
		lineHeight: !0,
		opacity: !0,
		order: !0,
		orphans: !0,
		tabSize: !0,
		widows: !0,
		zIndex: !0,
		zoom: !0,
		fillOpacity: !0,
		floodOpacity: !0,
		stopOpacity: !0,
		strokeDasharray: !0,
		strokeDashoffset: !0,
		strokeMiterlimit: !0,
		strokeOpacity: !0,
		strokeWidth: !0
	}, Ie = [
		"Webkit",
		"ms",
		"Moz",
		"O"
	];
	Object.keys(Fe).forEach(function(e) {
		Ie.forEach(function(t) {
			t = t + e.charAt(0).toUpperCase() + e.substring(1), Fe[t] = Fe[e];
		});
	});
	function Le(e, t, n) {
		return t == null || typeof t == "boolean" || t === "" ? "" : n || typeof t != "number" || t === 0 || Fe.hasOwnProperty(e) && Fe[e] ? ("" + t).trim() : t + "px";
	}
	function Re(e, t) {
		for (var n in e = e.style, t) if (t.hasOwnProperty(n)) {
			var r = n.indexOf("--") === 0, i = Le(n, t[n], r);
			n === "float" && (n = "cssFloat"), r ? e.setProperty(n, i) : e[n] = i;
		}
	}
	var ze = ie({ menuitem: !0 }, {
		area: !0,
		base: !0,
		br: !0,
		col: !0,
		embed: !0,
		hr: !0,
		img: !0,
		input: !0,
		keygen: !0,
		link: !0,
		meta: !0,
		param: !0,
		source: !0,
		track: !0,
		wbr: !0
	});
	function Be(e, t) {
		if (t) {
			if (ze[e] && (t.children != null || t.dangerouslySetInnerHTML != null)) throw Error(r(137, e));
			if (t.dangerouslySetInnerHTML != null) {
				if (t.children != null) throw Error(r(60));
				if (typeof t.dangerouslySetInnerHTML != "object" || !("__html" in t.dangerouslySetInnerHTML)) throw Error(r(61));
			}
			if (t.style != null && typeof t.style != "object") throw Error(r(62));
		}
	}
	function Ve(e, t) {
		if (e.indexOf("-") === -1) return typeof t.is == "string";
		switch (e) {
			case "annotation-xml":
			case "color-profile":
			case "font-face":
			case "font-face-src":
			case "font-face-uri":
			case "font-face-format":
			case "font-face-name":
			case "missing-glyph": return !1;
			default: return !0;
		}
	}
	var He = null;
	function Ue(e) {
		return e = e.target || e.srcElement || window, e.correspondingUseElement && (e = e.correspondingUseElement), e.nodeType === 3 ? e.parentNode : e;
	}
	var We = null, Ge = null, Ke = null;
	function qe(e) {
		if (e = Wi(e)) {
			if (typeof We != "function") throw Error(r(280));
			var t = e.stateNode;
			t && (t = Ki(t), We(e.stateNode, e.type, t));
		}
	}
	function Je(e) {
		Ge ? Ke ? Ke.push(e) : Ke = [e] : Ge = e;
	}
	function Ye() {
		if (Ge) {
			var e = Ge, t = Ke;
			if (Ke = Ge = null, qe(e), t) for (e = 0; e < t.length; e++) qe(t[e]);
		}
	}
	function Xe(e, t) {
		return e(t);
	}
	function Ze() {}
	var Qe = !1;
	function $e(e, t, n) {
		if (Qe) return e(t, n);
		Qe = !0;
		try {
			return Xe(e, t, n);
		} finally {
			Qe = !1, (Ge !== null || Ke !== null) && (Ze(), Ye());
		}
	}
	function et(e, t) {
		var n = e.stateNode;
		if (n === null) return null;
		var i = Ki(n);
		if (i === null) return null;
		n = i[t];
		a: switch (t) {
			case "onClick":
			case "onClickCapture":
			case "onDoubleClick":
			case "onDoubleClickCapture":
			case "onMouseDown":
			case "onMouseDownCapture":
			case "onMouseMove":
			case "onMouseMoveCapture":
			case "onMouseUp":
			case "onMouseUpCapture":
			case "onMouseEnter":
				(i = !i.disabled) || (e = e.type, i = !(e === "button" || e === "input" || e === "select" || e === "textarea")), e = !i;
				break a;
			default: e = !1;
		}
		if (e) return null;
		if (n && typeof n != "function") throw Error(r(231, t, typeof n));
		return n;
	}
	var tt = !1;
	if (c) try {
		var nt = {};
		Object.defineProperty(nt, "passive", { get: function() {
			tt = !0;
		} }), window.addEventListener("test", nt, nt), window.removeEventListener("test", nt, nt);
	} catch (e) {
		tt = !1;
	}
	function rt(e, t, n, r, i, a, o, s, c) {
		var l = Array.prototype.slice.call(arguments, 3);
		try {
			t.apply(n, l);
		} catch (e) {
			this.onError(e);
		}
	}
	var it = !1, at = null, ot = !1, st = null, ct = { onError: function(e) {
		it = !0, at = e;
	} };
	function lt(e, t, n, r, i, a, o, s, c) {
		it = !1, at = null, rt.apply(ct, arguments);
	}
	function ut(e, t, n, i, a, o, s, c, l) {
		if (lt.apply(this, arguments), it) {
			if (it) {
				var u = at;
				it = !1, at = null;
			} else throw Error(r(198));
			ot || (ot = !0, st = u);
		}
	}
	function dt(e) {
		var t = e, n = e;
		if (e.alternate) for (; t.return;) t = t.return;
		else {
			e = t;
			do
				t = e, t.flags & 4098 && (n = t.return), e = t.return;
			while (e);
		}
		return t.tag === 3 ? n : null;
	}
	function ft(e) {
		if (e.tag === 13) {
			var t = e.memoizedState;
			if (t === null && (e = e.alternate, e !== null && (t = e.memoizedState)), t !== null) return t.dehydrated;
		}
		return null;
	}
	function pt(e) {
		if (dt(e) !== e) throw Error(r(188));
	}
	function mt(e) {
		var t = e.alternate;
		if (!t) {
			if (t = dt(e), t === null) throw Error(r(188));
			return t === e ? e : null;
		}
		for (var n = e, i = t;;) {
			var a = n.return;
			if (a === null) break;
			var o = a.alternate;
			if (o === null) {
				if (i = a.return, i !== null) {
					n = i;
					continue;
				}
				break;
			}
			if (a.child === o.child) {
				for (o = a.child; o;) {
					if (o === n) return pt(a), e;
					if (o === i) return pt(a), t;
					o = o.sibling;
				}
				throw Error(r(188));
			}
			if (n.return !== i.return) n = a, i = o;
			else {
				for (var s = !1, c = a.child; c;) {
					if (c === n) {
						s = !0, n = a, i = o;
						break;
					}
					if (c === i) {
						s = !0, i = a, n = o;
						break;
					}
					c = c.sibling;
				}
				if (!s) {
					for (c = o.child; c;) {
						if (c === n) {
							s = !0, n = o, i = a;
							break;
						}
						if (c === i) {
							s = !0, i = o, n = a;
							break;
						}
						c = c.sibling;
					}
					if (!s) throw Error(r(189));
				}
			}
			if (n.alternate !== i) throw Error(r(190));
		}
		if (n.tag !== 3) throw Error(r(188));
		return n.stateNode.current === n ? e : t;
	}
	function ht(e) {
		return e = mt(e), e === null ? null : gt(e);
	}
	function gt(e) {
		if (e.tag === 5 || e.tag === 6) return e;
		for (e = e.child; e !== null;) {
			var t = gt(e);
			if (t !== null) return t;
			e = e.sibling;
		}
		return null;
	}
	var _t = n.unstable_scheduleCallback, vt = n.unstable_cancelCallback, yt = n.unstable_shouldYield, bt = n.unstable_requestPaint, xt = n.unstable_now, St = n.unstable_getCurrentPriorityLevel, Ct = n.unstable_ImmediatePriority, wt = n.unstable_UserBlockingPriority, Tt = n.unstable_NormalPriority, Et = n.unstable_LowPriority, Dt = n.unstable_IdlePriority, Ot = null, kt = null;
	function At(e) {
		if (kt && typeof kt.onCommitFiberRoot == "function") try {
			kt.onCommitFiberRoot(Ot, e, void 0, (e.current.flags & 128) == 128);
		} catch (e) {}
	}
	var jt = Math.clz32 ? Math.clz32 : Pt, Mt = Math.log, Nt = Math.LN2;
	function Pt(e) {
		return e >>>= 0, e === 0 ? 32 : 31 - (Mt(e) / Nt | 0) | 0;
	}
	var Ft = 64, It = 4194304;
	function Lt(e) {
		switch (e & -e) {
			case 1: return 1;
			case 2: return 2;
			case 4: return 4;
			case 8: return 8;
			case 16: return 16;
			case 32: return 32;
			case 64:
			case 128:
			case 256:
			case 512:
			case 1024:
			case 2048:
			case 4096:
			case 8192:
			case 16384:
			case 32768:
			case 65536:
			case 131072:
			case 262144:
			case 524288:
			case 1048576:
			case 2097152: return e & 4194240;
			case 4194304:
			case 8388608:
			case 16777216:
			case 33554432:
			case 67108864: return e & 130023424;
			case 134217728: return 134217728;
			case 268435456: return 268435456;
			case 536870912: return 536870912;
			case 1073741824: return 1073741824;
			default: return e;
		}
	}
	function Rt(e, t) {
		var n = e.pendingLanes;
		if (n === 0) return 0;
		var r = 0, i = e.suspendedLanes, a = e.pingedLanes, o = n & 268435455;
		if (o !== 0) {
			var s = o & ~i;
			s === 0 ? (a &= o, a !== 0 && (r = Lt(a))) : r = Lt(s);
		} else o = n & ~i, o === 0 ? a !== 0 && (r = Lt(a)) : r = Lt(o);
		if (r === 0) return 0;
		if (t !== 0 && t !== r && (t & i) === 0 && (i = r & -r, a = t & -t, i >= a || i === 16 && a & 4194240)) return t;
		if (r & 4 && (r |= n & 16), t = e.entangledLanes, t !== 0) for (e = e.entanglements, t &= r; 0 < t;) n = 31 - jt(t), i = 1 << n, r |= e[n], t &= ~i;
		return r;
	}
	function zt(e, t) {
		switch (e) {
			case 1:
			case 2:
			case 4: return t + 250;
			case 8:
			case 16:
			case 32:
			case 64:
			case 128:
			case 256:
			case 512:
			case 1024:
			case 2048:
			case 4096:
			case 8192:
			case 16384:
			case 32768:
			case 65536:
			case 131072:
			case 262144:
			case 524288:
			case 1048576:
			case 2097152: return t + 5e3;
			case 4194304:
			case 8388608:
			case 16777216:
			case 33554432:
			case 67108864: return -1;
			case 134217728:
			case 268435456:
			case 536870912:
			case 1073741824: return -1;
			default: return -1;
		}
	}
	function Bt(e, t) {
		for (var n = e.suspendedLanes, r = e.pingedLanes, i = e.expirationTimes, a = e.pendingLanes; 0 < a;) {
			var o = 31 - jt(a), s = 1 << o, c = i[o];
			c === -1 ? ((s & n) === 0 || (s & r) !== 0) && (i[o] = zt(s, t)) : c <= t && (e.expiredLanes |= s), a &= ~s;
		}
	}
	function Vt(e) {
		return e = e.pendingLanes & -1073741825, e === 0 ? e & 1073741824 ? 1073741824 : 0 : e;
	}
	function Ht() {
		var e = Ft;
		return Ft <<= 1, !(Ft & 4194240) && (Ft = 64), e;
	}
	function Ut(e) {
		for (var t = [], n = 0; 31 > n; n++) t.push(e);
		return t;
	}
	function Wt(e, t, n) {
		e.pendingLanes |= t, t !== 536870912 && (e.suspendedLanes = 0, e.pingedLanes = 0), e = e.eventTimes, t = 31 - jt(t), e[t] = n;
	}
	function Gt(e, t) {
		var n = e.pendingLanes & ~t;
		e.pendingLanes = t, e.suspendedLanes = 0, e.pingedLanes = 0, e.expiredLanes &= t, e.mutableReadLanes &= t, e.entangledLanes &= t, t = e.entanglements;
		var r = e.eventTimes;
		for (e = e.expirationTimes; 0 < n;) {
			var i = 31 - jt(n), a = 1 << i;
			t[i] = 0, r[i] = -1, e[i] = -1, n &= ~a;
		}
	}
	function Kt(e, t) {
		var n = e.entangledLanes |= t;
		for (e = e.entanglements; n;) {
			var r = 31 - jt(n), i = 1 << r;
			i & t | e[r] & t && (e[r] |= t), n &= ~i;
		}
	}
	var F = 0;
	function I(e) {
		return e &= -e, 1 < e ? 4 < e ? e & 268435455 ? 16 : 536870912 : 4 : 1;
	}
	var qt, Jt, Yt, Xt, Zt, Qt = !1, $t = [], en = null, tn = null, nn = null, rn = /* @__PURE__ */ new Map(), an = /* @__PURE__ */ new Map(), on = [], sn = "mousedown mouseup touchcancel touchend touchstart auxclick dblclick pointercancel pointerdown pointerup dragend dragstart drop compositionend compositionstart keydown keypress keyup input textInput copy cut paste click change contextmenu reset submit".split(" ");
	function cn(e, t) {
		switch (e) {
			case "focusin":
			case "focusout":
				en = null;
				break;
			case "dragenter":
			case "dragleave":
				tn = null;
				break;
			case "mouseover":
			case "mouseout":
				nn = null;
				break;
			case "pointerover":
			case "pointerout":
				rn.delete(t.pointerId);
				break;
			case "gotpointercapture":
			case "lostpointercapture": an.delete(t.pointerId);
		}
	}
	function ln(e, t, n, r, i, a) {
		return e === null || e.nativeEvent !== a ? (e = {
			blockedOn: t,
			domEventName: n,
			eventSystemFlags: r,
			nativeEvent: a,
			targetContainers: [i]
		}, t !== null && (t = Wi(t), t !== null && Jt(t)), e) : (e.eventSystemFlags |= r, t = e.targetContainers, i !== null && t.indexOf(i) === -1 && t.push(i), e);
	}
	function un(e, t, n, r, i) {
		switch (t) {
			case "focusin": return en = ln(en, e, t, n, r, i), !0;
			case "dragenter": return tn = ln(tn, e, t, n, r, i), !0;
			case "mouseover": return nn = ln(nn, e, t, n, r, i), !0;
			case "pointerover":
				var a = i.pointerId;
				return rn.set(a, ln(rn.get(a) || null, e, t, n, r, i)), !0;
			case "gotpointercapture": return a = i.pointerId, an.set(a, ln(an.get(a) || null, e, t, n, r, i)), !0;
		}
		return !1;
	}
	function dn(e) {
		var t = Ui(e.target);
		if (t !== null) {
			var n = dt(t);
			if (n !== null) {
				if (t = n.tag, t === 13) {
					if (t = ft(n), t !== null) {
						e.blockedOn = t, Zt(e.priority, function() {
							Yt(n);
						});
						return;
					}
				} else if (t === 3 && n.stateNode.current.memoizedState.isDehydrated) {
					e.blockedOn = n.tag === 3 ? n.stateNode.containerInfo : null;
					return;
				}
			}
		}
		e.blockedOn = null;
	}
	function fn(e) {
		if (e.blockedOn !== null) return !1;
		for (var t = e.targetContainers; 0 < t.length;) {
			var n = Cn(e.domEventName, e.eventSystemFlags, t[0], e.nativeEvent);
			if (n === null) {
				n = e.nativeEvent;
				var r = new n.constructor(n.type, n);
				He = r, n.target.dispatchEvent(r), He = null;
			} else return t = Wi(n), t !== null && Jt(t), e.blockedOn = n, !1;
			t.shift();
		}
		return !0;
	}
	function pn(e, t, n) {
		fn(e) && n.delete(t);
	}
	function mn() {
		Qt = !1, en !== null && fn(en) && (en = null), tn !== null && fn(tn) && (tn = null), nn !== null && fn(nn) && (nn = null), rn.forEach(pn), an.forEach(pn);
	}
	function hn(e, t) {
		e.blockedOn === t && (e.blockedOn = null, Qt || (Qt = !0, n.unstable_scheduleCallback(n.unstable_NormalPriority, mn)));
	}
	function gn(e) {
		function t(t) {
			return hn(t, e);
		}
		if (0 < $t.length) {
			hn($t[0], e);
			for (var n = 1; n < $t.length; n++) {
				var r = $t[n];
				r.blockedOn === e && (r.blockedOn = null);
			}
		}
		for (en !== null && hn(en, e), tn !== null && hn(tn, e), nn !== null && hn(nn, e), rn.forEach(t), an.forEach(t), n = 0; n < on.length; n++) r = on[n], r.blockedOn === e && (r.blockedOn = null);
		for (; 0 < on.length && (n = on[0], n.blockedOn === null);) dn(n), n.blockedOn === null && on.shift();
	}
	var _n = C.ReactCurrentBatchConfig, vn = !0;
	function yn(e, t, n, r) {
		var i = F, a = _n.transition;
		_n.transition = null;
		try {
			F = 1, xn(e, t, n, r);
		} finally {
			F = i, _n.transition = a;
		}
	}
	function bn(e, t, n, r) {
		var i = F, a = _n.transition;
		_n.transition = null;
		try {
			F = 4, xn(e, t, n, r);
		} finally {
			F = i, _n.transition = a;
		}
	}
	function xn(e, t, n, r) {
		if (vn) {
			var i = Cn(e, t, n, r);
			if (i === null) hi(e, t, r, Sn, n), cn(e, r);
			else if (un(i, e, t, n, r)) r.stopPropagation();
			else if (cn(e, r), t & 4 && -1 < sn.indexOf(e)) {
				for (; i !== null;) {
					var a = Wi(i);
					if (a !== null && qt(a), a = Cn(e, t, n, r), a === null && hi(e, t, r, Sn, n), a === i) break;
					i = a;
				}
				i !== null && r.stopPropagation();
			} else hi(e, t, r, null, n);
		}
	}
	var Sn = null;
	function Cn(e, t, n, r) {
		if (Sn = null, e = Ue(r), e = Ui(e), e !== null) if (t = dt(e), t === null) e = null;
		else if (n = t.tag, n === 13) {
			if (e = ft(t), e !== null) return e;
			e = null;
		} else if (n === 3) {
			if (t.stateNode.current.memoizedState.isDehydrated) return t.tag === 3 ? t.stateNode.containerInfo : null;
			e = null;
		} else t !== e && (e = null);
		return Sn = e, null;
	}
	function wn(e) {
		switch (e) {
			case "cancel":
			case "click":
			case "close":
			case "contextmenu":
			case "copy":
			case "cut":
			case "auxclick":
			case "dblclick":
			case "dragend":
			case "dragstart":
			case "drop":
			case "focusin":
			case "focusout":
			case "input":
			case "invalid":
			case "keydown":
			case "keypress":
			case "keyup":
			case "mousedown":
			case "mouseup":
			case "paste":
			case "pause":
			case "play":
			case "pointercancel":
			case "pointerdown":
			case "pointerup":
			case "ratechange":
			case "reset":
			case "resize":
			case "seeked":
			case "submit":
			case "touchcancel":
			case "touchend":
			case "touchstart":
			case "volumechange":
			case "change":
			case "selectionchange":
			case "textInput":
			case "compositionstart":
			case "compositionend":
			case "compositionupdate":
			case "beforeblur":
			case "afterblur":
			case "beforeinput":
			case "blur":
			case "fullscreenchange":
			case "focus":
			case "hashchange":
			case "popstate":
			case "select":
			case "selectstart": return 1;
			case "drag":
			case "dragenter":
			case "dragexit":
			case "dragleave":
			case "dragover":
			case "mousemove":
			case "mouseout":
			case "mouseover":
			case "pointermove":
			case "pointerout":
			case "pointerover":
			case "scroll":
			case "toggle":
			case "touchmove":
			case "wheel":
			case "mouseenter":
			case "mouseleave":
			case "pointerenter":
			case "pointerleave": return 4;
			case "message": switch (St()) {
				case Ct: return 1;
				case wt: return 4;
				case Tt:
				case Et: return 16;
				case Dt: return 536870912;
				default: return 16;
			}
			default: return 16;
		}
	}
	var Tn = null, En = null, Dn = null;
	function On() {
		if (Dn) return Dn;
		var e, t = En, n = t.length, r, i = "value" in Tn ? Tn.value : Tn.textContent, a = i.length;
		for (e = 0; e < n && t[e] === i[e]; e++);
		var o = n - e;
		for (r = 1; r <= o && t[n - r] === i[a - r]; r++);
		return Dn = i.slice(e, 1 < r ? 1 - r : void 0);
	}
	function kn(e) {
		var t = e.keyCode;
		return "charCode" in e ? (e = e.charCode, e === 0 && t === 13 && (e = 13)) : e = t, e === 10 && (e = 13), 32 <= e || e === 13 ? e : 0;
	}
	function An() {
		return !0;
	}
	function jn() {
		return !1;
	}
	function Mn(e) {
		function t(t, n, r, i, a) {
			for (var o in this._reactName = t, this._targetInst = r, this.type = n, this.nativeEvent = i, this.target = a, this.currentTarget = null, e) e.hasOwnProperty(o) && (t = e[o], this[o] = t ? t(i) : i[o]);
			return this.isDefaultPrevented = (i.defaultPrevented == null ? !1 === i.returnValue : i.defaultPrevented) ? An : jn, this.isPropagationStopped = jn, this;
		}
		return ie(t.prototype, {
			preventDefault: function() {
				this.defaultPrevented = !0;
				var e = this.nativeEvent;
				e && (e.preventDefault ? e.preventDefault() : typeof e.returnValue != "unknown" && (e.returnValue = !1), this.isDefaultPrevented = An);
			},
			stopPropagation: function() {
				var e = this.nativeEvent;
				e && (e.stopPropagation ? e.stopPropagation() : typeof e.cancelBubble != "unknown" && (e.cancelBubble = !0), this.isPropagationStopped = An);
			},
			persist: function() {},
			isPersistent: An
		}), t;
	}
	var Nn = {
		eventPhase: 0,
		bubbles: 0,
		cancelable: 0,
		timeStamp: function(e) {
			return e.timeStamp || Date.now();
		},
		defaultPrevented: 0,
		isTrusted: 0
	}, Pn = Mn(Nn), Fn = ie({}, Nn, {
		view: 0,
		detail: 0
	}), In = Mn(Fn), Ln, Rn, zn, Bn = ie({}, Fn, {
		screenX: 0,
		screenY: 0,
		clientX: 0,
		clientY: 0,
		pageX: 0,
		pageY: 0,
		ctrlKey: 0,
		shiftKey: 0,
		altKey: 0,
		metaKey: 0,
		getModifierState: Zn,
		button: 0,
		buttons: 0,
		relatedTarget: function(e) {
			return e.relatedTarget === void 0 ? e.fromElement === e.srcElement ? e.toElement : e.fromElement : e.relatedTarget;
		},
		movementX: function(e) {
			return "movementX" in e ? e.movementX : (e !== zn && (zn && e.type === "mousemove" ? (Ln = e.screenX - zn.screenX, Rn = e.screenY - zn.screenY) : Rn = Ln = 0, zn = e), Ln);
		},
		movementY: function(e) {
			return "movementY" in e ? e.movementY : Rn;
		}
	}), Vn = Mn(Bn), Hn = Mn(ie({}, Bn, { dataTransfer: 0 })), Un = Mn(ie({}, Fn, { relatedTarget: 0 })), Wn = Mn(ie({}, Nn, {
		animationName: 0,
		elapsedTime: 0,
		pseudoElement: 0
	})), Gn = Mn(ie({}, Nn, { clipboardData: function(e) {
		return "clipboardData" in e ? e.clipboardData : window.clipboardData;
	} })), Kn = Mn(ie({}, Nn, { data: 0 })), qn = {
		Esc: "Escape",
		Spacebar: " ",
		Left: "ArrowLeft",
		Up: "ArrowUp",
		Right: "ArrowRight",
		Down: "ArrowDown",
		Del: "Delete",
		Win: "OS",
		Menu: "ContextMenu",
		Apps: "ContextMenu",
		Scroll: "ScrollLock",
		MozPrintableKey: "Unidentified"
	}, Jn = {
		8: "Backspace",
		9: "Tab",
		12: "Clear",
		13: "Enter",
		16: "Shift",
		17: "Control",
		18: "Alt",
		19: "Pause",
		20: "CapsLock",
		27: "Escape",
		32: " ",
		33: "PageUp",
		34: "PageDown",
		35: "End",
		36: "Home",
		37: "ArrowLeft",
		38: "ArrowUp",
		39: "ArrowRight",
		40: "ArrowDown",
		45: "Insert",
		46: "Delete",
		112: "F1",
		113: "F2",
		114: "F3",
		115: "F4",
		116: "F5",
		117: "F6",
		118: "F7",
		119: "F8",
		120: "F9",
		121: "F10",
		122: "F11",
		123: "F12",
		144: "NumLock",
		145: "ScrollLock",
		224: "Meta"
	}, Yn = {
		Alt: "altKey",
		Control: "ctrlKey",
		Meta: "metaKey",
		Shift: "shiftKey"
	};
	function Xn(e) {
		var t = this.nativeEvent;
		return t.getModifierState ? t.getModifierState(e) : (e = Yn[e]) ? !!t[e] : !1;
	}
	function Zn() {
		return Xn;
	}
	var Qn = Mn(ie({}, Fn, {
		key: function(e) {
			if (e.key) {
				var t = qn[e.key] || e.key;
				if (t !== "Unidentified") return t;
			}
			return e.type === "keypress" ? (e = kn(e), e === 13 ? "Enter" : String.fromCharCode(e)) : e.type === "keydown" || e.type === "keyup" ? Jn[e.keyCode] || "Unidentified" : "";
		},
		code: 0,
		location: 0,
		ctrlKey: 0,
		shiftKey: 0,
		altKey: 0,
		metaKey: 0,
		repeat: 0,
		locale: 0,
		getModifierState: Zn,
		charCode: function(e) {
			return e.type === "keypress" ? kn(e) : 0;
		},
		keyCode: function(e) {
			return e.type === "keydown" || e.type === "keyup" ? e.keyCode : 0;
		},
		which: function(e) {
			return e.type === "keypress" ? kn(e) : e.type === "keydown" || e.type === "keyup" ? e.keyCode : 0;
		}
	})), $n = Mn(ie({}, Bn, {
		pointerId: 0,
		width: 0,
		height: 0,
		pressure: 0,
		tangentialPressure: 0,
		tiltX: 0,
		tiltY: 0,
		twist: 0,
		pointerType: 0,
		isPrimary: 0
	})), er = Mn(ie({}, Fn, {
		touches: 0,
		targetTouches: 0,
		changedTouches: 0,
		altKey: 0,
		metaKey: 0,
		ctrlKey: 0,
		shiftKey: 0,
		getModifierState: Zn
	})), tr = Mn(ie({}, Nn, {
		propertyName: 0,
		elapsedTime: 0,
		pseudoElement: 0
	})), nr = Mn(ie({}, Bn, {
		deltaX: function(e) {
			return "deltaX" in e ? e.deltaX : "wheelDeltaX" in e ? -e.wheelDeltaX : 0;
		},
		deltaY: function(e) {
			return "deltaY" in e ? e.deltaY : "wheelDeltaY" in e ? -e.wheelDeltaY : "wheelDelta" in e ? -e.wheelDelta : 0;
		},
		deltaZ: 0,
		deltaMode: 0
	})), rr = [
		9,
		13,
		27,
		32
	], ir = c && "CompositionEvent" in window, ar = null;
	c && "documentMode" in document && (ar = document.documentMode);
	var or = c && "TextEvent" in window && !ar, sr = c && (!ir || ar && 8 < ar && 11 >= ar), cr = " ", lr = !1;
	function ur(e, t) {
		switch (e) {
			case "keyup": return rr.indexOf(t.keyCode) !== -1;
			case "keydown": return t.keyCode !== 229;
			case "keypress":
			case "mousedown":
			case "focusout": return !0;
			default: return !1;
		}
	}
	function dr(e) {
		return e = e.detail, typeof e == "object" && "data" in e ? e.data : null;
	}
	var fr = !1;
	function pr(e, t) {
		switch (e) {
			case "compositionend": return dr(t);
			case "keypress": return t.which === 32 ? (lr = !0, cr) : null;
			case "textInput": return e = t.data, e === cr && lr ? null : e;
			default: return null;
		}
	}
	function mr(e, t) {
		if (fr) return e === "compositionend" || !ir && ur(e, t) ? (e = On(), Dn = En = Tn = null, fr = !1, e) : null;
		switch (e) {
			case "paste": return null;
			case "keypress":
				if (!(t.ctrlKey || t.altKey || t.metaKey) || t.ctrlKey && t.altKey) {
					if (t.char && 1 < t.char.length) return t.char;
					if (t.which) return String.fromCharCode(t.which);
				}
				return null;
			case "compositionend": return sr && t.locale !== "ko" ? null : t.data;
			default: return null;
		}
	}
	var hr = {
		color: !0,
		date: !0,
		datetime: !0,
		"datetime-local": !0,
		email: !0,
		month: !0,
		number: !0,
		password: !0,
		range: !0,
		search: !0,
		tel: !0,
		text: !0,
		time: !0,
		url: !0,
		week: !0
	};
	function gr(e) {
		var t = e && e.nodeName && e.nodeName.toLowerCase();
		return t === "input" ? !!hr[e.type] : t === "textarea";
	}
	function _r(e, t, n, r) {
		Je(r), t = _i(t, "onChange"), 0 < t.length && (n = new Pn("onChange", "change", null, n, r), e.push({
			event: n,
			listeners: t
		}));
	}
	var vr = null, yr = null;
	function br(e) {
		li(e, 0);
	}
	function xr(e) {
		if (ge(Gi(e))) return e;
	}
	function Sr(e, t) {
		if (e === "change") return t;
	}
	var Cr = !1;
	if (c) {
		var wr;
		if (c) {
			var Tr = "oninput" in document;
			if (!Tr) {
				var Er = document.createElement("div");
				Er.setAttribute("oninput", "return;"), Tr = typeof Er.oninput == "function";
			}
			wr = Tr;
		} else wr = !1;
		Cr = wr && (!document.documentMode || 9 < document.documentMode);
	}
	function Dr() {
		vr && (vr.detachEvent("onpropertychange", Or), yr = vr = null);
	}
	function Or(e) {
		if (e.propertyName === "value" && xr(yr)) {
			var t = [];
			_r(t, yr, e, Ue(e)), $e(br, t);
		}
	}
	function kr(e, t, n) {
		e === "focusin" ? (Dr(), vr = t, yr = n, vr.attachEvent("onpropertychange", Or)) : e === "focusout" && Dr();
	}
	function Ar(e) {
		if (e === "selectionchange" || e === "keyup" || e === "keydown") return xr(yr);
	}
	function jr(e, t) {
		if (e === "click") return xr(t);
	}
	function Mr(e, t) {
		if (e === "input" || e === "change") return xr(t);
	}
	function L(e, t) {
		return e === t && (e !== 0 || 1 / e == 1 / t) || e !== e && t !== t;
	}
	var Nr = typeof Object.is == "function" ? Object.is : L;
	function Pr(e, t) {
		if (Nr(e, t)) return !0;
		if (typeof e != "object" || !e || typeof t != "object" || !t) return !1;
		var n = Object.keys(e), r = Object.keys(t);
		if (n.length !== r.length) return !1;
		for (r = 0; r < n.length; r++) {
			var i = n[r];
			if (!l.call(t, i) || !Nr(e[i], t[i])) return !1;
		}
		return !0;
	}
	function Fr(e) {
		for (; e && e.firstChild;) e = e.firstChild;
		return e;
	}
	function Ir(e, t) {
		var n = Fr(e);
		e = 0;
		for (var r; n;) {
			if (n.nodeType === 3) {
				if (r = e + n.textContent.length, e <= t && r >= t) return {
					node: n,
					offset: t - e
				};
				e = r;
			}
			a: {
				for (; n;) {
					if (n.nextSibling) {
						n = n.nextSibling;
						break a;
					}
					n = n.parentNode;
				}
				n = void 0;
			}
			n = Fr(n);
		}
	}
	function Lr(e, t) {
		return e && t ? e === t ? !0 : e && e.nodeType === 3 ? !1 : t && t.nodeType === 3 ? Lr(e, t.parentNode) : "contains" in e ? e.contains(t) : e.compareDocumentPosition ? !!(e.compareDocumentPosition(t) & 16) : !1 : !1;
	}
	function Rr() {
		for (var e = window, t = _e(); t instanceof e.HTMLIFrameElement;) {
			try {
				var n = typeof t.contentWindow.location.href == "string";
			} catch (e) {
				n = !1;
			}
			if (n) e = t.contentWindow;
			else break;
			t = _e(e.document);
		}
		return t;
	}
	function zr(e) {
		var t = e && e.nodeName && e.nodeName.toLowerCase();
		return t && (t === "input" && (e.type === "text" || e.type === "search" || e.type === "tel" || e.type === "url" || e.type === "password") || t === "textarea" || e.contentEditable === "true");
	}
	function Br(e) {
		var t = Rr(), n = e.focusedElem, r = e.selectionRange;
		if (t !== n && n && n.ownerDocument && Lr(n.ownerDocument.documentElement, n)) {
			if (r !== null && zr(n)) {
				if (t = r.start, e = r.end, e === void 0 && (e = t), "selectionStart" in n) n.selectionStart = t, n.selectionEnd = Math.min(e, n.value.length);
				else if (e = (t = n.ownerDocument || document) && t.defaultView || window, e.getSelection) {
					e = e.getSelection();
					var i = n.textContent.length, a = Math.min(r.start, i);
					r = r.end === void 0 ? a : Math.min(r.end, i), !e.extend && a > r && (i = r, r = a, a = i), i = Ir(n, a);
					var o = Ir(n, r);
					i && o && (e.rangeCount !== 1 || e.anchorNode !== i.node || e.anchorOffset !== i.offset || e.focusNode !== o.node || e.focusOffset !== o.offset) && (t = t.createRange(), t.setStart(i.node, i.offset), e.removeAllRanges(), a > r ? (e.addRange(t), e.extend(o.node, o.offset)) : (t.setEnd(o.node, o.offset), e.addRange(t)));
				}
			}
			for (t = [], e = n; e = e.parentNode;) e.nodeType === 1 && t.push({
				element: e,
				left: e.scrollLeft,
				top: e.scrollTop
			});
			for (typeof n.focus == "function" && n.focus(), n = 0; n < t.length; n++) e = t[n], e.element.scrollLeft = e.left, e.element.scrollTop = e.top;
		}
	}
	var Vr = c && "documentMode" in document && 11 >= document.documentMode, Hr = null, Ur = null, Wr = null, Gr = !1;
	function Kr(e, t, n) {
		var r = n.window === n ? n.document : n.nodeType === 9 ? n : n.ownerDocument;
		Gr || Hr == null || Hr !== _e(r) || (r = Hr, "selectionStart" in r && zr(r) ? r = {
			start: r.selectionStart,
			end: r.selectionEnd
		} : (r = (r.ownerDocument && r.ownerDocument.defaultView || window).getSelection(), r = {
			anchorNode: r.anchorNode,
			anchorOffset: r.anchorOffset,
			focusNode: r.focusNode,
			focusOffset: r.focusOffset
		}), Wr && Pr(Wr, r) || (Wr = r, r = _i(Ur, "onSelect"), 0 < r.length && (t = new Pn("onSelect", "select", null, t, n), e.push({
			event: t,
			listeners: r
		}), t.target = Hr)));
	}
	function qr(e, t) {
		var n = {};
		return n[e.toLowerCase()] = t.toLowerCase(), n["Webkit" + e] = "webkit" + t, n["Moz" + e] = "moz" + t, n;
	}
	var Jr = {
		animationend: qr("Animation", "AnimationEnd"),
		animationiteration: qr("Animation", "AnimationIteration"),
		animationstart: qr("Animation", "AnimationStart"),
		transitionend: qr("Transition", "TransitionEnd")
	}, Yr = {}, R = {};
	c && (R = document.createElement("div").style, "AnimationEvent" in window || (delete Jr.animationend.animation, delete Jr.animationiteration.animation, delete Jr.animationstart.animation), "TransitionEvent" in window || delete Jr.transitionend.transition);
	function Xr(e) {
		if (Yr[e]) return Yr[e];
		if (!Jr[e]) return e;
		var t = Jr[e], n;
		for (n in t) if (t.hasOwnProperty(n) && n in R) return Yr[e] = t[n];
		return e;
	}
	var Zr = Xr("animationend"), Qr = Xr("animationiteration"), $r = Xr("animationstart"), ei = Xr("transitionend"), ti = /* @__PURE__ */ new Map(), ni = "abort auxClick cancel canPlay canPlayThrough click close contextMenu copy cut drag dragEnd dragEnter dragExit dragLeave dragOver dragStart drop durationChange emptied encrypted ended error gotPointerCapture input invalid keyDown keyPress keyUp load loadedData loadedMetadata loadStart lostPointerCapture mouseDown mouseMove mouseOut mouseOver mouseUp paste pause play playing pointerCancel pointerDown pointerMove pointerOut pointerOver pointerUp progress rateChange reset resize seeked seeking stalled submit suspend timeUpdate touchCancel touchEnd touchStart volumeChange scroll toggle touchMove waiting wheel".split(" ");
	function ri(e, t) {
		ti.set(e, t), o(t, [e]);
	}
	for (var ii = 0; ii < ni.length; ii++) {
		var ai = ni[ii];
		ri(ai.toLowerCase(), "on" + (ai[0].toUpperCase() + ai.slice(1)));
	}
	ri(Zr, "onAnimationEnd"), ri(Qr, "onAnimationIteration"), ri($r, "onAnimationStart"), ri("dblclick", "onDoubleClick"), ri("focusin", "onFocus"), ri("focusout", "onBlur"), ri(ei, "onTransitionEnd"), s("onMouseEnter", ["mouseout", "mouseover"]), s("onMouseLeave", ["mouseout", "mouseover"]), s("onPointerEnter", ["pointerout", "pointerover"]), s("onPointerLeave", ["pointerout", "pointerover"]), o("onChange", "change click focusin focusout input keydown keyup selectionchange".split(" ")), o("onSelect", "focusout contextmenu dragend focusin keydown keyup mousedown mouseup selectionchange".split(" ")), o("onBeforeInput", [
		"compositionend",
		"keypress",
		"textInput",
		"paste"
	]), o("onCompositionEnd", "compositionend focusout keydown keypress keyup mousedown".split(" ")), o("onCompositionStart", "compositionstart focusout keydown keypress keyup mousedown".split(" ")), o("onCompositionUpdate", "compositionupdate focusout keydown keypress keyup mousedown".split(" "));
	var oi = "abort canplay canplaythrough durationchange emptied encrypted ended error loadeddata loadedmetadata loadstart pause play playing progress ratechange resize seeked seeking stalled suspend timeupdate volumechange waiting".split(" "), si = new Set("cancel close invalid load scroll toggle".split(" ").concat(oi));
	function ci(e, t, n) {
		var r = e.type || "unknown-event";
		e.currentTarget = n, ut(r, t, void 0, e), e.currentTarget = null;
	}
	function li(e, t) {
		t = (t & 4) != 0;
		for (var n = 0; n < e.length; n++) {
			var r = e[n], i = r.event;
			r = r.listeners;
			a: {
				var a = void 0;
				if (t) for (var o = r.length - 1; 0 <= o; o--) {
					var s = r[o], c = s.instance, l = s.currentTarget;
					if (s = s.listener, c !== a && i.isPropagationStopped()) break a;
					ci(i, s, l), a = c;
				}
				else for (o = 0; o < r.length; o++) {
					if (s = r[o], c = s.instance, l = s.currentTarget, s = s.listener, c !== a && i.isPropagationStopped()) break a;
					ci(i, s, l), a = c;
				}
			}
		}
		if (ot) throw e = st, ot = !1, st = null, e;
	}
	function ui(e, t) {
		var n = t[Bi];
		n === void 0 && (n = t[Bi] = /* @__PURE__ */ new Set());
		var r = e + "__bubble";
		n.has(r) || (mi(t, e, 2, !1), n.add(r));
	}
	function di(e, t, n) {
		var r = 0;
		t && (r |= 4), mi(n, e, r, t);
	}
	var fi = "_reactListening" + Math.random().toString(36).slice(2);
	function pi(e) {
		if (!e[fi]) {
			e[fi] = !0, i.forEach(function(t) {
				t !== "selectionchange" && (si.has(t) || di(t, !1, e), di(t, !0, e));
			});
			var t = e.nodeType === 9 ? e : e.ownerDocument;
			t === null || t[fi] || (t[fi] = !0, di("selectionchange", !1, t));
		}
	}
	function mi(e, t, n, r) {
		switch (wn(t)) {
			case 1:
				var i = yn;
				break;
			case 4:
				i = bn;
				break;
			default: i = xn;
		}
		n = i.bind(null, t, n, e), i = void 0, !tt || t !== "touchstart" && t !== "touchmove" && t !== "wheel" || (i = !0), r ? i === void 0 ? e.addEventListener(t, n, !0) : e.addEventListener(t, n, {
			capture: !0,
			passive: i
		}) : i === void 0 ? e.addEventListener(t, n, !1) : e.addEventListener(t, n, { passive: i });
	}
	function hi(e, t, n, r, i) {
		var a = r;
		if (!(t & 1) && !(t & 2) && r !== null) a: for (;;) {
			if (r === null) return;
			var o = r.tag;
			if (o === 3 || o === 4) {
				var s = r.stateNode.containerInfo;
				if (s === i || s.nodeType === 8 && s.parentNode === i) break;
				if (o === 4) for (o = r.return; o !== null;) {
					var c = o.tag;
					if ((c === 3 || c === 4) && (c = o.stateNode.containerInfo, c === i || c.nodeType === 8 && c.parentNode === i)) return;
					o = o.return;
				}
				for (; s !== null;) {
					if (o = Ui(s), o === null) return;
					if (c = o.tag, c === 5 || c === 6) {
						r = a = o;
						continue a;
					}
					s = s.parentNode;
				}
			}
			r = r.return;
		}
		$e(function() {
			var r = a, i = Ue(n), o = [];
			a: {
				var s = ti.get(e);
				if (s !== void 0) {
					var c = Pn, l = e;
					switch (e) {
						case "keypress": if (kn(n) === 0) break a;
						case "keydown":
						case "keyup":
							c = Qn;
							break;
						case "focusin":
							l = "focus", c = Un;
							break;
						case "focusout":
							l = "blur", c = Un;
							break;
						case "beforeblur":
						case "afterblur":
							c = Un;
							break;
						case "click": if (n.button === 2) break a;
						case "auxclick":
						case "dblclick":
						case "mousedown":
						case "mousemove":
						case "mouseup":
						case "mouseout":
						case "mouseover":
						case "contextmenu":
							c = Vn;
							break;
						case "drag":
						case "dragend":
						case "dragenter":
						case "dragexit":
						case "dragleave":
						case "dragover":
						case "dragstart":
						case "drop":
							c = Hn;
							break;
						case "touchcancel":
						case "touchend":
						case "touchmove":
						case "touchstart":
							c = er;
							break;
						case Zr:
						case Qr:
						case $r:
							c = Wn;
							break;
						case ei:
							c = tr;
							break;
						case "scroll":
							c = In;
							break;
						case "wheel":
							c = nr;
							break;
						case "copy":
						case "cut":
						case "paste":
							c = Gn;
							break;
						case "gotpointercapture":
						case "lostpointercapture":
						case "pointercancel":
						case "pointerdown":
						case "pointermove":
						case "pointerout":
						case "pointerover":
						case "pointerup": c = $n;
					}
					var u = (t & 4) != 0, d = !u && e === "scroll", f = u ? s === null ? null : s + "Capture" : s;
					u = [];
					for (var p = r, m; p !== null;) {
						m = p;
						var h = m.stateNode;
						if (m.tag === 5 && h !== null && (m = h, f !== null && (h = et(p, f), h != null && u.push(gi(p, h, m)))), d) break;
						p = p.return;
					}
					0 < u.length && (s = new c(s, l, null, n, i), o.push({
						event: s,
						listeners: u
					}));
				}
			}
			if (!(t & 7)) {
				a: {
					if (s = e === "mouseover" || e === "pointerover", c = e === "mouseout" || e === "pointerout", s && n !== He && (l = n.relatedTarget || n.fromElement) && (Ui(l) || l[zi])) break a;
					if ((c || s) && (s = i.window === i ? i : (s = i.ownerDocument) ? s.defaultView || s.parentWindow : window, c ? (l = n.relatedTarget || n.toElement, c = r, l = l ? Ui(l) : null, l !== null && (d = dt(l), l !== d || l.tag !== 5 && l.tag !== 6) && (l = null)) : (c = null, l = r), c !== l)) {
						if (u = Vn, h = "onMouseLeave", f = "onMouseEnter", p = "mouse", (e === "pointerout" || e === "pointerover") && (u = $n, h = "onPointerLeave", f = "onPointerEnter", p = "pointer"), d = c == null ? s : Gi(c), m = l == null ? s : Gi(l), s = new u(h, p + "leave", c, n, i), s.target = d, s.relatedTarget = m, h = null, Ui(i) === r && (u = new u(f, p + "enter", l, n, i), u.target = m, u.relatedTarget = d, h = u), d = h, c && l) b: {
							for (u = c, f = l, p = 0, m = u; m; m = vi(m)) p++;
							for (m = 0, h = f; h; h = vi(h)) m++;
							for (; 0 < p - m;) u = vi(u), p--;
							for (; 0 < m - p;) f = vi(f), m--;
							for (; p--;) {
								if (u === f || f !== null && u === f.alternate) break b;
								u = vi(u), f = vi(f);
							}
							u = null;
						}
						else u = null;
						c !== null && yi(o, s, c, u, !1), l !== null && d !== null && yi(o, d, l, u, !0);
					}
				}
				a: {
					if (s = r ? Gi(r) : window, c = s.nodeName && s.nodeName.toLowerCase(), c === "select" || c === "input" && s.type === "file") var g = Sr;
					else if (gr(s)) if (Cr) g = Mr;
					else {
						g = Ar;
						var _ = kr;
					}
					else (c = s.nodeName) && c.toLowerCase() === "input" && (s.type === "checkbox" || s.type === "radio") && (g = jr);
					if (g && (g = g(e, r))) {
						_r(o, g, n, i);
						break a;
					}
					_ && _(e, s, r), e === "focusout" && (_ = s._wrapperState) && _.controlled && s.type === "number" && Ce(s, "number", s.value);
				}
				switch (_ = r ? Gi(r) : window, e) {
					case "focusin":
						(gr(_) || _.contentEditable === "true") && (Hr = _, Ur = r, Wr = null);
						break;
					case "focusout":
						Wr = Ur = Hr = null;
						break;
					case "mousedown":
						Gr = !0;
						break;
					case "contextmenu":
					case "mouseup":
					case "dragend":
						Gr = !1, Kr(o, n, i);
						break;
					case "selectionchange": if (Vr) break;
					case "keydown":
					case "keyup": Kr(o, n, i);
				}
				var v;
				if (ir) b: {
					switch (e) {
						case "compositionstart":
							var y = "onCompositionStart";
							break b;
						case "compositionend":
							y = "onCompositionEnd";
							break b;
						case "compositionupdate":
							y = "onCompositionUpdate";
							break b;
					}
					y = void 0;
				}
				else fr ? ur(e, n) && (y = "onCompositionEnd") : e === "keydown" && n.keyCode === 229 && (y = "onCompositionStart");
				y && (sr && n.locale !== "ko" && (fr || y !== "onCompositionStart" ? y === "onCompositionEnd" && fr && (v = On()) : (Tn = i, En = "value" in Tn ? Tn.value : Tn.textContent, fr = !0)), _ = _i(r, y), 0 < _.length && (y = new Kn(y, e, null, n, i), o.push({
					event: y,
					listeners: _
				}), v ? y.data = v : (v = dr(n), v !== null && (y.data = v)))), (v = or ? pr(e, n) : mr(e, n)) && (r = _i(r, "onBeforeInput"), 0 < r.length && (i = new Kn("onBeforeInput", "beforeinput", null, n, i), o.push({
					event: i,
					listeners: r
				}), i.data = v));
			}
			li(o, t);
		});
	}
	function gi(e, t, n) {
		return {
			instance: e,
			listener: t,
			currentTarget: n
		};
	}
	function _i(e, t) {
		for (var n = t + "Capture", r = []; e !== null;) {
			var i = e, a = i.stateNode;
			i.tag === 5 && a !== null && (i = a, a = et(e, n), a != null && r.unshift(gi(e, a, i)), a = et(e, t), a != null && r.push(gi(e, a, i))), e = e.return;
		}
		return r;
	}
	function vi(e) {
		if (e === null) return null;
		do
			e = e.return;
		while (e && e.tag !== 5);
		return e || null;
	}
	function yi(e, t, n, r, i) {
		for (var a = t._reactName, o = []; n !== null && n !== r;) {
			var s = n, c = s.alternate, l = s.stateNode;
			if (c !== null && c === r) break;
			s.tag === 5 && l !== null && (s = l, i ? (c = et(n, a), c != null && o.unshift(gi(n, c, s))) : i || (c = et(n, a), c != null && o.push(gi(n, c, s)))), n = n.return;
		}
		o.length !== 0 && e.push({
			event: t,
			listeners: o
		});
	}
	var bi = /\r\n?/g, xi = /\u0000|\uFFFD/g;
	function Si(e) {
		return (typeof e == "string" ? e : "" + e).replace(bi, "\n").replace(xi, "");
	}
	function Ci(e, t, n) {
		if (t = Si(t), Si(e) !== t && n) throw Error(r(425));
	}
	function wi() {}
	var Ti = null, Ei = null;
	function Di(e, t) {
		return e === "textarea" || e === "noscript" || typeof t.children == "string" || typeof t.children == "number" || typeof t.dangerouslySetInnerHTML == "object" && t.dangerouslySetInnerHTML !== null && t.dangerouslySetInnerHTML.__html != null;
	}
	var Oi = typeof setTimeout == "function" ? setTimeout : void 0, ki = typeof clearTimeout == "function" ? clearTimeout : void 0, Ai = typeof Promise == "function" ? Promise : void 0, ji = typeof queueMicrotask == "function" ? queueMicrotask : Ai === void 0 ? Oi : function(e) {
		return Ai.resolve(null).then(e).catch(Mi);
	};
	function Mi(e) {
		setTimeout(function() {
			throw e;
		});
	}
	function Ni(e, t) {
		var n = t, r = 0;
		do {
			var i = n.nextSibling;
			if (e.removeChild(n), i && i.nodeType === 8) if (n = i.data, n === "/$") {
				if (r === 0) {
					e.removeChild(i), gn(t);
					return;
				}
				r--;
			} else n !== "$" && n !== "$?" && n !== "$!" || r++;
			n = i;
		} while (n);
		gn(t);
	}
	function Pi(e) {
		for (; e != null; e = e.nextSibling) {
			var t = e.nodeType;
			if (t === 1 || t === 3) break;
			if (t === 8) {
				if (t = e.data, t === "$" || t === "$!" || t === "$?") break;
				if (t === "/$") return null;
			}
		}
		return e;
	}
	function Fi(e) {
		e = e.previousSibling;
		for (var t = 0; e;) {
			if (e.nodeType === 8) {
				var n = e.data;
				if (n === "$" || n === "$!" || n === "$?") {
					if (t === 0) return e;
					t--;
				} else n === "/$" && t++;
			}
			e = e.previousSibling;
		}
		return null;
	}
	var Ii = Math.random().toString(36).slice(2), Li = "__reactFiber$" + Ii, Ri = "__reactProps$" + Ii, zi = "__reactContainer$" + Ii, Bi = "__reactEvents$" + Ii, Vi = "__reactListeners$" + Ii, Hi = "__reactHandles$" + Ii;
	function Ui(e) {
		var t = e[Li];
		if (t) return t;
		for (var n = e.parentNode; n;) {
			if (t = n[zi] || n[Li]) {
				if (n = t.alternate, t.child !== null || n !== null && n.child !== null) for (e = Fi(e); e !== null;) {
					if (n = e[Li]) return n;
					e = Fi(e);
				}
				return t;
			}
			e = n, n = e.parentNode;
		}
		return null;
	}
	function Wi(e) {
		return e = e[Li] || e[zi], !e || e.tag !== 5 && e.tag !== 6 && e.tag !== 13 && e.tag !== 3 ? null : e;
	}
	function Gi(e) {
		if (e.tag === 5 || e.tag === 6) return e.stateNode;
		throw Error(r(33));
	}
	function Ki(e) {
		return e[Ri] || null;
	}
	var qi = [], Ji = -1;
	function Yi(e) {
		return { current: e };
	}
	function z(e) {
		0 > Ji || (e.current = qi[Ji], qi[Ji] = null, Ji--);
	}
	function B(e, t) {
		Ji++, qi[Ji] = e.current, e.current = t;
	}
	var Xi = {}, Zi = Yi(Xi), Qi = Yi(!1), $i = Xi;
	function ea(e, t) {
		var n = e.type.contextTypes;
		if (!n) return Xi;
		var r = e.stateNode;
		if (r && r.__reactInternalMemoizedUnmaskedChildContext === t) return r.__reactInternalMemoizedMaskedChildContext;
		var i = {}, a;
		for (a in n) i[a] = t[a];
		return r && (e = e.stateNode, e.__reactInternalMemoizedUnmaskedChildContext = t, e.__reactInternalMemoizedMaskedChildContext = i), i;
	}
	function ta(e) {
		return e = e.childContextTypes, e != null;
	}
	function na() {
		z(Qi), z(Zi);
	}
	function ra(e, t, n) {
		if (Zi.current !== Xi) throw Error(r(168));
		B(Zi, t), B(Qi, n);
	}
	function ia(e, t, n) {
		var i = e.stateNode;
		if (t = t.childContextTypes, typeof i.getChildContext != "function") return n;
		for (var a in i = i.getChildContext(), i) if (!(a in t)) throw Error(r(108, de(e) || "Unknown", a));
		return ie({}, n, i);
	}
	function aa(e) {
		return e = (e = e.stateNode) && e.__reactInternalMemoizedMergedChildContext || Xi, $i = Zi.current, B(Zi, e), B(Qi, Qi.current), !0;
	}
	function oa(e, t, n) {
		var i = e.stateNode;
		if (!i) throw Error(r(169));
		n ? (e = ia(e, t, $i), i.__reactInternalMemoizedMergedChildContext = e, z(Qi), z(Zi), B(Zi, e)) : z(Qi), B(Qi, n);
	}
	var sa = null, ca = !1, la = !1;
	function ua(e) {
		sa === null ? sa = [e] : sa.push(e);
	}
	function da(e) {
		ca = !0, ua(e);
	}
	function fa() {
		if (!la && sa !== null) {
			la = !0;
			var e = 0, t = F;
			try {
				var n = sa;
				for (F = 1; e < n.length; e++) {
					var r = n[e];
					do
						r = r(!0);
					while (r !== null);
				}
				sa = null, ca = !1;
			} catch (t) {
				throw sa !== null && (sa = sa.slice(e + 1)), _t(Ct, fa), t;
			} finally {
				F = t, la = !1;
			}
		}
		return null;
	}
	var pa = [], ma = 0, ha = null, ga = 0, _a = [], va = 0, ya = null, ba = 1, xa = "";
	function Sa(e, t) {
		pa[ma++] = ga, pa[ma++] = ha, ha = e, ga = t;
	}
	function Ca(e, t, n) {
		_a[va++] = ba, _a[va++] = xa, _a[va++] = ya, ya = e;
		var r = ba;
		e = xa;
		var i = 32 - jt(r) - 1;
		r &= ~(1 << i), n += 1;
		var a = 32 - jt(t) + i;
		if (30 < a) {
			var o = i - i % 5;
			a = (r & (1 << o) - 1).toString(32), r >>= o, i -= o, ba = 1 << 32 - jt(t) + i | n << i | r, xa = a + e;
		} else ba = 1 << a | n << i | r, xa = e;
	}
	function wa(e) {
		e.return !== null && (Sa(e, 1), Ca(e, 1, 0));
	}
	function Ta(e) {
		for (; e === ha;) ha = pa[--ma], pa[ma] = null, ga = pa[--ma], pa[ma] = null;
		for (; e === ya;) ya = _a[--va], _a[va] = null, xa = _a[--va], _a[va] = null, ba = _a[--va], _a[va] = null;
	}
	var Ea = null, Da = null, V = !1, Oa = null;
	function ka(e, t) {
		var n = Ql(5, null, null, 0);
		n.elementType = "DELETED", n.stateNode = t, n.return = e, t = e.deletions, t === null ? (e.deletions = [n], e.flags |= 16) : t.push(n);
	}
	function Aa(e, t) {
		switch (e.tag) {
			case 5:
				var n = e.type;
				return t = t.nodeType !== 1 || n.toLowerCase() !== t.nodeName.toLowerCase() ? null : t, t === null ? !1 : (e.stateNode = t, Ea = e, Da = Pi(t.firstChild), !0);
			case 6: return t = e.pendingProps === "" || t.nodeType !== 3 ? null : t, t === null ? !1 : (e.stateNode = t, Ea = e, Da = null, !0);
			case 13: return t = t.nodeType === 8 ? t : null, t === null ? !1 : (n = ya === null ? null : {
				id: ba,
				overflow: xa
			}, e.memoizedState = {
				dehydrated: t,
				treeContext: n,
				retryLane: 1073741824
			}, n = Ql(18, null, null, 0), n.stateNode = t, n.return = e, e.child = n, Ea = e, Da = null, !0);
			default: return !1;
		}
	}
	function ja(e) {
		return (e.mode & 1) != 0 && (e.flags & 128) == 0;
	}
	function Ma(e) {
		if (V) {
			var t = Da;
			if (t) {
				var n = t;
				if (!Aa(e, t)) {
					if (ja(e)) throw Error(r(418));
					t = Pi(n.nextSibling);
					var i = Ea;
					t && Aa(e, t) ? ka(i, n) : (e.flags = e.flags & -4097 | 2, V = !1, Ea = e);
				}
			} else {
				if (ja(e)) throw Error(r(418));
				e.flags = e.flags & -4097 | 2, V = !1, Ea = e;
			}
		}
	}
	function Na(e) {
		for (e = e.return; e !== null && e.tag !== 5 && e.tag !== 3 && e.tag !== 13;) e = e.return;
		Ea = e;
	}
	function Pa(e) {
		if (e !== Ea) return !1;
		if (!V) return Na(e), V = !0, !1;
		var t;
		if ((t = e.tag !== 3) && !(t = e.tag !== 5) && (t = e.type, t = t !== "head" && t !== "body" && !Di(e.type, e.memoizedProps)), t && (t = Da)) {
			if (ja(e)) throw Fa(), Error(r(418));
			for (; t;) ka(e, t), t = Pi(t.nextSibling);
		}
		if (Na(e), e.tag === 13) {
			if (e = e.memoizedState, e = e === null ? null : e.dehydrated, !e) throw Error(r(317));
			a: {
				for (e = e.nextSibling, t = 0; e;) {
					if (e.nodeType === 8) {
						var n = e.data;
						if (n === "/$") {
							if (t === 0) {
								Da = Pi(e.nextSibling);
								break a;
							}
							t--;
						} else n !== "$" && n !== "$!" && n !== "$?" || t++;
					}
					e = e.nextSibling;
				}
				Da = null;
			}
		} else Da = Ea ? Pi(e.stateNode.nextSibling) : null;
		return !0;
	}
	function Fa() {
		for (var e = Da; e;) e = Pi(e.nextSibling);
	}
	function Ia() {
		Da = Ea = null, V = !1;
	}
	function La(e) {
		Oa === null ? Oa = [e] : Oa.push(e);
	}
	var Ra = C.ReactCurrentBatchConfig;
	function za(e, t, n) {
		if (e = n.ref, e !== null && typeof e != "function" && typeof e != "object") {
			if (n._owner) {
				if (n = n._owner, n) {
					if (n.tag !== 1) throw Error(r(309));
					var i = n.stateNode;
				}
				if (!i) throw Error(r(147, e));
				var a = i, o = "" + e;
				return t !== null && t.ref !== null && typeof t.ref == "function" && t.ref._stringRef === o ? t.ref : (t = function(e) {
					var t = a.refs;
					e === null ? delete t[o] : t[o] = e;
				}, t._stringRef = o, t);
			}
			if (typeof e != "string") throw Error(r(284));
			if (!n._owner) throw Error(r(290, e));
		}
		return e;
	}
	function Ba(e, t) {
		throw e = Object.prototype.toString.call(t), Error(r(31, e === "[object Object]" ? "object with keys {" + Object.keys(t).join(", ") + "}" : e));
	}
	function Va(e) {
		var t = e._init;
		return t(e._payload);
	}
	function Ha(e) {
		function t(t, n) {
			if (e) {
				var r = t.deletions;
				r === null ? (t.deletions = [n], t.flags |= 16) : r.push(n);
			}
		}
		function n(n, r) {
			if (!e) return null;
			for (; r !== null;) t(n, r), r = r.sibling;
			return null;
		}
		function i(e, t) {
			for (e = /* @__PURE__ */ new Map(); t !== null;) t.key === null ? e.set(t.index, t) : e.set(t.key, t), t = t.sibling;
			return e;
		}
		function a(e, t) {
			return e = tu(e, t), e.index = 0, e.sibling = null, e;
		}
		function o(t, n, r) {
			return t.index = r, e ? (r = t.alternate, r === null ? (t.flags |= 2, n) : (r = r.index, r < n ? (t.flags |= 2, n) : r)) : (t.flags |= 1048576, n);
		}
		function s(t) {
			return e && t.alternate === null && (t.flags |= 2), t;
		}
		function c(e, t, n, r) {
			return t === null || t.tag !== 6 ? (t = au(n, e.mode, r), t.return = e, t) : (t = a(t, n), t.return = e, t);
		}
		function l(e, t, n, r) {
			var i = n.type;
			return i === E ? d(e, t, n.props.children, r, n.key) : t !== null && (t.elementType === i || typeof i == "object" && i && i.$$typeof === ee && Va(i) === t.type) ? (r = a(t, n.props), r.ref = za(e, t, n), r.return = e, r) : (r = nu(n.type, n.key, n.props, null, e.mode, r), r.ref = za(e, t, n), r.return = e, r);
		}
		function u(e, t, n, r) {
			return t === null || t.tag !== 4 || t.stateNode.containerInfo !== n.containerInfo || t.stateNode.implementation !== n.implementation ? (t = ou(n, e.mode, r), t.return = e, t) : (t = a(t, n.children || []), t.return = e, t);
		}
		function d(e, t, n, r, i) {
			return t === null || t.tag !== 7 ? (t = ru(n, e.mode, r, i), t.return = e, t) : (t = a(t, n), t.return = e, t);
		}
		function f(e, t, n) {
			if (typeof t == "string" && t !== "" || typeof t == "number") return t = au("" + t, e.mode, n), t.return = e, t;
			if (typeof t == "object" && t) {
				switch (t.$$typeof) {
					case w: return n = nu(t.type, t.key, t.props, null, e.mode, n), n.ref = za(e, null, t), n.return = e, n;
					case T: return t = ou(t, e.mode, n), t.return = e, t;
					case ee:
						var r = t._init;
						return f(e, r(t._payload), n);
				}
				if (we(t) || re(t)) return t = ru(t, e.mode, n, null), t.return = e, t;
				Ba(e, t);
			}
			return null;
		}
		function p(e, t, n, r) {
			var i = t === null ? null : t.key;
			if (typeof n == "string" && n !== "" || typeof n == "number") return i === null ? c(e, t, "" + n, r) : null;
			if (typeof n == "object" && n) {
				switch (n.$$typeof) {
					case w: return n.key === i ? l(e, t, n, r) : null;
					case T: return n.key === i ? u(e, t, n, r) : null;
					case ee: return i = n._init, p(e, t, i(n._payload), r);
				}
				if (we(n) || re(n)) return i === null ? d(e, t, n, r, null) : null;
				Ba(e, n);
			}
			return null;
		}
		function m(e, t, n, r, i) {
			if (typeof r == "string" && r !== "" || typeof r == "number") return e = e.get(n) || null, c(t, e, "" + r, i);
			if (typeof r == "object" && r) {
				switch (r.$$typeof) {
					case w: return e = e.get(r.key === null ? n : r.key) || null, l(t, e, r, i);
					case T: return e = e.get(r.key === null ? n : r.key) || null, u(t, e, r, i);
					case ee:
						var a = r._init;
						return m(e, t, n, a(r._payload), i);
				}
				if (we(r) || re(r)) return e = e.get(n) || null, d(t, e, r, i, null);
				Ba(t, r);
			}
			return null;
		}
		function h(r, a, s, c) {
			for (var l = null, u = null, d = a, h = a = 0, g = null; d !== null && h < s.length; h++) {
				d.index > h ? (g = d, d = null) : g = d.sibling;
				var _ = p(r, d, s[h], c);
				if (_ === null) {
					d === null && (d = g);
					break;
				}
				e && d && _.alternate === null && t(r, d), a = o(_, a, h), u === null ? l = _ : u.sibling = _, u = _, d = g;
			}
			if (h === s.length) return n(r, d), V && Sa(r, h), l;
			if (d === null) {
				for (; h < s.length; h++) d = f(r, s[h], c), d !== null && (a = o(d, a, h), u === null ? l = d : u.sibling = d, u = d);
				return V && Sa(r, h), l;
			}
			for (d = i(r, d); h < s.length; h++) g = m(d, r, h, s[h], c), g !== null && (e && g.alternate !== null && d.delete(g.key === null ? h : g.key), a = o(g, a, h), u === null ? l = g : u.sibling = g, u = g);
			return e && d.forEach(function(e) {
				return t(r, e);
			}), V && Sa(r, h), l;
		}
		function g(a, s, c, l) {
			var u = re(c);
			if (typeof u != "function") throw Error(r(150));
			if (c = u.call(c), c == null) throw Error(r(151));
			for (var d = u = null, h = s, g = s = 0, _ = null, v = c.next(); h !== null && !v.done; g++, v = c.next()) {
				h.index > g ? (_ = h, h = null) : _ = h.sibling;
				var y = p(a, h, v.value, l);
				if (y === null) {
					h === null && (h = _);
					break;
				}
				e && h && y.alternate === null && t(a, h), s = o(y, s, g), d === null ? u = y : d.sibling = y, d = y, h = _;
			}
			if (v.done) return n(a, h), V && Sa(a, g), u;
			if (h === null) {
				for (; !v.done; g++, v = c.next()) v = f(a, v.value, l), v !== null && (s = o(v, s, g), d === null ? u = v : d.sibling = v, d = v);
				return V && Sa(a, g), u;
			}
			for (h = i(a, h); !v.done; g++, v = c.next()) v = m(h, a, g, v.value, l), v !== null && (e && v.alternate !== null && h.delete(v.key === null ? g : v.key), s = o(v, s, g), d === null ? u = v : d.sibling = v, d = v);
			return e && h.forEach(function(e) {
				return t(a, e);
			}), V && Sa(a, g), u;
		}
		function _(e, r, i, o) {
			if (typeof i == "object" && i && i.type === E && i.key === null && (i = i.props.children), typeof i == "object" && i) {
				switch (i.$$typeof) {
					case w:
						a: {
							for (var c = i.key, l = r; l !== null;) {
								if (l.key === c) {
									if (c = i.type, c === E) {
										if (l.tag === 7) {
											n(e, l.sibling), r = a(l, i.props.children), r.return = e, e = r;
											break a;
										}
									} else if (l.elementType === c || typeof c == "object" && c && c.$$typeof === ee && Va(c) === l.type) {
										n(e, l.sibling), r = a(l, i.props), r.ref = za(e, l, i), r.return = e, e = r;
										break a;
									}
									n(e, l);
									break;
								} else t(e, l);
								l = l.sibling;
							}
							i.type === E ? (r = ru(i.props.children, e.mode, o, i.key), r.return = e, e = r) : (o = nu(i.type, i.key, i.props, null, e.mode, o), o.ref = za(e, r, i), o.return = e, e = o);
						}
						return s(e);
					case T:
						a: {
							for (l = i.key; r !== null;) {
								if (r.key === l) if (r.tag === 4 && r.stateNode.containerInfo === i.containerInfo && r.stateNode.implementation === i.implementation) {
									n(e, r.sibling), r = a(r, i.children || []), r.return = e, e = r;
									break a;
								} else {
									n(e, r);
									break;
								}
								else t(e, r);
								r = r.sibling;
							}
							r = ou(i, e.mode, o), r.return = e, e = r;
						}
						return s(e);
					case ee: return l = i._init, _(e, r, l(i._payload), o);
				}
				if (we(i)) return h(e, r, i, o);
				if (re(i)) return g(e, r, i, o);
				Ba(e, i);
			}
			return typeof i == "string" && i !== "" || typeof i == "number" ? (i = "" + i, r !== null && r.tag === 6 ? (n(e, r.sibling), r = a(r, i), r.return = e, e = r) : (n(e, r), r = au(i, e.mode, o), r.return = e, e = r), s(e)) : n(e, r);
		}
		return _;
	}
	var Ua = Ha(!0), Wa = Ha(!1), Ga = Yi(null), Ka = null, qa = null, H = null;
	function Ja() {
		H = qa = Ka = null;
	}
	function Ya(e) {
		var t = Ga.current;
		z(Ga), e._currentValue = t;
	}
	function Xa(e, t, n) {
		for (; e !== null;) {
			var r = e.alternate;
			if ((e.childLanes & t) === t ? r !== null && (r.childLanes & t) !== t && (r.childLanes |= t) : (e.childLanes |= t, r !== null && (r.childLanes |= t)), e === n) break;
			e = e.return;
		}
	}
	function Za(e, t) {
		Ka = e, H = qa = null, e = e.dependencies, e !== null && e.firstContext !== null && ((e.lanes & t) !== 0 && (zs = !0), e.firstContext = null);
	}
	function Qa(e) {
		var t = e._currentValue;
		if (H !== e) if (e = {
			context: e,
			memoizedValue: t,
			next: null
		}, qa === null) {
			if (Ka === null) throw Error(r(308));
			qa = e, Ka.dependencies = {
				lanes: 0,
				firstContext: e
			};
		} else qa = qa.next = e;
		return t;
	}
	var $a = null;
	function eo(e) {
		$a === null ? $a = [e] : $a.push(e);
	}
	function to(e, t, n, r) {
		var i = t.interleaved;
		return i === null ? (n.next = n, eo(t)) : (n.next = i.next, i.next = n), t.interleaved = n, no(e, r);
	}
	function no(e, t) {
		e.lanes |= t;
		var n = e.alternate;
		for (n !== null && (n.lanes |= t), n = e, e = e.return; e !== null;) e.childLanes |= t, n = e.alternate, n !== null && (n.childLanes |= t), n = e, e = e.return;
		return n.tag === 3 ? n.stateNode : null;
	}
	var ro = !1;
	function io(e) {
		e.updateQueue = {
			baseState: e.memoizedState,
			firstBaseUpdate: null,
			lastBaseUpdate: null,
			shared: {
				pending: null,
				interleaved: null,
				lanes: 0
			},
			effects: null
		};
	}
	function ao(e, t) {
		e = e.updateQueue, t.updateQueue === e && (t.updateQueue = {
			baseState: e.baseState,
			firstBaseUpdate: e.firstBaseUpdate,
			lastBaseUpdate: e.lastBaseUpdate,
			shared: e.shared,
			effects: e.effects
		});
	}
	function oo(e, t) {
		return {
			eventTime: e,
			lane: t,
			tag: 0,
			payload: null,
			callback: null,
			next: null
		};
	}
	function so(e, t, n) {
		var r = e.updateQueue;
		if (r === null) return null;
		if (r = r.shared, K & 2) {
			var i = r.pending;
			return i === null ? t.next = t : (t.next = i.next, i.next = t), r.pending = t, no(e, n);
		}
		return i = r.interleaved, i === null ? (t.next = t, eo(r)) : (t.next = i.next, i.next = t), r.interleaved = t, no(e, n);
	}
	function co(e, t, n) {
		if (t = t.updateQueue, t !== null && (t = t.shared, n & 4194240)) {
			var r = t.lanes;
			r &= e.pendingLanes, n |= r, t.lanes = n, Kt(e, n);
		}
	}
	function lo(e, t) {
		var n = e.updateQueue, r = e.alternate;
		if (r !== null && (r = r.updateQueue, n === r)) {
			var i = null, a = null;
			if (n = n.firstBaseUpdate, n !== null) {
				do {
					var o = {
						eventTime: n.eventTime,
						lane: n.lane,
						tag: n.tag,
						payload: n.payload,
						callback: n.callback,
						next: null
					};
					a === null ? i = a = o : a = a.next = o, n = n.next;
				} while (n !== null);
				a === null ? i = a = t : a = a.next = t;
			} else i = a = t;
			n = {
				baseState: r.baseState,
				firstBaseUpdate: i,
				lastBaseUpdate: a,
				shared: r.shared,
				effects: r.effects
			}, e.updateQueue = n;
			return;
		}
		e = n.lastBaseUpdate, e === null ? n.firstBaseUpdate = t : e.next = t, n.lastBaseUpdate = t;
	}
	function uo(e, t, n, r) {
		var i = e.updateQueue;
		ro = !1;
		var a = i.firstBaseUpdate, o = i.lastBaseUpdate, s = i.shared.pending;
		if (s !== null) {
			i.shared.pending = null;
			var c = s, l = c.next;
			c.next = null, o === null ? a = l : o.next = l, o = c;
			var u = e.alternate;
			u !== null && (u = u.updateQueue, s = u.lastBaseUpdate, s !== o && (s === null ? u.firstBaseUpdate = l : s.next = l, u.lastBaseUpdate = c));
		}
		if (a !== null) {
			var d = i.baseState;
			o = 0, u = l = c = null, s = a;
			do {
				var f = s.lane, p = s.eventTime;
				if ((r & f) === f) {
					u !== null && (u = u.next = {
						eventTime: p,
						lane: 0,
						tag: s.tag,
						payload: s.payload,
						callback: s.callback,
						next: null
					});
					a: {
						var m = e, h = s;
						switch (f = t, p = n, h.tag) {
							case 1:
								if (m = h.payload, typeof m == "function") {
									d = m.call(p, d, f);
									break a;
								}
								d = m;
								break a;
							case 3: m.flags = m.flags & -65537 | 128;
							case 0:
								if (m = h.payload, f = typeof m == "function" ? m.call(p, d, f) : m, f == null) break a;
								d = ie({}, d, f);
								break a;
							case 2: ro = !0;
						}
					}
					s.callback !== null && s.lane !== 0 && (e.flags |= 64, f = i.effects, f === null ? i.effects = [s] : f.push(s));
				} else p = {
					eventTime: p,
					lane: f,
					tag: s.tag,
					payload: s.payload,
					callback: s.callback,
					next: null
				}, u === null ? (l = u = p, c = d) : u = u.next = p, o |= f;
				if (s = s.next, s === null) {
					if (s = i.shared.pending, s === null) break;
					f = s, s = f.next, f.next = null, i.lastBaseUpdate = f, i.shared.pending = null;
				}
			} while (1);
			if (u === null && (c = d), i.baseState = c, i.firstBaseUpdate = l, i.lastBaseUpdate = u, t = i.shared.interleaved, t !== null) {
				i = t;
				do
					o |= i.lane, i = i.next;
				while (i !== t);
			} else a === null && (i.shared.lanes = 0);
			el |= o, e.lanes = o, e.memoizedState = d;
		}
	}
	function fo(e, t, n) {
		if (e = t.effects, t.effects = null, e !== null) for (t = 0; t < e.length; t++) {
			var i = e[t], a = i.callback;
			if (a !== null) {
				if (i.callback = null, i = n, typeof a != "function") throw Error(r(191, a));
				a.call(i);
			}
		}
	}
	var po = {}, mo = Yi(po), ho = Yi(po), go = Yi(po);
	function _o(e) {
		if (e === po) throw Error(r(174));
		return e;
	}
	function vo(e, t) {
		switch (B(go, t), B(ho, e), B(mo, po), e = t.nodeType, e) {
			case 9:
			case 11:
				t = (t = t.documentElement) ? t.namespaceURI : je(null, "");
				break;
			default: e = e === 8 ? t.parentNode : t, t = e.namespaceURI || null, e = e.tagName, t = je(t, e);
		}
		z(mo), B(mo, t);
	}
	function yo() {
		z(mo), z(ho), z(go);
	}
	function bo(e) {
		_o(go.current);
		var t = _o(mo.current), n = je(t, e.type);
		t !== n && (B(ho, e), B(mo, n));
	}
	function xo(e) {
		ho.current === e && (z(mo), z(ho));
	}
	var So = Yi(0);
	function Co(e) {
		for (var t = e; t !== null;) {
			if (t.tag === 13) {
				var n = t.memoizedState;
				if (n !== null && (n = n.dehydrated, n === null || n.data === "$?" || n.data === "$!")) return t;
			} else if (t.tag === 19 && t.memoizedProps.revealOrder !== void 0) {
				if (t.flags & 128) return t;
			} else if (t.child !== null) {
				t.child.return = t, t = t.child;
				continue;
			}
			if (t === e) break;
			for (; t.sibling === null;) {
				if (t.return === null || t.return === e) return null;
				t = t.return;
			}
			t.sibling.return = t.return, t = t.sibling;
		}
		return null;
	}
	var wo = [];
	function To() {
		for (var e = 0; e < wo.length; e++) wo[e]._workInProgressVersionPrimary = null;
		wo.length = 0;
	}
	var Eo = C.ReactCurrentDispatcher, Do = C.ReactCurrentBatchConfig, Oo = 0, ko = null, Ao = null, jo = null, Mo = !1, No = !1, Po = 0, Fo = 0;
	function Io() {
		throw Error(r(321));
	}
	function Lo(e, t) {
		if (t === null) return !1;
		for (var n = 0; n < t.length && n < e.length; n++) if (!Nr(e[n], t[n])) return !1;
		return !0;
	}
	function Ro(e, t, n, i, a, o) {
		if (Oo = o, ko = t, t.memoizedState = null, t.updateQueue = null, t.lanes = 0, Eo.current = e === null || e.memoizedState === null ? bs : xs, e = n(i, a), No) {
			o = 0;
			do {
				if (No = !1, Po = 0, 25 <= o) throw Error(r(301));
				o += 1, jo = Ao = null, t.updateQueue = null, Eo.current = Ss, e = n(i, a);
			} while (No);
		}
		if (Eo.current = ys, t = Ao !== null && Ao.next !== null, Oo = 0, jo = Ao = ko = null, Mo = !1, t) throw Error(r(300));
		return e;
	}
	function zo() {
		var e = Po !== 0;
		return Po = 0, e;
	}
	function Bo() {
		var e = {
			memoizedState: null,
			baseState: null,
			baseQueue: null,
			queue: null,
			next: null
		};
		return jo === null ? ko.memoizedState = jo = e : jo = jo.next = e, jo;
	}
	function Vo() {
		if (Ao === null) {
			var e = ko.alternate;
			e = e === null ? null : e.memoizedState;
		} else e = Ao.next;
		var t = jo === null ? ko.memoizedState : jo.next;
		if (t !== null) jo = t, Ao = e;
		else {
			if (e === null) throw Error(r(310));
			Ao = e, e = {
				memoizedState: Ao.memoizedState,
				baseState: Ao.baseState,
				baseQueue: Ao.baseQueue,
				queue: Ao.queue,
				next: null
			}, jo === null ? ko.memoizedState = jo = e : jo = jo.next = e;
		}
		return jo;
	}
	function Ho(e, t) {
		return typeof t == "function" ? t(e) : t;
	}
	function Uo(e) {
		var t = Vo(), n = t.queue;
		if (n === null) throw Error(r(311));
		n.lastRenderedReducer = e;
		var i = Ao, a = i.baseQueue, o = n.pending;
		if (o !== null) {
			if (a !== null) {
				var s = a.next;
				a.next = o.next, o.next = s;
			}
			i.baseQueue = a = o, n.pending = null;
		}
		if (a !== null) {
			o = a.next, i = i.baseState;
			var c = s = null, l = null, u = o;
			do {
				var d = u.lane;
				if ((Oo & d) === d) l !== null && (l = l.next = {
					lane: 0,
					action: u.action,
					hasEagerState: u.hasEagerState,
					eagerState: u.eagerState,
					next: null
				}), i = u.hasEagerState ? u.eagerState : e(i, u.action);
				else {
					var f = {
						lane: d,
						action: u.action,
						hasEagerState: u.hasEagerState,
						eagerState: u.eagerState,
						next: null
					};
					l === null ? (c = l = f, s = i) : l = l.next = f, ko.lanes |= d, el |= d;
				}
				u = u.next;
			} while (u !== null && u !== o);
			l === null ? s = i : l.next = c, Nr(i, t.memoizedState) || (zs = !0), t.memoizedState = i, t.baseState = s, t.baseQueue = l, n.lastRenderedState = i;
		}
		if (e = n.interleaved, e !== null) {
			a = e;
			do
				o = a.lane, ko.lanes |= o, el |= o, a = a.next;
			while (a !== e);
		} else a === null && (n.lanes = 0);
		return [t.memoizedState, n.dispatch];
	}
	function Wo(e) {
		var t = Vo(), n = t.queue;
		if (n === null) throw Error(r(311));
		n.lastRenderedReducer = e;
		var i = n.dispatch, a = n.pending, o = t.memoizedState;
		if (a !== null) {
			n.pending = null;
			var s = a = a.next;
			do
				o = e(o, s.action), s = s.next;
			while (s !== a);
			Nr(o, t.memoizedState) || (zs = !0), t.memoizedState = o, t.baseQueue === null && (t.baseState = o), n.lastRenderedState = o;
		}
		return [o, i];
	}
	function Go() {}
	function Ko(e, t) {
		var n = ko, i = Vo(), a = t(), o = !Nr(i.memoizedState, a);
		if (o && (i.memoizedState = a, zs = !0), i = i.queue, is(Yo.bind(null, n, i, e), [e]), i.getSnapshot !== t || o || jo !== null && jo.memoizedState.tag & 1) {
			if (n.flags |= 2048, $o(9, Jo.bind(null, n, i, a, t), void 0, null), q === null) throw Error(r(349));
			Oo & 30 || qo(n, t, a);
		}
		return a;
	}
	function qo(e, t, n) {
		e.flags |= 16384, e = {
			getSnapshot: t,
			value: n
		}, t = ko.updateQueue, t === null ? (t = {
			lastEffect: null,
			stores: null
		}, ko.updateQueue = t, t.stores = [e]) : (n = t.stores, n === null ? t.stores = [e] : n.push(e));
	}
	function Jo(e, t, n, r) {
		t.value = n, t.getSnapshot = r, Xo(t) && Zo(e);
	}
	function Yo(e, t, n) {
		return n(function() {
			Xo(t) && Zo(e);
		});
	}
	function Xo(e) {
		var t = e.getSnapshot;
		e = e.value;
		try {
			var n = t();
			return !Nr(e, n);
		} catch (e) {
			return !0;
		}
	}
	function Zo(e) {
		var t = no(e, 1);
		t !== null && bl(t, e, 1, -1);
	}
	function Qo(e) {
		var t = Bo();
		return typeof e == "function" && (e = e()), t.memoizedState = t.baseState = e, e = {
			pending: null,
			interleaved: null,
			lanes: 0,
			dispatch: null,
			lastRenderedReducer: Ho,
			lastRenderedState: e
		}, t.queue = e, e = e.dispatch = gs.bind(null, ko, e), [t.memoizedState, e];
	}
	function $o(e, t, n, r) {
		return e = {
			tag: e,
			create: t,
			destroy: n,
			deps: r,
			next: null
		}, t = ko.updateQueue, t === null ? (t = {
			lastEffect: null,
			stores: null
		}, ko.updateQueue = t, t.lastEffect = e.next = e) : (n = t.lastEffect, n === null ? t.lastEffect = e.next = e : (r = n.next, n.next = e, e.next = r, t.lastEffect = e)), e;
	}
	function es() {
		return Vo().memoizedState;
	}
	function ts(e, t, n, r) {
		var i = Bo();
		ko.flags |= e, i.memoizedState = $o(1 | t, n, void 0, r === void 0 ? null : r);
	}
	function ns(e, t, n, r) {
		var i = Vo();
		r = r === void 0 ? null : r;
		var a = void 0;
		if (Ao !== null) {
			var o = Ao.memoizedState;
			if (a = o.destroy, r !== null && Lo(r, o.deps)) {
				i.memoizedState = $o(t, n, a, r);
				return;
			}
		}
		ko.flags |= e, i.memoizedState = $o(1 | t, n, a, r);
	}
	function rs(e, t) {
		return ts(8390656, 8, e, t);
	}
	function is(e, t) {
		return ns(2048, 8, e, t);
	}
	function as(e, t) {
		return ns(4, 2, e, t);
	}
	function os(e, t) {
		return ns(4, 4, e, t);
	}
	function ss(e, t) {
		if (typeof t == "function") return e = e(), t(e), function() {
			t(null);
		};
		if (t != null) return e = e(), t.current = e, function() {
			t.current = null;
		};
	}
	function cs(e, t, n) {
		return n = n == null ? null : n.concat([e]), ns(4, 4, ss.bind(null, t, e), n);
	}
	function ls() {}
	function us(e, t) {
		var n = Vo();
		t = t === void 0 ? null : t;
		var r = n.memoizedState;
		return r !== null && t !== null && Lo(t, r[1]) ? r[0] : (n.memoizedState = [e, t], e);
	}
	function ds(e, t) {
		var n = Vo();
		t = t === void 0 ? null : t;
		var r = n.memoizedState;
		return r !== null && t !== null && Lo(t, r[1]) ? r[0] : (e = e(), n.memoizedState = [e, t], e);
	}
	function fs(e, t, n) {
		return Oo & 21 ? (Nr(n, t) || (n = Ht(), ko.lanes |= n, el |= n, e.baseState = !0), t) : (e.baseState && (e.baseState = !1, zs = !0), e.memoizedState = n);
	}
	function ps(e, t) {
		var n = F;
		F = n !== 0 && 4 > n ? n : 4, e(!0);
		var r = Do.transition;
		Do.transition = {};
		try {
			e(!1), t();
		} finally {
			F = n, Do.transition = r;
		}
	}
	function ms() {
		return Vo().memoizedState;
	}
	function hs(e, t, n) {
		var r = yl(e);
		if (n = {
			lane: r,
			action: n,
			hasEagerState: !1,
			eagerState: null,
			next: null
		}, U(e)) _s(t, n);
		else if (n = to(e, t, n, r), n !== null) {
			var i = vl();
			bl(n, e, r, i), vs(n, t, r);
		}
	}
	function gs(e, t, n) {
		var r = yl(e), i = {
			lane: r,
			action: n,
			hasEagerState: !1,
			eagerState: null,
			next: null
		};
		if (U(e)) _s(t, i);
		else {
			var a = e.alternate;
			if (e.lanes === 0 && (a === null || a.lanes === 0) && (a = t.lastRenderedReducer, a !== null)) try {
				var o = t.lastRenderedState, s = a(o, n);
				if (i.hasEagerState = !0, i.eagerState = s, Nr(s, o)) {
					var c = t.interleaved;
					c === null ? (i.next = i, eo(t)) : (i.next = c.next, c.next = i), t.interleaved = i;
					return;
				}
			} catch (e) {}
			n = to(e, t, i, r), n !== null && (i = vl(), bl(n, e, r, i), vs(n, t, r));
		}
	}
	function U(e) {
		var t = e.alternate;
		return e === ko || t !== null && t === ko;
	}
	function _s(e, t) {
		No = Mo = !0;
		var n = e.pending;
		n === null ? t.next = t : (t.next = n.next, n.next = t), e.pending = t;
	}
	function vs(e, t, n) {
		if (n & 4194240) {
			var r = t.lanes;
			r &= e.pendingLanes, n |= r, t.lanes = n, Kt(e, n);
		}
	}
	var ys = {
		readContext: Qa,
		useCallback: Io,
		useContext: Io,
		useEffect: Io,
		useImperativeHandle: Io,
		useInsertionEffect: Io,
		useLayoutEffect: Io,
		useMemo: Io,
		useReducer: Io,
		useRef: Io,
		useState: Io,
		useDebugValue: Io,
		useDeferredValue: Io,
		useTransition: Io,
		useMutableSource: Io,
		useSyncExternalStore: Io,
		useId: Io,
		unstable_isNewReconciler: !1
	}, bs = {
		readContext: Qa,
		useCallback: function(e, t) {
			return Bo().memoizedState = [e, t === void 0 ? null : t], e;
		},
		useContext: Qa,
		useEffect: rs,
		useImperativeHandle: function(e, t, n) {
			return n = n == null ? null : n.concat([e]), ts(4194308, 4, ss.bind(null, t, e), n);
		},
		useLayoutEffect: function(e, t) {
			return ts(4194308, 4, e, t);
		},
		useInsertionEffect: function(e, t) {
			return ts(4, 2, e, t);
		},
		useMemo: function(e, t) {
			var n = Bo();
			return t = t === void 0 ? null : t, e = e(), n.memoizedState = [e, t], e;
		},
		useReducer: function(e, t, n) {
			var r = Bo();
			return t = n === void 0 ? t : n(t), r.memoizedState = r.baseState = t, e = {
				pending: null,
				interleaved: null,
				lanes: 0,
				dispatch: null,
				lastRenderedReducer: e,
				lastRenderedState: t
			}, r.queue = e, e = e.dispatch = hs.bind(null, ko, e), [r.memoizedState, e];
		},
		useRef: function(e) {
			var t = Bo();
			return e = { current: e }, t.memoizedState = e;
		},
		useState: Qo,
		useDebugValue: ls,
		useDeferredValue: function(e) {
			return Bo().memoizedState = e;
		},
		useTransition: function() {
			var e = Qo(!1), t = e[0];
			return e = ps.bind(null, e[1]), Bo().memoizedState = e, [t, e];
		},
		useMutableSource: function() {},
		useSyncExternalStore: function(e, t, n) {
			var i = ko, a = Bo();
			if (V) {
				if (n === void 0) throw Error(r(407));
				n = n();
			} else {
				if (n = t(), q === null) throw Error(r(349));
				Oo & 30 || qo(i, t, n);
			}
			a.memoizedState = n;
			var o = {
				value: n,
				getSnapshot: t
			};
			return a.queue = o, rs(Yo.bind(null, i, o, e), [e]), i.flags |= 2048, $o(9, Jo.bind(null, i, o, n, t), void 0, null), n;
		},
		useId: function() {
			var e = Bo(), t = q.identifierPrefix;
			if (V) {
				var n = xa, r = ba;
				n = (r & ~(1 << 32 - jt(r) - 1)).toString(32) + n, t = ":" + t + "R" + n, n = Po++, 0 < n && (t += "H" + n.toString(32)), t += ":";
			} else n = Fo++, t = ":" + t + "r" + n.toString(32) + ":";
			return e.memoizedState = t;
		},
		unstable_isNewReconciler: !1
	}, xs = {
		readContext: Qa,
		useCallback: us,
		useContext: Qa,
		useEffect: is,
		useImperativeHandle: cs,
		useInsertionEffect: as,
		useLayoutEffect: os,
		useMemo: ds,
		useReducer: Uo,
		useRef: es,
		useState: function() {
			return Uo(Ho);
		},
		useDebugValue: ls,
		useDeferredValue: function(e) {
			return fs(Vo(), Ao.memoizedState, e);
		},
		useTransition: function() {
			return [Uo(Ho)[0], Vo().memoizedState];
		},
		useMutableSource: Go,
		useSyncExternalStore: Ko,
		useId: ms,
		unstable_isNewReconciler: !1
	}, Ss = {
		readContext: Qa,
		useCallback: us,
		useContext: Qa,
		useEffect: is,
		useImperativeHandle: cs,
		useInsertionEffect: as,
		useLayoutEffect: os,
		useMemo: ds,
		useReducer: Wo,
		useRef: es,
		useState: function() {
			return Wo(Ho);
		},
		useDebugValue: ls,
		useDeferredValue: function(e) {
			var t = Vo();
			return Ao === null ? t.memoizedState = e : fs(t, Ao.memoizedState, e);
		},
		useTransition: function() {
			return [Wo(Ho)[0], Vo().memoizedState];
		},
		useMutableSource: Go,
		useSyncExternalStore: Ko,
		useId: ms,
		unstable_isNewReconciler: !1
	};
	function W(e, t) {
		if (e && e.defaultProps) {
			for (var n in t = ie({}, t), e = e.defaultProps, e) t[n] === void 0 && (t[n] = e[n]);
			return t;
		}
		return t;
	}
	function Cs(e, t, n, r) {
		t = e.memoizedState, n = n(r, t), n = n == null ? t : ie({}, t, n), e.memoizedState = n, e.lanes === 0 && (e.updateQueue.baseState = n);
	}
	var ws = {
		isMounted: function(e) {
			return (e = e._reactInternals) ? dt(e) === e : !1;
		},
		enqueueSetState: function(e, t, n) {
			e = e._reactInternals;
			var r = vl(), i = yl(e), a = oo(r, i);
			a.payload = t, n != null && (a.callback = n), t = so(e, a, i), t !== null && (bl(t, e, i, r), co(t, e, i));
		},
		enqueueReplaceState: function(e, t, n) {
			e = e._reactInternals;
			var r = vl(), i = yl(e), a = oo(r, i);
			a.tag = 1, a.payload = t, n != null && (a.callback = n), t = so(e, a, i), t !== null && (bl(t, e, i, r), co(t, e, i));
		},
		enqueueForceUpdate: function(e, t) {
			e = e._reactInternals;
			var n = vl(), r = yl(e), i = oo(n, r);
			i.tag = 2, t != null && (i.callback = t), t = so(e, i, r), t !== null && (bl(t, e, r, n), co(t, e, r));
		}
	};
	function Ts(e, t, n, r, i, a, o) {
		return e = e.stateNode, typeof e.shouldComponentUpdate == "function" ? e.shouldComponentUpdate(r, a, o) : t.prototype && t.prototype.isPureReactComponent ? !Pr(n, r) || !Pr(i, a) : !0;
	}
	function Es(e, t, n) {
		var r = !1, i = Xi, a = t.contextType;
		return typeof a == "object" && a ? a = Qa(a) : (i = ta(t) ? $i : Zi.current, r = t.contextTypes, a = (r = r != null) ? ea(e, i) : Xi), t = new t(n, a), e.memoizedState = t.state !== null && t.state !== void 0 ? t.state : null, t.updater = ws, e.stateNode = t, t._reactInternals = e, r && (e = e.stateNode, e.__reactInternalMemoizedUnmaskedChildContext = i, e.__reactInternalMemoizedMaskedChildContext = a), t;
	}
	function Ds(e, t, n, r) {
		e = t.state, typeof t.componentWillReceiveProps == "function" && t.componentWillReceiveProps(n, r), typeof t.UNSAFE_componentWillReceiveProps == "function" && t.UNSAFE_componentWillReceiveProps(n, r), t.state !== e && ws.enqueueReplaceState(t, t.state, null);
	}
	function Os(e, t, n, r) {
		var i = e.stateNode;
		i.props = n, i.state = e.memoizedState, i.refs = {}, io(e);
		var a = t.contextType;
		typeof a == "object" && a ? i.context = Qa(a) : (a = ta(t) ? $i : Zi.current, i.context = ea(e, a)), i.state = e.memoizedState, a = t.getDerivedStateFromProps, typeof a == "function" && (Cs(e, t, a, n), i.state = e.memoizedState), typeof t.getDerivedStateFromProps == "function" || typeof i.getSnapshotBeforeUpdate == "function" || typeof i.UNSAFE_componentWillMount != "function" && typeof i.componentWillMount != "function" || (t = i.state, typeof i.componentWillMount == "function" && i.componentWillMount(), typeof i.UNSAFE_componentWillMount == "function" && i.UNSAFE_componentWillMount(), t !== i.state && ws.enqueueReplaceState(i, i.state, null), uo(e, n, i, r), i.state = e.memoizedState), typeof i.componentDidMount == "function" && (e.flags |= 4194308);
	}
	function ks(e, t) {
		try {
			var n = "", r = t;
			do
				n += le(r), r = r.return;
			while (r);
			var i = n;
		} catch (e) {
			i = "\nError generating stack: " + e.message + "\n" + e.stack;
		}
		return {
			value: e,
			source: t,
			stack: i,
			digest: null
		};
	}
	function As(e, t, n) {
		return {
			value: e,
			source: null,
			stack: n == null ? null : n,
			digest: t == null ? null : t
		};
	}
	function js(e, t) {
		try {
			console.error(t.value);
		} catch (e) {
			setTimeout(function() {
				throw e;
			});
		}
	}
	var Ms = typeof WeakMap == "function" ? WeakMap : Map;
	function Ns(e, t, n) {
		n = oo(-1, n), n.tag = 3, n.payload = { element: null };
		var r = t.value;
		return n.callback = function() {
			cl || (cl = !0, ll = r), js(e, t);
		}, n;
	}
	function Ps(e, t, n) {
		n = oo(-1, n), n.tag = 3;
		var r = e.type.getDerivedStateFromError;
		if (typeof r == "function") {
			var i = t.value;
			n.payload = function() {
				return r(i);
			}, n.callback = function() {
				js(e, t);
			};
		}
		var a = e.stateNode;
		return a !== null && typeof a.componentDidCatch == "function" && (n.callback = function() {
			js(e, t), typeof r != "function" && (ul === null ? ul = /* @__PURE__ */ new Set([this]) : ul.add(this));
			var n = t.stack;
			this.componentDidCatch(t.value, { componentStack: n === null ? "" : n });
		}), n;
	}
	function Fs(e, t, n) {
		var r = e.pingCache;
		if (r === null) {
			r = e.pingCache = new Ms();
			var i = /* @__PURE__ */ new Set();
			r.set(t, i);
		} else i = r.get(t), i === void 0 && (i = /* @__PURE__ */ new Set(), r.set(t, i));
		i.has(n) || (i.add(n), e = Gl.bind(null, e, t, n), t.then(e, e));
	}
	function Is(e) {
		do {
			var t;
			if ((t = e.tag === 13) && (t = e.memoizedState, t = t === null || t.dehydrated !== null), t) return e;
			e = e.return;
		} while (e !== null);
		return null;
	}
	function Ls(e, t, n, r, i) {
		return e.mode & 1 ? (e.flags |= 65536, e.lanes = i, e) : (e === t ? e.flags |= 65536 : (e.flags |= 128, n.flags |= 131072, n.flags &= -52805, n.tag === 1 && (n.alternate === null ? n.tag = 17 : (t = oo(-1, 1), t.tag = 2, so(n, t, 1))), n.lanes |= 1), e);
	}
	var Rs = C.ReactCurrentOwner, zs = !1;
	function Bs(e, t, n, r) {
		t.child = e === null ? Wa(t, null, n, r) : Ua(t, e.child, n, r);
	}
	function Vs(e, t, n, r, i) {
		n = n.render;
		var a = t.ref;
		return Za(t, i), r = Ro(e, t, n, r, a, i), n = zo(), e !== null && !zs ? (t.updateQueue = e.updateQueue, t.flags &= -2053, e.lanes &= ~i, sc(e, t, i)) : (V && n && wa(t), t.flags |= 1, Bs(e, t, r, i), t.child);
	}
	function Hs(e, t, n, r, i) {
		if (e === null) {
			var a = n.type;
			return typeof a == "function" && !$l(a) && a.defaultProps === void 0 && n.compare === null && n.defaultProps === void 0 ? (t.tag = 15, t.type = a, Us(e, t, a, r, i)) : (e = nu(n.type, null, r, t, t.mode, i), e.ref = t.ref, e.return = t, t.child = e);
		}
		if (a = e.child, (e.lanes & i) === 0) {
			var o = a.memoizedProps;
			if (n = n.compare, n = n === null ? Pr : n, n(o, r) && e.ref === t.ref) return sc(e, t, i);
		}
		return t.flags |= 1, e = tu(a, r), e.ref = t.ref, e.return = t, t.child = e;
	}
	function Us(e, t, n, r, i) {
		if (e !== null) {
			var a = e.memoizedProps;
			if (Pr(a, r) && e.ref === t.ref) if (zs = !1, t.pendingProps = r = a, (e.lanes & i) !== 0) e.flags & 131072 && (zs = !0);
			else return t.lanes = e.lanes, sc(e, t, i);
		}
		return Ks(e, t, n, r, i);
	}
	function Ws(e, t, n) {
		var r = t.pendingProps, i = r.children, a = e === null ? null : e.memoizedState;
		if (r.mode === "hidden") if (!(t.mode & 1)) t.memoizedState = {
			baseLanes: 0,
			cachePool: null,
			transitions: null
		}, B(Zc, Xc), Xc |= n;
		else {
			if (!(n & 1073741824)) return e = a === null ? n : a.baseLanes | n, t.lanes = t.childLanes = 1073741824, t.memoizedState = {
				baseLanes: e,
				cachePool: null,
				transitions: null
			}, t.updateQueue = null, B(Zc, Xc), Xc |= e, null;
			t.memoizedState = {
				baseLanes: 0,
				cachePool: null,
				transitions: null
			}, r = a === null ? n : a.baseLanes, B(Zc, Xc), Xc |= r;
		}
		else a === null ? r = n : (r = a.baseLanes | n, t.memoizedState = null), B(Zc, Xc), Xc |= r;
		return Bs(e, t, i, n), t.child;
	}
	function Gs(e, t) {
		var n = t.ref;
		(e === null && n !== null || e !== null && e.ref !== n) && (t.flags |= 512, t.flags |= 2097152);
	}
	function Ks(e, t, n, r, i) {
		var a = ta(n) ? $i : Zi.current;
		return a = ea(t, a), Za(t, i), n = Ro(e, t, n, r, a, i), r = zo(), e !== null && !zs ? (t.updateQueue = e.updateQueue, t.flags &= -2053, e.lanes &= ~i, sc(e, t, i)) : (V && r && wa(t), t.flags |= 1, Bs(e, t, n, i), t.child);
	}
	function qs(e, t, n, r, i) {
		if (ta(n)) {
			var a = !0;
			aa(t);
		} else a = !1;
		if (Za(t, i), t.stateNode === null) oc(e, t), Es(t, n, r), Os(t, n, r, i), r = !0;
		else if (e === null) {
			var o = t.stateNode, s = t.memoizedProps;
			o.props = s;
			var c = o.context, l = n.contextType;
			typeof l == "object" && l ? l = Qa(l) : (l = ta(n) ? $i : Zi.current, l = ea(t, l));
			var u = n.getDerivedStateFromProps, d = typeof u == "function" || typeof o.getSnapshotBeforeUpdate == "function";
			d || typeof o.UNSAFE_componentWillReceiveProps != "function" && typeof o.componentWillReceiveProps != "function" || (s !== r || c !== l) && Ds(t, o, r, l), ro = !1;
			var f = t.memoizedState;
			o.state = f, uo(t, r, o, i), c = t.memoizedState, s !== r || f !== c || Qi.current || ro ? (typeof u == "function" && (Cs(t, n, u, r), c = t.memoizedState), (s = ro || Ts(t, n, s, r, f, c, l)) ? (d || typeof o.UNSAFE_componentWillMount != "function" && typeof o.componentWillMount != "function" || (typeof o.componentWillMount == "function" && o.componentWillMount(), typeof o.UNSAFE_componentWillMount == "function" && o.UNSAFE_componentWillMount()), typeof o.componentDidMount == "function" && (t.flags |= 4194308)) : (typeof o.componentDidMount == "function" && (t.flags |= 4194308), t.memoizedProps = r, t.memoizedState = c), o.props = r, o.state = c, o.context = l, r = s) : (typeof o.componentDidMount == "function" && (t.flags |= 4194308), r = !1);
		} else {
			o = t.stateNode, ao(e, t), s = t.memoizedProps, l = t.type === t.elementType ? s : W(t.type, s), o.props = l, d = t.pendingProps, f = o.context, c = n.contextType, typeof c == "object" && c ? c = Qa(c) : (c = ta(n) ? $i : Zi.current, c = ea(t, c));
			var p = n.getDerivedStateFromProps;
			(u = typeof p == "function" || typeof o.getSnapshotBeforeUpdate == "function") || typeof o.UNSAFE_componentWillReceiveProps != "function" && typeof o.componentWillReceiveProps != "function" || (s !== d || f !== c) && Ds(t, o, r, c), ro = !1, f = t.memoizedState, o.state = f, uo(t, r, o, i);
			var m = t.memoizedState;
			s !== d || f !== m || Qi.current || ro ? (typeof p == "function" && (Cs(t, n, p, r), m = t.memoizedState), (l = ro || Ts(t, n, l, r, f, m, c) || !1) ? (u || typeof o.UNSAFE_componentWillUpdate != "function" && typeof o.componentWillUpdate != "function" || (typeof o.componentWillUpdate == "function" && o.componentWillUpdate(r, m, c), typeof o.UNSAFE_componentWillUpdate == "function" && o.UNSAFE_componentWillUpdate(r, m, c)), typeof o.componentDidUpdate == "function" && (t.flags |= 4), typeof o.getSnapshotBeforeUpdate == "function" && (t.flags |= 1024)) : (typeof o.componentDidUpdate != "function" || s === e.memoizedProps && f === e.memoizedState || (t.flags |= 4), typeof o.getSnapshotBeforeUpdate != "function" || s === e.memoizedProps && f === e.memoizedState || (t.flags |= 1024), t.memoizedProps = r, t.memoizedState = m), o.props = r, o.state = m, o.context = c, r = l) : (typeof o.componentDidUpdate != "function" || s === e.memoizedProps && f === e.memoizedState || (t.flags |= 4), typeof o.getSnapshotBeforeUpdate != "function" || s === e.memoizedProps && f === e.memoizedState || (t.flags |= 1024), r = !1);
		}
		return Js(e, t, n, r, a, i);
	}
	function Js(e, t, n, r, i, a) {
		Gs(e, t);
		var o = (t.flags & 128) != 0;
		if (!r && !o) return i && oa(t, n, !1), sc(e, t, a);
		r = t.stateNode, Rs.current = t;
		var s = o && typeof n.getDerivedStateFromError != "function" ? null : r.render();
		return t.flags |= 1, e !== null && o ? (t.child = Ua(t, e.child, null, a), t.child = Ua(t, null, s, a)) : Bs(e, t, s, a), t.memoizedState = r.state, i && oa(t, n, !0), t.child;
	}
	function Ys(e) {
		var t = e.stateNode;
		t.pendingContext ? ra(e, t.pendingContext, t.pendingContext !== t.context) : t.context && ra(e, t.context, !1), vo(e, t.containerInfo);
	}
	function Xs(e, t, n, r, i) {
		return Ia(), La(i), t.flags |= 256, Bs(e, t, n, r), t.child;
	}
	var Zs = {
		dehydrated: null,
		treeContext: null,
		retryLane: 0
	};
	function Qs(e) {
		return {
			baseLanes: e,
			cachePool: null,
			transitions: null
		};
	}
	function $s(e, t, n) {
		var r = t.pendingProps, i = So.current, a = !1, o = (t.flags & 128) != 0, s;
		if ((s = o) || (s = e !== null && e.memoizedState === null ? !1 : (i & 2) != 0), s ? (a = !0, t.flags &= -129) : (e === null || e.memoizedState !== null) && (i |= 1), B(So, i & 1), e === null) return Ma(t), e = t.memoizedState, e !== null && (e = e.dehydrated, e !== null) ? (t.mode & 1 ? e.data === "$!" ? t.lanes = 8 : t.lanes = 1073741824 : t.lanes = 1, null) : (o = r.children, e = r.fallback, a ? (r = t.mode, a = t.child, o = {
			mode: "hidden",
			children: o
		}, !(r & 1) && a !== null ? (a.childLanes = 0, a.pendingProps = o) : a = iu(o, r, 0, null), e = ru(e, r, n, null), a.return = t, e.return = t, a.sibling = e, t.child = a, t.child.memoizedState = Qs(n), t.memoizedState = Zs, e) : ec(t, o));
		if (i = e.memoizedState, i !== null && (s = i.dehydrated, s !== null)) return nc(e, t, o, r, s, i, n);
		if (a) {
			a = r.fallback, o = t.mode, i = e.child, s = i.sibling;
			var c = {
				mode: "hidden",
				children: r.children
			};
			return !(o & 1) && t.child !== i ? (r = t.child, r.childLanes = 0, r.pendingProps = c, t.deletions = null) : (r = tu(i, c), r.subtreeFlags = i.subtreeFlags & 14680064), s === null ? (a = ru(a, o, n, null), a.flags |= 2) : a = tu(s, a), a.return = t, r.return = t, r.sibling = a, t.child = r, r = a, a = t.child, o = e.child.memoizedState, o = o === null ? Qs(n) : {
				baseLanes: o.baseLanes | n,
				cachePool: null,
				transitions: o.transitions
			}, a.memoizedState = o, a.childLanes = e.childLanes & ~n, t.memoizedState = Zs, r;
		}
		return a = e.child, e = a.sibling, r = tu(a, {
			mode: "visible",
			children: r.children
		}), !(t.mode & 1) && (r.lanes = n), r.return = t, r.sibling = null, e !== null && (n = t.deletions, n === null ? (t.deletions = [e], t.flags |= 16) : n.push(e)), t.child = r, t.memoizedState = null, r;
	}
	function ec(e, t) {
		return t = iu({
			mode: "visible",
			children: t
		}, e.mode, 0, null), t.return = e, e.child = t;
	}
	function tc(e, t, n, r) {
		return r !== null && La(r), Ua(t, e.child, null, n), e = ec(t, t.pendingProps.children), e.flags |= 2, t.memoizedState = null, e;
	}
	function nc(e, t, n, i, a, o, s) {
		if (n) return t.flags & 256 ? (t.flags &= -257, i = As(Error(r(422))), tc(e, t, s, i)) : t.memoizedState === null ? (o = i.fallback, a = t.mode, i = iu({
			mode: "visible",
			children: i.children
		}, a, 0, null), o = ru(o, a, s, null), o.flags |= 2, i.return = t, o.return = t, i.sibling = o, t.child = i, t.mode & 1 && Ua(t, e.child, null, s), t.child.memoizedState = Qs(s), t.memoizedState = Zs, o) : (t.child = e.child, t.flags |= 128, null);
		if (!(t.mode & 1)) return tc(e, t, s, null);
		if (a.data === "$!") {
			if (i = a.nextSibling && a.nextSibling.dataset, i) var c = i.dgst;
			return i = c, o = Error(r(419)), i = As(o, i, void 0), tc(e, t, s, i);
		}
		if (c = (s & e.childLanes) !== 0, zs || c) {
			if (i = q, i !== null) {
				switch (s & -s) {
					case 4:
						a = 2;
						break;
					case 16:
						a = 8;
						break;
					case 64:
					case 128:
					case 256:
					case 512:
					case 1024:
					case 2048:
					case 4096:
					case 8192:
					case 16384:
					case 32768:
					case 65536:
					case 131072:
					case 262144:
					case 524288:
					case 1048576:
					case 2097152:
					case 4194304:
					case 8388608:
					case 16777216:
					case 33554432:
					case 67108864:
						a = 32;
						break;
					case 536870912:
						a = 268435456;
						break;
					default: a = 0;
				}
				a = (a & (i.suspendedLanes | s)) === 0 ? a : 0, a !== 0 && a !== o.retryLane && (o.retryLane = a, no(e, a), bl(i, e, a, -1));
			}
			return Pl(), i = As(Error(r(421))), tc(e, t, s, i);
		}
		return a.data === "$?" ? (t.flags |= 128, t.child = e.child, t = ql.bind(null, e), a._reactRetry = t, null) : (e = o.treeContext, Da = Pi(a.nextSibling), Ea = t, V = !0, Oa = null, e !== null && (_a[va++] = ba, _a[va++] = xa, _a[va++] = ya, ba = e.id, xa = e.overflow, ya = t), t = ec(t, i.children), t.flags |= 4096, t);
	}
	function rc(e, t, n) {
		e.lanes |= t;
		var r = e.alternate;
		r !== null && (r.lanes |= t), Xa(e.return, t, n);
	}
	function ic(e, t, n, r, i) {
		var a = e.memoizedState;
		a === null ? e.memoizedState = {
			isBackwards: t,
			rendering: null,
			renderingStartTime: 0,
			last: r,
			tail: n,
			tailMode: i
		} : (a.isBackwards = t, a.rendering = null, a.renderingStartTime = 0, a.last = r, a.tail = n, a.tailMode = i);
	}
	function ac(e, t, n) {
		var r = t.pendingProps, i = r.revealOrder, a = r.tail;
		if (Bs(e, t, r.children, n), r = So.current, r & 2) r = r & 1 | 2, t.flags |= 128;
		else {
			if (e !== null && e.flags & 128) a: for (e = t.child; e !== null;) {
				if (e.tag === 13) e.memoizedState !== null && rc(e, n, t);
				else if (e.tag === 19) rc(e, n, t);
				else if (e.child !== null) {
					e.child.return = e, e = e.child;
					continue;
				}
				if (e === t) break a;
				for (; e.sibling === null;) {
					if (e.return === null || e.return === t) break a;
					e = e.return;
				}
				e.sibling.return = e.return, e = e.sibling;
			}
			r &= 1;
		}
		if (B(So, r), !(t.mode & 1)) t.memoizedState = null;
		else switch (i) {
			case "forwards":
				for (n = t.child, i = null; n !== null;) e = n.alternate, e !== null && Co(e) === null && (i = n), n = n.sibling;
				n = i, n === null ? (i = t.child, t.child = null) : (i = n.sibling, n.sibling = null), ic(t, !1, i, n, a);
				break;
			case "backwards":
				for (n = null, i = t.child, t.child = null; i !== null;) {
					if (e = i.alternate, e !== null && Co(e) === null) {
						t.child = i;
						break;
					}
					e = i.sibling, i.sibling = n, n = i, i = e;
				}
				ic(t, !0, n, null, a);
				break;
			case "together":
				ic(t, !1, null, null, void 0);
				break;
			default: t.memoizedState = null;
		}
		return t.child;
	}
	function oc(e, t) {
		!(t.mode & 1) && e !== null && (e.alternate = null, t.alternate = null, t.flags |= 2);
	}
	function sc(e, t, n) {
		if (e !== null && (t.dependencies = e.dependencies), el |= t.lanes, (n & t.childLanes) === 0) return null;
		if (e !== null && t.child !== e.child) throw Error(r(153));
		if (t.child !== null) {
			for (e = t.child, n = tu(e, e.pendingProps), t.child = n, n.return = t; e.sibling !== null;) e = e.sibling, n = n.sibling = tu(e, e.pendingProps), n.return = t;
			n.sibling = null;
		}
		return t.child;
	}
	function cc(e, t, n) {
		switch (t.tag) {
			case 3:
				Ys(t), Ia();
				break;
			case 5:
				bo(t);
				break;
			case 1:
				ta(t.type) && aa(t);
				break;
			case 4:
				vo(t, t.stateNode.containerInfo);
				break;
			case 10:
				var r = t.type._context, i = t.memoizedProps.value;
				B(Ga, r._currentValue), r._currentValue = i;
				break;
			case 13:
				if (r = t.memoizedState, r !== null) return r.dehydrated === null ? (n & t.child.childLanes) === 0 ? (B(So, So.current & 1), e = sc(e, t, n), e === null ? null : e.sibling) : $s(e, t, n) : (B(So, So.current & 1), t.flags |= 128, null);
				B(So, So.current & 1);
				break;
			case 19:
				if (r = (n & t.childLanes) !== 0, e.flags & 128) {
					if (r) return ac(e, t, n);
					t.flags |= 128;
				}
				if (i = t.memoizedState, i !== null && (i.rendering = null, i.tail = null, i.lastEffect = null), B(So, So.current), r) break;
				return null;
			case 22:
			case 23: return t.lanes = 0, Ws(e, t, n);
		}
		return sc(e, t, n);
	}
	var lc = function(e, t) {
		for (var n = t.child; n !== null;) {
			if (n.tag === 5 || n.tag === 6) e.appendChild(n.stateNode);
			else if (n.tag !== 4 && n.child !== null) {
				n.child.return = n, n = n.child;
				continue;
			}
			if (n === t) break;
			for (; n.sibling === null;) {
				if (n.return === null || n.return === t) return;
				n = n.return;
			}
			n.sibling.return = n.return, n = n.sibling;
		}
	}, uc = function(e, t, n, r) {
		var i = e.memoizedProps;
		if (i !== r) {
			e = t.stateNode, _o(mo.current);
			var o = null;
			switch (n) {
				case "input":
					i = ve(e, i), r = ve(e, r), o = [];
					break;
				case "select":
					i = ie({}, i, { value: void 0 }), r = ie({}, r, { value: void 0 }), o = [];
					break;
				case "textarea":
					i = Ee(e, i), r = Ee(e, r), o = [];
					break;
				default: typeof i.onClick != "function" && typeof r.onClick == "function" && (e.onclick = wi);
			}
			Be(n, r);
			var s;
			for (u in n = null, i) if (!r.hasOwnProperty(u) && i.hasOwnProperty(u) && i[u] != null) if (u === "style") {
				var c = i[u];
				for (s in c) c.hasOwnProperty(s) && (n || (n = {}), n[s] = "");
			} else u !== "dangerouslySetInnerHTML" && u !== "children" && u !== "suppressContentEditableWarning" && u !== "suppressHydrationWarning" && u !== "autoFocus" && (a.hasOwnProperty(u) ? o || (o = []) : (o = o || []).push(u, null));
			for (u in r) {
				var l = r[u];
				if (c = i == null ? void 0 : i[u], r.hasOwnProperty(u) && l !== c && (l != null || c != null)) if (u === "style") if (c) {
					for (s in c) !c.hasOwnProperty(s) || l && l.hasOwnProperty(s) || (n || (n = {}), n[s] = "");
					for (s in l) l.hasOwnProperty(s) && c[s] !== l[s] && (n || (n = {}), n[s] = l[s]);
				} else n || (o || (o = []), o.push(u, n)), n = l;
				else u === "dangerouslySetInnerHTML" ? (l = l ? l.__html : void 0, c = c ? c.__html : void 0, l != null && c !== l && (o = o || []).push(u, l)) : u === "children" ? typeof l != "string" && typeof l != "number" || (o = o || []).push(u, "" + l) : u !== "suppressContentEditableWarning" && u !== "suppressHydrationWarning" && (a.hasOwnProperty(u) ? (l != null && u === "onScroll" && ui("scroll", e), o || c === l || (o = [])) : (o = o || []).push(u, l));
			}
			n && (o = o || []).push("style", n);
			var u = o;
			(t.updateQueue = u) && (t.flags |= 4);
		}
	}, dc = function(e, t, n, r) {
		n !== r && (t.flags |= 4);
	};
	function fc(e, t) {
		if (!V) switch (e.tailMode) {
			case "hidden":
				t = e.tail;
				for (var n = null; t !== null;) t.alternate !== null && (n = t), t = t.sibling;
				n === null ? e.tail = null : n.sibling = null;
				break;
			case "collapsed":
				n = e.tail;
				for (var r = null; n !== null;) n.alternate !== null && (r = n), n = n.sibling;
				r === null ? t || e.tail === null ? e.tail = null : e.tail.sibling = null : r.sibling = null;
		}
	}
	function pc(e) {
		var t = e.alternate !== null && e.alternate.child === e.child, n = 0, r = 0;
		if (t) for (var i = e.child; i !== null;) n |= i.lanes | i.childLanes, r |= i.subtreeFlags & 14680064, r |= i.flags & 14680064, i.return = e, i = i.sibling;
		else for (i = e.child; i !== null;) n |= i.lanes | i.childLanes, r |= i.subtreeFlags, r |= i.flags, i.return = e, i = i.sibling;
		return e.subtreeFlags |= r, e.childLanes = n, t;
	}
	function mc(e, t, n) {
		var i = t.pendingProps;
		switch (Ta(t), t.tag) {
			case 2:
			case 16:
			case 15:
			case 0:
			case 11:
			case 7:
			case 8:
			case 12:
			case 9:
			case 14: return pc(t), null;
			case 1: return ta(t.type) && na(), pc(t), null;
			case 3: return i = t.stateNode, yo(), z(Qi), z(Zi), To(), i.pendingContext && (i.context = i.pendingContext, i.pendingContext = null), (e === null || e.child === null) && (Pa(t) ? t.flags |= 4 : e === null || e.memoizedState.isDehydrated && !(t.flags & 256) || (t.flags |= 1024, Oa !== null && (wl(Oa), Oa = null))), pc(t), null;
			case 5:
				xo(t);
				var o = _o(go.current);
				if (n = t.type, e !== null && t.stateNode != null) uc(e, t, n, i, o), e.ref !== t.ref && (t.flags |= 512, t.flags |= 2097152);
				else {
					if (!i) {
						if (t.stateNode === null) throw Error(r(166));
						return pc(t), null;
					}
					if (e = _o(mo.current), Pa(t)) {
						i = t.stateNode, n = t.type;
						var s = t.memoizedProps;
						switch (i[Li] = t, i[Ri] = s, e = (t.mode & 1) != 0, n) {
							case "dialog":
								ui("cancel", i), ui("close", i);
								break;
							case "iframe":
							case "object":
							case "embed":
								ui("load", i);
								break;
							case "video":
							case "audio":
								for (o = 0; o < oi.length; o++) ui(oi[o], i);
								break;
							case "source":
								ui("error", i);
								break;
							case "img":
							case "image":
							case "link":
								ui("error", i), ui("load", i);
								break;
							case "details":
								ui("toggle", i);
								break;
							case "input":
								ye(i, s), ui("invalid", i);
								break;
							case "select":
								i._wrapperState = { wasMultiple: !!s.multiple }, ui("invalid", i);
								break;
							case "textarea": De(i, s), ui("invalid", i);
						}
						for (var c in Be(n, s), o = null, s) if (s.hasOwnProperty(c)) {
							var l = s[c];
							c === "children" ? typeof l == "string" ? i.textContent !== l && (!0 !== s.suppressHydrationWarning && Ci(i.textContent, l, e), o = ["children", l]) : typeof l == "number" && i.textContent !== "" + l && (!0 !== s.suppressHydrationWarning && Ci(i.textContent, l, e), o = ["children", "" + l]) : a.hasOwnProperty(c) && l != null && c === "onScroll" && ui("scroll", i);
						}
						switch (n) {
							case "input":
								he(i), Se(i, s, !0);
								break;
							case "textarea":
								he(i), ke(i);
								break;
							case "select":
							case "option": break;
							default: typeof s.onClick == "function" && (i.onclick = wi);
						}
						i = o, t.updateQueue = i, i !== null && (t.flags |= 4);
					} else {
						c = o.nodeType === 9 ? o : o.ownerDocument, e === "http://www.w3.org/1999/xhtml" && (e = Ae(n)), e === "http://www.w3.org/1999/xhtml" ? n === "script" ? (e = c.createElement("div"), e.innerHTML = "<script><\/script>", e = e.removeChild(e.firstChild)) : typeof i.is == "string" ? e = c.createElement(n, { is: i.is }) : (e = c.createElement(n), n === "select" && (c = e, i.multiple ? c.multiple = !0 : i.size && (c.size = i.size))) : e = c.createElementNS(e, n), e[Li] = t, e[Ri] = i, lc(e, t, !1, !1), t.stateNode = e;
						a: {
							switch (c = Ve(n, i), n) {
								case "dialog":
									ui("cancel", e), ui("close", e), o = i;
									break;
								case "iframe":
								case "object":
								case "embed":
									ui("load", e), o = i;
									break;
								case "video":
								case "audio":
									for (o = 0; o < oi.length; o++) ui(oi[o], e);
									o = i;
									break;
								case "source":
									ui("error", e), o = i;
									break;
								case "img":
								case "image":
								case "link":
									ui("error", e), ui("load", e), o = i;
									break;
								case "details":
									ui("toggle", e), o = i;
									break;
								case "input":
									ye(e, i), o = ve(e, i), ui("invalid", e);
									break;
								case "option":
									o = i;
									break;
								case "select":
									e._wrapperState = { wasMultiple: !!i.multiple }, o = ie({}, i, { value: void 0 }), ui("invalid", e);
									break;
								case "textarea":
									De(e, i), o = Ee(e, i), ui("invalid", e);
									break;
								default: o = i;
							}
							for (s in Be(n, o), l = o, l) if (l.hasOwnProperty(s)) {
								var u = l[s];
								s === "style" ? Re(e, u) : s === "dangerouslySetInnerHTML" ? (u = u ? u.__html : void 0, u != null && Ne(e, u)) : s === "children" ? typeof u == "string" ? (n !== "textarea" || u !== "") && Pe(e, u) : typeof u == "number" && Pe(e, "" + u) : s !== "suppressContentEditableWarning" && s !== "suppressHydrationWarning" && s !== "autoFocus" && (a.hasOwnProperty(s) ? u != null && s === "onScroll" && ui("scroll", e) : u != null && S(e, s, u, c));
							}
							switch (n) {
								case "input":
									he(e), Se(e, i, !1);
									break;
								case "textarea":
									he(e), ke(e);
									break;
								case "option":
									i.value != null && e.setAttribute("value", "" + fe(i.value));
									break;
								case "select":
									e.multiple = !!i.multiple, s = i.value, s == null ? i.defaultValue != null && Te(e, !!i.multiple, i.defaultValue, !0) : Te(e, !!i.multiple, s, !1);
									break;
								default: typeof o.onClick == "function" && (e.onclick = wi);
							}
							switch (n) {
								case "button":
								case "input":
								case "select":
								case "textarea":
									i = !!i.autoFocus;
									break a;
								case "img":
									i = !0;
									break a;
								default: i = !1;
							}
						}
						i && (t.flags |= 4);
					}
					t.ref !== null && (t.flags |= 512, t.flags |= 2097152);
				}
				return pc(t), null;
			case 6:
				if (e && t.stateNode != null) dc(e, t, e.memoizedProps, i);
				else {
					if (typeof i != "string" && t.stateNode === null) throw Error(r(166));
					if (n = _o(go.current), _o(mo.current), Pa(t)) {
						if (i = t.stateNode, n = t.memoizedProps, i[Li] = t, (s = i.nodeValue !== n) && (e = Ea, e !== null)) switch (e.tag) {
							case 3:
								Ci(i.nodeValue, n, (e.mode & 1) != 0);
								break;
							case 5: !0 !== e.memoizedProps.suppressHydrationWarning && Ci(i.nodeValue, n, (e.mode & 1) != 0);
						}
						s && (t.flags |= 4);
					} else i = (n.nodeType === 9 ? n : n.ownerDocument).createTextNode(i), i[Li] = t, t.stateNode = i;
				}
				return pc(t), null;
			case 13:
				if (z(So), i = t.memoizedState, e === null || e.memoizedState !== null && e.memoizedState.dehydrated !== null) {
					if (V && Da !== null && t.mode & 1 && !(t.flags & 128)) Fa(), Ia(), t.flags |= 98560, s = !1;
					else if (s = Pa(t), i !== null && i.dehydrated !== null) {
						if (e === null) {
							if (!s) throw Error(r(318));
							if (s = t.memoizedState, s = s === null ? null : s.dehydrated, !s) throw Error(r(317));
							s[Li] = t;
						} else Ia(), !(t.flags & 128) && (t.memoizedState = null), t.flags |= 4;
						pc(t), s = !1;
					} else Oa !== null && (wl(Oa), Oa = null), s = !0;
					if (!s) return t.flags & 65536 ? t : null;
				}
				return t.flags & 128 ? (t.lanes = n, t) : (i = i !== null, i !== (e !== null && e.memoizedState !== null) && i && (t.child.flags |= 8192, t.mode & 1 && (e === null || So.current & 1 ? Qc === 0 && (Qc = 3) : Pl())), t.updateQueue !== null && (t.flags |= 4), pc(t), null);
			case 4: return yo(), e === null && pi(t.stateNode.containerInfo), pc(t), null;
			case 10: return Ya(t.type._context), pc(t), null;
			case 17: return ta(t.type) && na(), pc(t), null;
			case 19:
				if (z(So), s = t.memoizedState, s === null) return pc(t), null;
				if (i = (t.flags & 128) != 0, c = s.rendering, c === null) if (i) fc(s, !1);
				else {
					if (Qc !== 0 || e !== null && e.flags & 128) for (e = t.child; e !== null;) {
						if (c = Co(e), c !== null) {
							for (t.flags |= 128, fc(s, !1), i = c.updateQueue, i !== null && (t.updateQueue = i, t.flags |= 4), t.subtreeFlags = 0, i = n, n = t.child; n !== null;) s = n, e = i, s.flags &= 14680066, c = s.alternate, c === null ? (s.childLanes = 0, s.lanes = e, s.child = null, s.subtreeFlags = 0, s.memoizedProps = null, s.memoizedState = null, s.updateQueue = null, s.dependencies = null, s.stateNode = null) : (s.childLanes = c.childLanes, s.lanes = c.lanes, s.child = c.child, s.subtreeFlags = 0, s.deletions = null, s.memoizedProps = c.memoizedProps, s.memoizedState = c.memoizedState, s.updateQueue = c.updateQueue, s.type = c.type, e = c.dependencies, s.dependencies = e === null ? null : {
								lanes: e.lanes,
								firstContext: e.firstContext
							}), n = n.sibling;
							return B(So, So.current & 1 | 2), t.child;
						}
						e = e.sibling;
					}
					s.tail !== null && xt() > ol && (t.flags |= 128, i = !0, fc(s, !1), t.lanes = 4194304);
				}
				else {
					if (!i) if (e = Co(c), e !== null) {
						if (t.flags |= 128, i = !0, n = e.updateQueue, n !== null && (t.updateQueue = n, t.flags |= 4), fc(s, !0), s.tail === null && s.tailMode === "hidden" && !c.alternate && !V) return pc(t), null;
					} else 2 * xt() - s.renderingStartTime > ol && n !== 1073741824 && (t.flags |= 128, i = !0, fc(s, !1), t.lanes = 4194304);
					s.isBackwards ? (c.sibling = t.child, t.child = c) : (n = s.last, n === null ? t.child = c : n.sibling = c, s.last = c);
				}
				return s.tail === null ? (pc(t), null) : (t = s.tail, s.rendering = t, s.tail = t.sibling, s.renderingStartTime = xt(), t.sibling = null, n = So.current, B(So, i ? n & 1 | 2 : n & 1), t);
			case 22:
			case 23: return Al(), i = t.memoizedState !== null, e !== null && e.memoizedState !== null !== i && (t.flags |= 8192), i && t.mode & 1 ? Xc & 1073741824 && (pc(t), t.subtreeFlags & 6 && (t.flags |= 8192)) : pc(t), null;
			case 24: return null;
			case 25: return null;
		}
		throw Error(r(156, t.tag));
	}
	function hc(e, t) {
		switch (Ta(t), t.tag) {
			case 1: return ta(t.type) && na(), e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
			case 3: return yo(), z(Qi), z(Zi), To(), e = t.flags, e & 65536 && !(e & 128) ? (t.flags = e & -65537 | 128, t) : null;
			case 5: return xo(t), null;
			case 13:
				if (z(So), e = t.memoizedState, e !== null && e.dehydrated !== null) {
					if (t.alternate === null) throw Error(r(340));
					Ia();
				}
				return e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
			case 19: return z(So), null;
			case 4: return yo(), null;
			case 10: return Ya(t.type._context), null;
			case 22:
			case 23: return Al(), null;
			case 24: return null;
			default: return null;
		}
	}
	var gc = !1, _c = !1, vc = typeof WeakSet == "function" ? WeakSet : Set, G = null;
	function yc(e, t) {
		var n = e.ref;
		if (n !== null) if (typeof n == "function") try {
			n(null);
		} catch (n) {
			Wl(e, t, n);
		}
		else n.current = null;
	}
	function bc(e, t, n) {
		try {
			n();
		} catch (n) {
			Wl(e, t, n);
		}
	}
	var xc = !1;
	function Sc(e, t) {
		if (Ti = vn, e = Rr(), zr(e)) {
			if ("selectionStart" in e) var n = {
				start: e.selectionStart,
				end: e.selectionEnd
			};
			else a: {
				n = (n = e.ownerDocument) && n.defaultView || window;
				var i = n.getSelection && n.getSelection();
				if (i && i.rangeCount !== 0) {
					n = i.anchorNode;
					var a = i.anchorOffset, o = i.focusNode;
					i = i.focusOffset;
					try {
						n.nodeType, o.nodeType;
					} catch (e) {
						n = null;
						break a;
					}
					var s = 0, c = -1, l = -1, u = 0, d = 0, f = e, p = null;
					b: for (;;) {
						for (var m; f !== n || a !== 0 && f.nodeType !== 3 || (c = s + a), f !== o || i !== 0 && f.nodeType !== 3 || (l = s + i), f.nodeType === 3 && (s += f.nodeValue.length), (m = f.firstChild) !== null;) p = f, f = m;
						for (;;) {
							if (f === e) break b;
							if (p === n && ++u === a && (c = s), p === o && ++d === i && (l = s), (m = f.nextSibling) !== null) break;
							f = p, p = f.parentNode;
						}
						f = m;
					}
					n = c === -1 || l === -1 ? null : {
						start: c,
						end: l
					};
				} else n = null;
			}
			n = n || {
				start: 0,
				end: 0
			};
		} else n = null;
		for (Ei = {
			focusedElem: e,
			selectionRange: n
		}, vn = !1, G = t; G !== null;) if (t = G, e = t.child, t.subtreeFlags & 1028 && e !== null) e.return = t, G = e;
		else for (; G !== null;) {
			t = G;
			try {
				var h = t.alternate;
				if (t.flags & 1024) switch (t.tag) {
					case 0:
					case 11:
					case 15: break;
					case 1:
						if (h !== null) {
							var g = h.memoizedProps, _ = h.memoizedState, v = t.stateNode;
							v.__reactInternalSnapshotBeforeUpdate = v.getSnapshotBeforeUpdate(t.elementType === t.type ? g : W(t.type, g), _);
						}
						break;
					case 3:
						var y = t.stateNode.containerInfo;
						y.nodeType === 1 ? y.textContent = "" : y.nodeType === 9 && y.documentElement && y.removeChild(y.documentElement);
						break;
					case 5:
					case 6:
					case 4:
					case 17: break;
					default: throw Error(r(163));
				}
			} catch (e) {
				Wl(t, t.return, e);
			}
			if (e = t.sibling, e !== null) {
				e.return = t.return, G = e;
				break;
			}
			G = t.return;
		}
		return h = xc, xc = !1, h;
	}
	function Cc(e, t, n) {
		var r = t.updateQueue;
		if (r = r === null ? null : r.lastEffect, r !== null) {
			var i = r = r.next;
			do {
				if ((i.tag & e) === e) {
					var a = i.destroy;
					i.destroy = void 0, a !== void 0 && bc(t, n, a);
				}
				i = i.next;
			} while (i !== r);
		}
	}
	function wc(e, t) {
		if (t = t.updateQueue, t = t === null ? null : t.lastEffect, t !== null) {
			var n = t = t.next;
			do {
				if ((n.tag & e) === e) {
					var r = n.create;
					n.destroy = r();
				}
				n = n.next;
			} while (n !== t);
		}
	}
	function Tc(e) {
		var t = e.ref;
		if (t !== null) {
			var n = e.stateNode;
			switch (e.tag) {
				case 5:
					e = n;
					break;
				default: e = n;
			}
			typeof t == "function" ? t(e) : t.current = e;
		}
	}
	function Ec(e) {
		var t = e.alternate;
		t !== null && (e.alternate = null, Ec(t)), e.child = null, e.deletions = null, e.sibling = null, e.tag === 5 && (t = e.stateNode, t !== null && (delete t[Li], delete t[Ri], delete t[Bi], delete t[Vi], delete t[Hi])), e.stateNode = null, e.return = null, e.dependencies = null, e.memoizedProps = null, e.memoizedState = null, e.pendingProps = null, e.stateNode = null, e.updateQueue = null;
	}
	function Dc(e) {
		return e.tag === 5 || e.tag === 3 || e.tag === 4;
	}
	function Oc(e) {
		a: for (;;) {
			for (; e.sibling === null;) {
				if (e.return === null || Dc(e.return)) return null;
				e = e.return;
			}
			for (e.sibling.return = e.return, e = e.sibling; e.tag !== 5 && e.tag !== 6 && e.tag !== 18;) {
				if (e.flags & 2 || e.child === null || e.tag === 4) continue a;
				e.child.return = e, e = e.child;
			}
			if (!(e.flags & 2)) return e.stateNode;
		}
	}
	function kc(e, t, n) {
		var r = e.tag;
		if (r === 5 || r === 6) e = e.stateNode, t ? n.nodeType === 8 ? n.parentNode.insertBefore(e, t) : n.insertBefore(e, t) : (n.nodeType === 8 ? (t = n.parentNode, t.insertBefore(e, n)) : (t = n, t.appendChild(e)), n = n._reactRootContainer, n != null || t.onclick !== null || (t.onclick = wi));
		else if (r !== 4 && (e = e.child, e !== null)) for (kc(e, t, n), e = e.sibling; e !== null;) kc(e, t, n), e = e.sibling;
	}
	function Ac(e, t, n) {
		var r = e.tag;
		if (r === 5 || r === 6) e = e.stateNode, t ? n.insertBefore(e, t) : n.appendChild(e);
		else if (r !== 4 && (e = e.child, e !== null)) for (Ac(e, t, n), e = e.sibling; e !== null;) Ac(e, t, n), e = e.sibling;
	}
	var jc = null, Mc = !1;
	function Nc(e, t, n) {
		for (n = n.child; n !== null;) Pc(e, t, n), n = n.sibling;
	}
	function Pc(e, t, n) {
		if (kt && typeof kt.onCommitFiberUnmount == "function") try {
			kt.onCommitFiberUnmount(Ot, n);
		} catch (e) {}
		switch (n.tag) {
			case 5: _c || yc(n, t);
			case 6:
				var r = jc, i = Mc;
				jc = null, Nc(e, t, n), jc = r, Mc = i, jc !== null && (Mc ? (e = jc, n = n.stateNode, e.nodeType === 8 ? e.parentNode.removeChild(n) : e.removeChild(n)) : jc.removeChild(n.stateNode));
				break;
			case 18:
				jc !== null && (Mc ? (e = jc, n = n.stateNode, e.nodeType === 8 ? Ni(e.parentNode, n) : e.nodeType === 1 && Ni(e, n), gn(e)) : Ni(jc, n.stateNode));
				break;
			case 4:
				r = jc, i = Mc, jc = n.stateNode.containerInfo, Mc = !0, Nc(e, t, n), jc = r, Mc = i;
				break;
			case 0:
			case 11:
			case 14:
			case 15:
				if (!_c && (r = n.updateQueue, r !== null && (r = r.lastEffect, r !== null))) {
					i = r = r.next;
					do {
						var a = i, o = a.destroy;
						a = a.tag, o !== void 0 && (a & 2 || a & 4) && bc(n, t, o), i = i.next;
					} while (i !== r);
				}
				Nc(e, t, n);
				break;
			case 1:
				if (!_c && (yc(n, t), r = n.stateNode, typeof r.componentWillUnmount == "function")) try {
					r.props = n.memoizedProps, r.state = n.memoizedState, r.componentWillUnmount();
				} catch (e) {
					Wl(n, t, e);
				}
				Nc(e, t, n);
				break;
			case 21:
				Nc(e, t, n);
				break;
			case 22:
				n.mode & 1 ? (_c = (r = _c) || n.memoizedState !== null, Nc(e, t, n), _c = r) : Nc(e, t, n);
				break;
			default: Nc(e, t, n);
		}
	}
	function Fc(e) {
		var t = e.updateQueue;
		if (t !== null) {
			e.updateQueue = null;
			var n = e.stateNode;
			n === null && (n = e.stateNode = new vc()), t.forEach(function(t) {
				var r = Jl.bind(null, e, t);
				n.has(t) || (n.add(t), t.then(r, r));
			});
		}
	}
	function Ic(e, t) {
		var n = t.deletions;
		if (n !== null) for (var i = 0; i < n.length; i++) {
			var a = n[i];
			try {
				var o = e, s = t, c = s;
				a: for (; c !== null;) {
					switch (c.tag) {
						case 5:
							jc = c.stateNode, Mc = !1;
							break a;
						case 3:
							jc = c.stateNode.containerInfo, Mc = !0;
							break a;
						case 4:
							jc = c.stateNode.containerInfo, Mc = !0;
							break a;
					}
					c = c.return;
				}
				if (jc === null) throw Error(r(160));
				Pc(o, s, a), jc = null, Mc = !1;
				var l = a.alternate;
				l !== null && (l.return = null), a.return = null;
			} catch (e) {
				Wl(a, t, e);
			}
		}
		if (t.subtreeFlags & 12854) for (t = t.child; t !== null;) Lc(t, e), t = t.sibling;
	}
	function Lc(e, t) {
		var n = e.alternate, i = e.flags;
		switch (e.tag) {
			case 0:
			case 11:
			case 14:
			case 15:
				if (Ic(t, e), Rc(e), i & 4) {
					try {
						Cc(3, e, e.return), wc(3, e);
					} catch (t) {
						Wl(e, e.return, t);
					}
					try {
						Cc(5, e, e.return);
					} catch (t) {
						Wl(e, e.return, t);
					}
				}
				break;
			case 1:
				Ic(t, e), Rc(e), i & 512 && n !== null && yc(n, n.return);
				break;
			case 5:
				if (Ic(t, e), Rc(e), i & 512 && n !== null && yc(n, n.return), e.flags & 32) {
					var a = e.stateNode;
					try {
						Pe(a, "");
					} catch (t) {
						Wl(e, e.return, t);
					}
				}
				if (i & 4 && (a = e.stateNode, a != null)) {
					var o = e.memoizedProps, s = n === null ? o : n.memoizedProps, c = e.type, l = e.updateQueue;
					if (e.updateQueue = null, l !== null) try {
						c === "input" && o.type === "radio" && o.name != null && be(a, o), Ve(c, s);
						var u = Ve(c, o);
						for (s = 0; s < l.length; s += 2) {
							var d = l[s], f = l[s + 1];
							d === "style" ? Re(a, f) : d === "dangerouslySetInnerHTML" ? Ne(a, f) : d === "children" ? Pe(a, f) : S(a, d, f, u);
						}
						switch (c) {
							case "input":
								xe(a, o);
								break;
							case "textarea":
								Oe(a, o);
								break;
							case "select":
								var p = a._wrapperState.wasMultiple;
								a._wrapperState.wasMultiple = !!o.multiple;
								var m = o.value;
								m == null ? p !== !!o.multiple && (o.defaultValue == null ? Te(a, !!o.multiple, o.multiple ? [] : "", !1) : Te(a, !!o.multiple, o.defaultValue, !0)) : Te(a, !!o.multiple, m, !1);
						}
						a[Ri] = o;
					} catch (t) {
						Wl(e, e.return, t);
					}
				}
				break;
			case 6:
				if (Ic(t, e), Rc(e), i & 4) {
					if (e.stateNode === null) throw Error(r(162));
					a = e.stateNode, o = e.memoizedProps;
					try {
						a.nodeValue = o;
					} catch (t) {
						Wl(e, e.return, t);
					}
				}
				break;
			case 3:
				if (Ic(t, e), Rc(e), i & 4 && n !== null && n.memoizedState.isDehydrated) try {
					gn(t.containerInfo);
				} catch (t) {
					Wl(e, e.return, t);
				}
				break;
			case 4:
				Ic(t, e), Rc(e);
				break;
			case 13:
				Ic(t, e), Rc(e), a = e.child, a.flags & 8192 && (o = a.memoizedState !== null, a.stateNode.isHidden = o, !o || a.alternate !== null && a.alternate.memoizedState !== null || (al = xt())), i & 4 && Fc(e);
				break;
			case 22:
				if (d = n !== null && n.memoizedState !== null, e.mode & 1 ? (_c = (u = _c) || d, Ic(t, e), _c = u) : Ic(t, e), Rc(e), i & 8192) {
					if (u = e.memoizedState !== null, (e.stateNode.isHidden = u) && !d && e.mode & 1) for (G = e, d = e.child; d !== null;) {
						for (f = G = d; G !== null;) {
							switch (p = G, m = p.child, p.tag) {
								case 0:
								case 11:
								case 14:
								case 15:
									Cc(4, p, p.return);
									break;
								case 1:
									yc(p, p.return);
									var h = p.stateNode;
									if (typeof h.componentWillUnmount == "function") {
										i = p, n = p.return;
										try {
											t = i, h.props = t.memoizedProps, h.state = t.memoizedState, h.componentWillUnmount();
										} catch (e) {
											Wl(i, n, e);
										}
									}
									break;
								case 5:
									yc(p, p.return);
									break;
								case 22: if (p.memoizedState !== null) {
									Hc(f);
									continue;
								}
							}
							m === null ? Hc(f) : (m.return = p, G = m);
						}
						d = d.sibling;
					}
					a: for (d = null, f = e;;) {
						if (f.tag === 5) {
							if (d === null) {
								d = f;
								try {
									a = f.stateNode, u ? (o = a.style, typeof o.setProperty == "function" ? o.setProperty("display", "none", "important") : o.display = "none") : (c = f.stateNode, l = f.memoizedProps.style, s = l != null && l.hasOwnProperty("display") ? l.display : null, c.style.display = Le("display", s));
								} catch (t) {
									Wl(e, e.return, t);
								}
							}
						} else if (f.tag === 6) {
							if (d === null) try {
								f.stateNode.nodeValue = u ? "" : f.memoizedProps;
							} catch (t) {
								Wl(e, e.return, t);
							}
						} else if ((f.tag !== 22 && f.tag !== 23 || f.memoizedState === null || f === e) && f.child !== null) {
							f.child.return = f, f = f.child;
							continue;
						}
						if (f === e) break a;
						for (; f.sibling === null;) {
							if (f.return === null || f.return === e) break a;
							d === f && (d = null), f = f.return;
						}
						d === f && (d = null), f.sibling.return = f.return, f = f.sibling;
					}
				}
				break;
			case 19:
				Ic(t, e), Rc(e), i & 4 && Fc(e);
				break;
			case 21: break;
			default: Ic(t, e), Rc(e);
		}
	}
	function Rc(e) {
		var t = e.flags;
		if (t & 2) {
			try {
				a: {
					for (var n = e.return; n !== null;) {
						if (Dc(n)) {
							var i = n;
							break a;
						}
						n = n.return;
					}
					throw Error(r(160));
				}
				switch (i.tag) {
					case 5:
						var a = i.stateNode;
						i.flags & 32 && (Pe(a, ""), i.flags &= -33), Ac(e, Oc(e), a);
						break;
					case 3:
					case 4:
						var o = i.stateNode.containerInfo;
						kc(e, Oc(e), o);
						break;
					default: throw Error(r(161));
				}
			} catch (t) {
				Wl(e, e.return, t);
			}
			e.flags &= -3;
		}
		t & 4096 && (e.flags &= -4097);
	}
	function zc(e, t, n) {
		G = e, Bc(e, t, n);
	}
	function Bc(e, t, n) {
		for (var r = (e.mode & 1) != 0; G !== null;) {
			var i = G, a = i.child;
			if (i.tag === 22 && r) {
				var o = i.memoizedState !== null || gc;
				if (!o) {
					var s = i.alternate, c = s !== null && s.memoizedState !== null || _c;
					s = gc;
					var l = _c;
					if (gc = o, (_c = c) && !l) for (G = i; G !== null;) o = G, c = o.child, o.tag === 22 && o.memoizedState !== null || c === null ? Uc(i) : (c.return = o, G = c);
					for (; a !== null;) G = a, Bc(a, t, n), a = a.sibling;
					G = i, gc = s, _c = l;
				}
				Vc(e, t, n);
			} else i.subtreeFlags & 8772 && a !== null ? (a.return = i, G = a) : Vc(e, t, n);
		}
	}
	function Vc(e) {
		for (; G !== null;) {
			var t = G;
			if (t.flags & 8772) {
				var n = t.alternate;
				try {
					if (t.flags & 8772) switch (t.tag) {
						case 0:
						case 11:
						case 15:
							_c || wc(5, t);
							break;
						case 1:
							var i = t.stateNode;
							if (t.flags & 4 && !_c) if (n === null) i.componentDidMount();
							else {
								var a = t.elementType === t.type ? n.memoizedProps : W(t.type, n.memoizedProps);
								i.componentDidUpdate(a, n.memoizedState, i.__reactInternalSnapshotBeforeUpdate);
							}
							var o = t.updateQueue;
							o !== null && fo(t, o, i);
							break;
						case 3:
							var s = t.updateQueue;
							if (s !== null) {
								if (n = null, t.child !== null) switch (t.child.tag) {
									case 5:
										n = t.child.stateNode;
										break;
									case 1: n = t.child.stateNode;
								}
								fo(t, s, n);
							}
							break;
						case 5:
							var c = t.stateNode;
							if (n === null && t.flags & 4) {
								n = c;
								var l = t.memoizedProps;
								switch (t.type) {
									case "button":
									case "input":
									case "select":
									case "textarea":
										l.autoFocus && n.focus();
										break;
									case "img": l.src && (n.src = l.src);
								}
							}
							break;
						case 6: break;
						case 4: break;
						case 12: break;
						case 13:
							if (t.memoizedState === null) {
								var u = t.alternate;
								if (u !== null) {
									var d = u.memoizedState;
									if (d !== null) {
										var f = d.dehydrated;
										f !== null && gn(f);
									}
								}
							}
							break;
						case 19:
						case 17:
						case 21:
						case 22:
						case 23:
						case 25: break;
						default: throw Error(r(163));
					}
					_c || t.flags & 512 && Tc(t);
				} catch (e) {
					Wl(t, t.return, e);
				}
			}
			if (t === e) {
				G = null;
				break;
			}
			if (n = t.sibling, n !== null) {
				n.return = t.return, G = n;
				break;
			}
			G = t.return;
		}
	}
	function Hc(e) {
		for (; G !== null;) {
			var t = G;
			if (t === e) {
				G = null;
				break;
			}
			var n = t.sibling;
			if (n !== null) {
				n.return = t.return, G = n;
				break;
			}
			G = t.return;
		}
	}
	function Uc(e) {
		for (; G !== null;) {
			var t = G;
			try {
				switch (t.tag) {
					case 0:
					case 11:
					case 15:
						var n = t.return;
						try {
							wc(4, t);
						} catch (e) {
							Wl(t, n, e);
						}
						break;
					case 1:
						var r = t.stateNode;
						if (typeof r.componentDidMount == "function") {
							var i = t.return;
							try {
								r.componentDidMount();
							} catch (e) {
								Wl(t, i, e);
							}
						}
						var a = t.return;
						try {
							Tc(t);
						} catch (e) {
							Wl(t, a, e);
						}
						break;
					case 5:
						var o = t.return;
						try {
							Tc(t);
						} catch (e) {
							Wl(t, o, e);
						}
				}
			} catch (e) {
				Wl(t, t.return, e);
			}
			if (t === e) {
				G = null;
				break;
			}
			var s = t.sibling;
			if (s !== null) {
				s.return = t.return, G = s;
				break;
			}
			G = t.return;
		}
	}
	var Wc = Math.ceil, Gc = C.ReactCurrentDispatcher, Kc = C.ReactCurrentOwner, qc = C.ReactCurrentBatchConfig, K = 0, q = null, Jc = null, Yc = 0, Xc = 0, Zc = Yi(0), Qc = 0, $c = null, el = 0, tl = 0, nl = 0, rl = null, il = null, al = 0, ol = Infinity, sl = null, cl = !1, ll = null, ul = null, dl = !1, fl = null, pl = 0, ml = 0, hl = null, gl = -1, _l = 0;
	function vl() {
		return K & 6 ? xt() : gl === -1 ? gl = xt() : gl;
	}
	function yl(e) {
		return e.mode & 1 ? K & 2 && Yc !== 0 ? Yc & -Yc : Ra.transition === null ? (e = F, e === 0 ? (e = window.event, e = e === void 0 ? 16 : wn(e.type), e) : e) : (_l === 0 && (_l = Ht()), _l) : 1;
	}
	function bl(e, t, n, i) {
		if (50 < ml) throw ml = 0, hl = null, Error(r(185));
		Wt(e, n, i), (!(K & 2) || e !== q) && (e === q && (!(K & 2) && (tl |= n), Qc === 4 && El(e, Yc)), xl(e, i), n === 1 && K === 0 && !(t.mode & 1) && (ol = xt() + 500, ca && fa()));
	}
	function xl(e, t) {
		var n = e.callbackNode;
		Bt(e, t);
		var r = Rt(e, e === q ? Yc : 0);
		if (r === 0) n !== null && vt(n), e.callbackNode = null, e.callbackPriority = 0;
		else if (t = r & -r, e.callbackPriority !== t) {
			if (n != null && vt(n), t === 1) e.tag === 0 ? da(Dl.bind(null, e)) : ua(Dl.bind(null, e)), ji(function() {
				!(K & 6) && fa();
			}), n = null;
			else {
				switch (I(r)) {
					case 1:
						n = Ct;
						break;
					case 4:
						n = wt;
						break;
					case 16:
						n = Tt;
						break;
					case 536870912:
						n = Dt;
						break;
					default: n = Tt;
				}
				n = Xl(n, Sl.bind(null, e));
			}
			e.callbackPriority = t, e.callbackNode = n;
		}
	}
	function Sl(e, t) {
		if (gl = -1, _l = 0, K & 6) throw Error(r(327));
		var n = e.callbackNode;
		if (Hl() && e.callbackNode !== n) return null;
		var i = Rt(e, e === q ? Yc : 0);
		if (i === 0) return null;
		if (i & 30 || (i & e.expiredLanes) !== 0 || t) t = Fl(e, i);
		else {
			t = i;
			var a = K;
			K |= 2;
			var o = Nl();
			(q !== e || Yc !== t) && (sl = null, ol = xt() + 500, jl(e, t));
			do
				try {
					Ll();
					break;
				} catch (t) {
					Ml(e, t);
				}
			while (1);
			Ja(), Gc.current = o, K = a, Jc === null ? (q = null, Yc = 0, t = Qc) : t = 0;
		}
		if (t !== 0) {
			if (t === 2 && (a = Vt(e), a !== 0 && (i = a, t = Cl(e, a))), t === 1) throw n = $c, jl(e, 0), El(e, i), xl(e, xt()), n;
			if (t === 6) El(e, i);
			else {
				if (a = e.current.alternate, !(i & 30) && !Tl(a) && (t = Fl(e, i), t === 2 && (o = Vt(e), o !== 0 && (i = o, t = Cl(e, o))), t === 1)) throw n = $c, jl(e, 0), El(e, i), xl(e, xt()), n;
				switch (e.finishedWork = a, e.finishedLanes = i, t) {
					case 0:
					case 1: throw Error(r(345));
					case 2:
						Bl(e, il, sl);
						break;
					case 3:
						if (El(e, i), (i & 130023424) === i && (t = al + 500 - xt(), 10 < t)) {
							if (Rt(e, 0) !== 0) break;
							if (a = e.suspendedLanes, (a & i) !== i) {
								vl(), e.pingedLanes |= e.suspendedLanes & a;
								break;
							}
							e.timeoutHandle = Oi(Bl.bind(null, e, il, sl), t);
							break;
						}
						Bl(e, il, sl);
						break;
					case 4:
						if (El(e, i), (i & 4194240) === i) break;
						for (t = e.eventTimes, a = -1; 0 < i;) {
							var s = 31 - jt(i);
							o = 1 << s, s = t[s], s > a && (a = s), i &= ~o;
						}
						if (i = a, i = xt() - i, i = (120 > i ? 120 : 480 > i ? 480 : 1080 > i ? 1080 : 1920 > i ? 1920 : 3e3 > i ? 3e3 : 4320 > i ? 4320 : 1960 * Wc(i / 1960)) - i, 10 < i) {
							e.timeoutHandle = Oi(Bl.bind(null, e, il, sl), i);
							break;
						}
						Bl(e, il, sl);
						break;
					case 5:
						Bl(e, il, sl);
						break;
					default: throw Error(r(329));
				}
			}
		}
		return xl(e, xt()), e.callbackNode === n ? Sl.bind(null, e) : null;
	}
	function Cl(e, t) {
		var n = rl;
		return e.current.memoizedState.isDehydrated && (jl(e, t).flags |= 256), e = Fl(e, t), e !== 2 && (t = il, il = n, t !== null && wl(t)), e;
	}
	function wl(e) {
		il === null ? il = e : il.push.apply(il, e);
	}
	function Tl(e) {
		for (var t = e;;) {
			if (t.flags & 16384) {
				var n = t.updateQueue;
				if (n !== null && (n = n.stores, n !== null)) for (var r = 0; r < n.length; r++) {
					var i = n[r], a = i.getSnapshot;
					i = i.value;
					try {
						if (!Nr(a(), i)) return !1;
					} catch (e) {
						return !1;
					}
				}
			}
			if (n = t.child, t.subtreeFlags & 16384 && n !== null) n.return = t, t = n;
			else {
				if (t === e) break;
				for (; t.sibling === null;) {
					if (t.return === null || t.return === e) return !0;
					t = t.return;
				}
				t.sibling.return = t.return, t = t.sibling;
			}
		}
		return !0;
	}
	function El(e, t) {
		for (t &= ~nl, t &= ~tl, e.suspendedLanes |= t, e.pingedLanes &= ~t, e = e.expirationTimes; 0 < t;) {
			var n = 31 - jt(t), r = 1 << n;
			e[n] = -1, t &= ~r;
		}
	}
	function Dl(e) {
		if (K & 6) throw Error(r(327));
		Hl();
		var t = Rt(e, 0);
		if (!(t & 1)) return xl(e, xt()), null;
		var n = Fl(e, t);
		if (e.tag !== 0 && n === 2) {
			var i = Vt(e);
			i !== 0 && (t = i, n = Cl(e, i));
		}
		if (n === 1) throw n = $c, jl(e, 0), El(e, t), xl(e, xt()), n;
		if (n === 6) throw Error(r(345));
		return e.finishedWork = e.current.alternate, e.finishedLanes = t, Bl(e, il, sl), xl(e, xt()), null;
	}
	function Ol(e, t) {
		var n = K;
		K |= 1;
		try {
			return e(t);
		} finally {
			K = n, K === 0 && (ol = xt() + 500, ca && fa());
		}
	}
	function kl(e) {
		fl !== null && fl.tag === 0 && !(K & 6) && Hl();
		var t = K;
		K |= 1;
		var n = qc.transition, r = F;
		try {
			if (qc.transition = null, F = 1, e) return e();
		} finally {
			F = r, qc.transition = n, K = t, !(K & 6) && fa();
		}
	}
	function Al() {
		Xc = Zc.current, z(Zc);
	}
	function jl(e, t) {
		e.finishedWork = null, e.finishedLanes = 0;
		var n = e.timeoutHandle;
		if (n !== -1 && (e.timeoutHandle = -1, ki(n)), Jc !== null) for (n = Jc.return; n !== null;) {
			var r = n;
			switch (Ta(r), r.tag) {
				case 1:
					r = r.type.childContextTypes, r != null && na();
					break;
				case 3:
					yo(), z(Qi), z(Zi), To();
					break;
				case 5:
					xo(r);
					break;
				case 4:
					yo();
					break;
				case 13:
					z(So);
					break;
				case 19:
					z(So);
					break;
				case 10:
					Ya(r.type._context);
					break;
				case 22:
				case 23: Al();
			}
			n = n.return;
		}
		if (q = e, Jc = e = tu(e.current, null), Yc = Xc = t, Qc = 0, $c = null, nl = tl = el = 0, il = rl = null, $a !== null) {
			for (t = 0; t < $a.length; t++) if (n = $a[t], r = n.interleaved, r !== null) {
				n.interleaved = null;
				var i = r.next, a = n.pending;
				if (a !== null) {
					var o = a.next;
					a.next = i, r.next = o;
				}
				n.pending = r;
			}
			$a = null;
		}
		return e;
	}
	function Ml(e, t) {
		do {
			var n = Jc;
			try {
				if (Ja(), Eo.current = ys, Mo) {
					for (var i = ko.memoizedState; i !== null;) {
						var a = i.queue;
						a !== null && (a.pending = null), i = i.next;
					}
					Mo = !1;
				}
				if (Oo = 0, jo = Ao = ko = null, No = !1, Po = 0, Kc.current = null, n === null || n.return === null) {
					Qc = 1, $c = t, Jc = null;
					break;
				}
				a: {
					var o = e, s = n.return, c = n, l = t;
					if (t = Yc, c.flags |= 32768, typeof l == "object" && l && typeof l.then == "function") {
						var u = l, d = c, f = d.tag;
						if (!(d.mode & 1) && (f === 0 || f === 11 || f === 15)) {
							var p = d.alternate;
							p ? (d.updateQueue = p.updateQueue, d.memoizedState = p.memoizedState, d.lanes = p.lanes) : (d.updateQueue = null, d.memoizedState = null);
						}
						var m = Is(s);
						if (m !== null) {
							m.flags &= -257, Ls(m, s, c, o, t), m.mode & 1 && Fs(o, u, t), t = m, l = u;
							var h = t.updateQueue;
							if (h === null) {
								var g = /* @__PURE__ */ new Set();
								g.add(l), t.updateQueue = g;
							} else h.add(l);
							break a;
						} else {
							if (!(t & 1)) {
								Fs(o, u, t), Pl();
								break a;
							}
							l = Error(r(426));
						}
					} else if (V && c.mode & 1) {
						var _ = Is(s);
						if (_ !== null) {
							!(_.flags & 65536) && (_.flags |= 256), Ls(_, s, c, o, t), La(ks(l, c));
							break a;
						}
					}
					o = l = ks(l, c), Qc !== 4 && (Qc = 2), rl === null ? rl = [o] : rl.push(o), o = s;
					do {
						switch (o.tag) {
							case 3:
								o.flags |= 65536, t &= -t, o.lanes |= t;
								var v = Ns(o, l, t);
								lo(o, v);
								break a;
							case 1:
								c = l;
								var y = o.type, b = o.stateNode;
								if (!(o.flags & 128) && (typeof y.getDerivedStateFromError == "function" || b !== null && typeof b.componentDidCatch == "function" && (ul === null || !ul.has(b)))) {
									o.flags |= 65536, t &= -t, o.lanes |= t;
									var x = Ps(o, c, t);
									lo(o, x);
									break a;
								}
						}
						o = o.return;
					} while (o !== null);
				}
				zl(n);
			} catch (e) {
				t = e, Jc === n && n !== null && (Jc = n = n.return);
				continue;
			}
			break;
		} while (1);
	}
	function Nl() {
		var e = Gc.current;
		return Gc.current = ys, e === null ? ys : e;
	}
	function Pl() {
		(Qc === 0 || Qc === 3 || Qc === 2) && (Qc = 4), q === null || !(el & 268435455) && !(tl & 268435455) || El(q, Yc);
	}
	function Fl(e, t) {
		var n = K;
		K |= 2;
		var i = Nl();
		(q !== e || Yc !== t) && (sl = null, jl(e, t));
		do
			try {
				Il();
				break;
			} catch (t) {
				Ml(e, t);
			}
		while (1);
		if (Ja(), K = n, Gc.current = i, Jc !== null) throw Error(r(261));
		return q = null, Yc = 0, Qc;
	}
	function Il() {
		for (; Jc !== null;) Rl(Jc);
	}
	function Ll() {
		for (; Jc !== null && !yt();) Rl(Jc);
	}
	function Rl(e) {
		var t = Yl(e.alternate, e, Xc);
		e.memoizedProps = e.pendingProps, t === null ? zl(e) : Jc = t, Kc.current = null;
	}
	function zl(e) {
		var t = e;
		do {
			var n = t.alternate;
			if (e = t.return, t.flags & 32768) {
				if (n = hc(n, t), n !== null) {
					n.flags &= 32767, Jc = n;
					return;
				}
				if (e !== null) e.flags |= 32768, e.subtreeFlags = 0, e.deletions = null;
				else {
					Qc = 6, Jc = null;
					return;
				}
			} else if (n = mc(n, t, Xc), n !== null) {
				Jc = n;
				return;
			}
			if (t = t.sibling, t !== null) {
				Jc = t;
				return;
			}
			Jc = t = e;
		} while (t !== null);
		Qc === 0 && (Qc = 5);
	}
	function Bl(e, t, n) {
		var r = F, i = qc.transition;
		try {
			qc.transition = null, F = 1, Vl(e, t, n, r);
		} finally {
			qc.transition = i, F = r;
		}
		return null;
	}
	function Vl(e, t, n, i) {
		do
			Hl();
		while (fl !== null);
		if (K & 6) throw Error(r(327));
		n = e.finishedWork;
		var a = e.finishedLanes;
		if (n === null) return null;
		if (e.finishedWork = null, e.finishedLanes = 0, n === e.current) throw Error(r(177));
		e.callbackNode = null, e.callbackPriority = 0;
		var o = n.lanes | n.childLanes;
		if (Gt(e, o), e === q && (Jc = q = null, Yc = 0), !(n.subtreeFlags & 2064) && !(n.flags & 2064) || dl || (dl = !0, Xl(Tt, function() {
			return Hl(), null;
		})), o = (n.flags & 15990) != 0, n.subtreeFlags & 15990 || o) {
			o = qc.transition, qc.transition = null;
			var s = F;
			F = 1;
			var c = K;
			K |= 4, Kc.current = null, Sc(e, n), Lc(n, e), Br(Ei), vn = !!Ti, Ei = Ti = null, e.current = n, zc(n, e, a), bt(), K = c, F = s, qc.transition = o;
		} else e.current = n;
		if (dl && (dl = !1, fl = e, pl = a), o = e.pendingLanes, o === 0 && (ul = null), At(n.stateNode, i), xl(e, xt()), t !== null) for (i = e.onRecoverableError, n = 0; n < t.length; n++) a = t[n], i(a.value, {
			componentStack: a.stack,
			digest: a.digest
		});
		if (cl) throw cl = !1, e = ll, ll = null, e;
		return pl & 1 && e.tag !== 0 && Hl(), o = e.pendingLanes, o & 1 ? e === hl ? ml++ : (ml = 0, hl = e) : ml = 0, fa(), null;
	}
	function Hl() {
		if (fl !== null) {
			var e = I(pl), t = qc.transition, n = F;
			try {
				if (qc.transition = null, F = 16 > e ? 16 : e, fl === null) var i = !1;
				else {
					if (e = fl, fl = null, pl = 0, K & 6) throw Error(r(331));
					var a = K;
					for (K |= 4, G = e.current; G !== null;) {
						var o = G, s = o.child;
						if (G.flags & 16) {
							var c = o.deletions;
							if (c !== null) {
								for (var l = 0; l < c.length; l++) {
									var u = c[l];
									for (G = u; G !== null;) {
										var d = G;
										switch (d.tag) {
											case 0:
											case 11:
											case 15: Cc(8, d, o);
										}
										var f = d.child;
										if (f !== null) f.return = d, G = f;
										else for (; G !== null;) {
											d = G;
											var p = d.sibling, m = d.return;
											if (Ec(d), d === u) {
												G = null;
												break;
											}
											if (p !== null) {
												p.return = m, G = p;
												break;
											}
											G = m;
										}
									}
								}
								var h = o.alternate;
								if (h !== null) {
									var g = h.child;
									if (g !== null) {
										h.child = null;
										do {
											var _ = g.sibling;
											g.sibling = null, g = _;
										} while (g !== null);
									}
								}
								G = o;
							}
						}
						if (o.subtreeFlags & 2064 && s !== null) s.return = o, G = s;
						else b: for (; G !== null;) {
							if (o = G, o.flags & 2048) switch (o.tag) {
								case 0:
								case 11:
								case 15: Cc(9, o, o.return);
							}
							var v = o.sibling;
							if (v !== null) {
								v.return = o.return, G = v;
								break b;
							}
							G = o.return;
						}
					}
					var y = e.current;
					for (G = y; G !== null;) {
						s = G;
						var b = s.child;
						if (s.subtreeFlags & 2064 && b !== null) b.return = s, G = b;
						else b: for (s = y; G !== null;) {
							if (c = G, c.flags & 2048) try {
								switch (c.tag) {
									case 0:
									case 11:
									case 15: wc(9, c);
								}
							} catch (e) {
								Wl(c, c.return, e);
							}
							if (c === s) {
								G = null;
								break b;
							}
							var x = c.sibling;
							if (x !== null) {
								x.return = c.return, G = x;
								break b;
							}
							G = c.return;
						}
					}
					if (K = a, fa(), kt && typeof kt.onPostCommitFiberRoot == "function") try {
						kt.onPostCommitFiberRoot(Ot, e);
					} catch (e) {}
					i = !0;
				}
				return i;
			} finally {
				F = n, qc.transition = t;
			}
		}
		return !1;
	}
	function Ul(e, t, n) {
		t = ks(n, t), t = Ns(e, t, 1), e = so(e, t, 1), t = vl(), e !== null && (Wt(e, 1, t), xl(e, t));
	}
	function Wl(e, t, n) {
		if (e.tag === 3) Ul(e, e, n);
		else for (; t !== null;) {
			if (t.tag === 3) {
				Ul(t, e, n);
				break;
			} else if (t.tag === 1) {
				var r = t.stateNode;
				if (typeof t.type.getDerivedStateFromError == "function" || typeof r.componentDidCatch == "function" && (ul === null || !ul.has(r))) {
					e = ks(n, e), e = Ps(t, e, 1), t = so(t, e, 1), e = vl(), t !== null && (Wt(t, 1, e), xl(t, e));
					break;
				}
			}
			t = t.return;
		}
	}
	function Gl(e, t, n) {
		var r = e.pingCache;
		r !== null && r.delete(t), t = vl(), e.pingedLanes |= e.suspendedLanes & n, q === e && (Yc & n) === n && (Qc === 4 || Qc === 3 && (Yc & 130023424) === Yc && 500 > xt() - al ? jl(e, 0) : nl |= n), xl(e, t);
	}
	function Kl(e, t) {
		t === 0 && (e.mode & 1 ? (t = It, It <<= 1, !(It & 130023424) && (It = 4194304)) : t = 1);
		var n = vl();
		e = no(e, t), e !== null && (Wt(e, t, n), xl(e, n));
	}
	function ql(e) {
		var t = e.memoizedState, n = 0;
		t !== null && (n = t.retryLane), Kl(e, n);
	}
	function Jl(e, t) {
		var n = 0;
		switch (e.tag) {
			case 13:
				var i = e.stateNode, a = e.memoizedState;
				a !== null && (n = a.retryLane);
				break;
			case 19:
				i = e.stateNode;
				break;
			default: throw Error(r(314));
		}
		i !== null && i.delete(t), Kl(e, n);
	}
	var Yl = function(e, t, n) {
		if (e !== null) if (e.memoizedProps !== t.pendingProps || Qi.current) zs = !0;
		else {
			if ((e.lanes & n) === 0 && !(t.flags & 128)) return zs = !1, cc(e, t, n);
			zs = !!(e.flags & 131072);
		}
		else zs = !1, V && t.flags & 1048576 && Ca(t, ga, t.index);
		switch (t.lanes = 0, t.tag) {
			case 2:
				var i = t.type;
				oc(e, t), e = t.pendingProps;
				var a = ea(t, Zi.current);
				Za(t, n), a = Ro(null, t, i, e, a, n);
				var o = zo();
				return t.flags |= 1, typeof a == "object" && a && typeof a.render == "function" && a.$$typeof === void 0 ? (t.tag = 1, t.memoizedState = null, t.updateQueue = null, ta(i) ? (o = !0, aa(t)) : o = !1, t.memoizedState = a.state !== null && a.state !== void 0 ? a.state : null, io(t), a.updater = ws, t.stateNode = a, a._reactInternals = t, Os(t, i, e, n), t = Js(null, t, i, !0, o, n)) : (t.tag = 0, V && o && wa(t), Bs(null, t, a, n), t = t.child), t;
			case 16:
				i = t.elementType;
				a: {
					switch (oc(e, t), e = t.pendingProps, a = i._init, i = a(i._payload), t.type = i, a = t.tag = eu(i), e = W(i, e), a) {
						case 0:
							t = Ks(null, t, i, e, n);
							break a;
						case 1:
							t = qs(null, t, i, e, n);
							break a;
						case 11:
							t = Vs(null, t, i, e, n);
							break a;
						case 14:
							t = Hs(null, t, i, W(i.type, e), n);
							break a;
					}
					throw Error(r(306, i, ""));
				}
				return t;
			case 0: return i = t.type, a = t.pendingProps, a = t.elementType === i ? a : W(i, a), Ks(e, t, i, a, n);
			case 1: return i = t.type, a = t.pendingProps, a = t.elementType === i ? a : W(i, a), qs(e, t, i, a, n);
			case 3:
				a: {
					if (Ys(t), e === null) throw Error(r(387));
					i = t.pendingProps, o = t.memoizedState, a = o.element, ao(e, t), uo(t, i, null, n);
					var s = t.memoizedState;
					if (i = s.element, o.isDehydrated) if (o = {
						element: i,
						isDehydrated: !1,
						cache: s.cache,
						pendingSuspenseBoundaries: s.pendingSuspenseBoundaries,
						transitions: s.transitions
					}, t.updateQueue.baseState = o, t.memoizedState = o, t.flags & 256) {
						a = ks(Error(r(423)), t), t = Xs(e, t, i, n, a);
						break a;
					} else if (i !== a) {
						a = ks(Error(r(424)), t), t = Xs(e, t, i, n, a);
						break a;
					} else for (Da = Pi(t.stateNode.containerInfo.firstChild), Ea = t, V = !0, Oa = null, n = Wa(t, null, i, n), t.child = n; n;) n.flags = n.flags & -3 | 4096, n = n.sibling;
					else {
						if (Ia(), i === a) {
							t = sc(e, t, n);
							break a;
						}
						Bs(e, t, i, n);
					}
					t = t.child;
				}
				return t;
			case 5: return bo(t), e === null && Ma(t), i = t.type, a = t.pendingProps, o = e === null ? null : e.memoizedProps, s = a.children, Di(i, a) ? s = null : o !== null && Di(i, o) && (t.flags |= 32), Gs(e, t), Bs(e, t, s, n), t.child;
			case 6: return e === null && Ma(t), null;
			case 13: return $s(e, t, n);
			case 4: return vo(t, t.stateNode.containerInfo), i = t.pendingProps, e === null ? t.child = Ua(t, null, i, n) : Bs(e, t, i, n), t.child;
			case 11: return i = t.type, a = t.pendingProps, a = t.elementType === i ? a : W(i, a), Vs(e, t, i, a, n);
			case 7: return Bs(e, t, t.pendingProps, n), t.child;
			case 8: return Bs(e, t, t.pendingProps.children, n), t.child;
			case 12: return Bs(e, t, t.pendingProps.children, n), t.child;
			case 10:
				a: {
					if (i = t.type._context, a = t.pendingProps, o = t.memoizedProps, s = a.value, B(Ga, i._currentValue), i._currentValue = s, o !== null) if (Nr(o.value, s)) {
						if (o.children === a.children && !Qi.current) {
							t = sc(e, t, n);
							break a;
						}
					} else for (o = t.child, o !== null && (o.return = t); o !== null;) {
						var c = o.dependencies;
						if (c !== null) {
							s = o.child;
							for (var l = c.firstContext; l !== null;) {
								if (l.context === i) {
									if (o.tag === 1) {
										l = oo(-1, n & -n), l.tag = 2;
										var u = o.updateQueue;
										if (u !== null) {
											u = u.shared;
											var d = u.pending;
											d === null ? l.next = l : (l.next = d.next, d.next = l), u.pending = l;
										}
									}
									o.lanes |= n, l = o.alternate, l !== null && (l.lanes |= n), Xa(o.return, n, t), c.lanes |= n;
									break;
								}
								l = l.next;
							}
						} else if (o.tag === 10) s = o.type === t.type ? null : o.child;
						else if (o.tag === 18) {
							if (s = o.return, s === null) throw Error(r(341));
							s.lanes |= n, c = s.alternate, c !== null && (c.lanes |= n), Xa(s, n, t), s = o.sibling;
						} else s = o.child;
						if (s !== null) s.return = o;
						else for (s = o; s !== null;) {
							if (s === t) {
								s = null;
								break;
							}
							if (o = s.sibling, o !== null) {
								o.return = s.return, s = o;
								break;
							}
							s = s.return;
						}
						o = s;
					}
					Bs(e, t, a.children, n), t = t.child;
				}
				return t;
			case 9: return a = t.type, i = t.pendingProps.children, Za(t, n), a = Qa(a), i = i(a), t.flags |= 1, Bs(e, t, i, n), t.child;
			case 14: return i = t.type, a = W(i, t.pendingProps), a = W(i.type, a), Hs(e, t, i, a, n);
			case 15: return Us(e, t, t.type, t.pendingProps, n);
			case 17: return i = t.type, a = t.pendingProps, a = t.elementType === i ? a : W(i, a), oc(e, t), t.tag = 1, ta(i) ? (e = !0, aa(t)) : e = !1, Za(t, n), Es(t, i, a), Os(t, i, a, n), Js(null, t, i, !0, e, n);
			case 19: return ac(e, t, n);
			case 22: return Ws(e, t, n);
		}
		throw Error(r(156, t.tag));
	};
	function Xl(e, t) {
		return _t(e, t);
	}
	function Zl(e, t, n, r) {
		this.tag = e, this.key = n, this.sibling = this.child = this.return = this.stateNode = this.type = this.elementType = null, this.index = 0, this.ref = null, this.pendingProps = t, this.dependencies = this.memoizedState = this.updateQueue = this.memoizedProps = null, this.mode = r, this.subtreeFlags = this.flags = 0, this.deletions = null, this.childLanes = this.lanes = 0, this.alternate = null;
	}
	function Ql(e, t, n, r) {
		return new Zl(e, t, n, r);
	}
	function $l(e) {
		return e = e.prototype, !(!e || !e.isReactComponent);
	}
	function eu(e) {
		if (typeof e == "function") return +!!$l(e);
		if (e != null) {
			if (e = e.$$typeof, e === j) return 11;
			if (e === P) return 14;
		}
		return 2;
	}
	function tu(e, t) {
		var n = e.alternate;
		return n === null ? (n = Ql(e.tag, t, e.key, e.mode), n.elementType = e.elementType, n.type = e.type, n.stateNode = e.stateNode, n.alternate = e, e.alternate = n) : (n.pendingProps = t, n.type = e.type, n.flags = 0, n.subtreeFlags = 0, n.deletions = null), n.flags = e.flags & 14680064, n.childLanes = e.childLanes, n.lanes = e.lanes, n.child = e.child, n.memoizedProps = e.memoizedProps, n.memoizedState = e.memoizedState, n.updateQueue = e.updateQueue, t = e.dependencies, n.dependencies = t === null ? null : {
			lanes: t.lanes,
			firstContext: t.firstContext
		}, n.sibling = e.sibling, n.index = e.index, n.ref = e.ref, n;
	}
	function nu(e, t, n, i, a, o) {
		var s = 2;
		if (i = e, typeof e == "function") $l(e) && (s = 1);
		else if (typeof e == "string") s = 5;
		else a: switch (e) {
			case E: return ru(n.children, a, o, t);
			case D:
				s = 8, a |= 8;
				break;
			case O: return e = Ql(12, n, t, a | 2), e.elementType = O, e.lanes = o, e;
			case M: return e = Ql(13, n, t, a), e.elementType = M, e.lanes = o, e;
			case N: return e = Ql(19, n, t, a), e.elementType = N, e.lanes = o, e;
			case te: return iu(n, a, o, t);
			default:
				if (typeof e == "object" && e) switch (e.$$typeof) {
					case k:
						s = 10;
						break a;
					case A:
						s = 9;
						break a;
					case j:
						s = 11;
						break a;
					case P:
						s = 14;
						break a;
					case ee:
						s = 16, i = null;
						break a;
				}
				throw Error(r(130, e == null ? e : typeof e, ""));
		}
		return t = Ql(s, n, t, a), t.elementType = e, t.type = i, t.lanes = o, t;
	}
	function ru(e, t, n, r) {
		return e = Ql(7, e, r, t), e.lanes = n, e;
	}
	function iu(e, t, n, r) {
		return e = Ql(22, e, r, t), e.elementType = te, e.lanes = n, e.stateNode = { isHidden: !1 }, e;
	}
	function au(e, t, n) {
		return e = Ql(6, e, null, t), e.lanes = n, e;
	}
	function ou(e, t, n) {
		return t = Ql(4, e.children === null ? [] : e.children, e.key, t), t.lanes = n, t.stateNode = {
			containerInfo: e.containerInfo,
			pendingChildren: null,
			implementation: e.implementation
		}, t;
	}
	function su(e, t, n, r, i) {
		this.tag = t, this.containerInfo = e, this.finishedWork = this.pingCache = this.current = this.pendingChildren = null, this.timeoutHandle = -1, this.callbackNode = this.pendingContext = this.context = null, this.callbackPriority = 0, this.eventTimes = Ut(0), this.expirationTimes = Ut(-1), this.entangledLanes = this.finishedLanes = this.mutableReadLanes = this.expiredLanes = this.pingedLanes = this.suspendedLanes = this.pendingLanes = 0, this.entanglements = Ut(0), this.identifierPrefix = r, this.onRecoverableError = i, this.mutableSourceEagerHydrationData = null;
	}
	function cu(e, t, n, r, i, a, o, s, c) {
		return e = new su(e, t, n, s, c), t === 1 ? (t = 1, !0 === a && (t |= 8)) : t = 0, a = Ql(3, null, null, t), e.current = a, a.stateNode = e, a.memoizedState = {
			element: r,
			isDehydrated: n,
			cache: null,
			transitions: null,
			pendingSuspenseBoundaries: null
		}, io(a), e;
	}
	function lu(e, t, n) {
		var r = 3 < arguments.length && arguments[3] !== void 0 ? arguments[3] : null;
		return {
			$$typeof: T,
			key: r == null ? null : "" + r,
			children: e,
			containerInfo: t,
			implementation: n
		};
	}
	function uu(e) {
		if (!e) return Xi;
		e = e._reactInternals;
		a: {
			if (dt(e) !== e || e.tag !== 1) throw Error(r(170));
			var t = e;
			do {
				switch (t.tag) {
					case 3:
						t = t.stateNode.context;
						break a;
					case 1: if (ta(t.type)) {
						t = t.stateNode.__reactInternalMemoizedMergedChildContext;
						break a;
					}
				}
				t = t.return;
			} while (t !== null);
			throw Error(r(171));
		}
		if (e.tag === 1) {
			var n = e.type;
			if (ta(n)) return ia(e, n, t);
		}
		return t;
	}
	function du(e, t, n, r, i, a, o, s, c) {
		return e = cu(n, r, !0, e, i, a, o, s, c), e.context = uu(null), n = e.current, r = vl(), i = yl(n), a = oo(r, i), a.callback = t == null ? null : t, so(n, a, i), e.current.lanes = i, Wt(e, i, r), xl(e, r), e;
	}
	function fu(e, t, n, r) {
		var i = t.current, a = vl(), o = yl(i);
		return n = uu(n), t.context === null ? t.context = n : t.pendingContext = n, t = oo(a, o), t.payload = { element: e }, r = r === void 0 ? null : r, r !== null && (t.callback = r), e = so(i, t, o), e !== null && (bl(e, i, o, a), co(e, i, o)), o;
	}
	function pu(e) {
		if (e = e.current, !e.child) return null;
		switch (e.child.tag) {
			case 5: return e.child.stateNode;
			default: return e.child.stateNode;
		}
	}
	function mu(e, t) {
		if (e = e.memoizedState, e !== null && e.dehydrated !== null) {
			var n = e.retryLane;
			e.retryLane = n !== 0 && n < t ? n : t;
		}
	}
	function hu(e, t) {
		mu(e, t), (e = e.alternate) && mu(e, t);
	}
	function gu() {
		return null;
	}
	var _u = typeof reportError == "function" ? reportError : function(e) {
		console.error(e);
	};
	function vu(e) {
		this._internalRoot = e;
	}
	yu.prototype.render = vu.prototype.render = function(e) {
		var t = this._internalRoot;
		if (t === null) throw Error(r(409));
		fu(e, t, null, null);
	}, yu.prototype.unmount = vu.prototype.unmount = function() {
		var e = this._internalRoot;
		if (e !== null) {
			this._internalRoot = null;
			var t = e.containerInfo;
			kl(function() {
				fu(null, e, null, null);
			}), t[zi] = null;
		}
	};
	function yu(e) {
		this._internalRoot = e;
	}
	yu.prototype.unstable_scheduleHydration = function(e) {
		if (e) {
			var t = Xt();
			e = {
				blockedOn: null,
				target: e,
				priority: t
			};
			for (var n = 0; n < on.length && t !== 0 && t < on[n].priority; n++);
			on.splice(n, 0, e), n === 0 && dn(e);
		}
	};
	function bu(e) {
		return !(!e || e.nodeType !== 1 && e.nodeType !== 9 && e.nodeType !== 11);
	}
	function xu(e) {
		return !(!e || e.nodeType !== 1 && e.nodeType !== 9 && e.nodeType !== 11 && (e.nodeType !== 8 || e.nodeValue !== " react-mount-point-unstable "));
	}
	function Su() {}
	function Cu(e, t, n, r, i) {
		if (i) {
			if (typeof r == "function") {
				var a = r;
				r = function() {
					var e = pu(o);
					a.call(e);
				};
			}
			var o = du(t, r, e, 0, null, !1, !1, "", Su);
			return e._reactRootContainer = o, e[zi] = o.current, pi(e.nodeType === 8 ? e.parentNode : e), kl(), o;
		}
		for (; i = e.lastChild;) e.removeChild(i);
		if (typeof r == "function") {
			var s = r;
			r = function() {
				var e = pu(c);
				s.call(e);
			};
		}
		var c = cu(e, 0, !1, null, null, !1, !1, "", Su);
		return e._reactRootContainer = c, e[zi] = c.current, pi(e.nodeType === 8 ? e.parentNode : e), kl(function() {
			fu(t, c, n, r);
		}), c;
	}
	function wu(e, t, n, r, i) {
		var a = n._reactRootContainer;
		if (a) {
			var o = a;
			if (typeof i == "function") {
				var s = i;
				i = function() {
					var e = pu(o);
					s.call(e);
				};
			}
			fu(t, o, e, i);
		} else o = Cu(n, t, e, i, r);
		return pu(o);
	}
	qt = function(e) {
		switch (e.tag) {
			case 3:
				var t = e.stateNode;
				if (t.current.memoizedState.isDehydrated) {
					var n = Lt(t.pendingLanes);
					n !== 0 && (Kt(t, n | 1), xl(t, xt()), !(K & 6) && (ol = xt() + 500, fa()));
				}
				break;
			case 13: kl(function() {
				var t = no(e, 1);
				t !== null && bl(t, e, 1, vl());
			}), hu(e, 1);
		}
	}, Jt = function(e) {
		if (e.tag === 13) {
			var t = no(e, 134217728);
			t !== null && bl(t, e, 134217728, vl()), hu(e, 134217728);
		}
	}, Yt = function(e) {
		if (e.tag === 13) {
			var t = yl(e), n = no(e, t);
			n !== null && bl(n, e, t, vl()), hu(e, t);
		}
	}, Xt = function() {
		return F;
	}, Zt = function(e, t) {
		var n = F;
		try {
			return F = e, t();
		} finally {
			F = n;
		}
	}, We = function(e, t, n) {
		switch (t) {
			case "input":
				if (xe(e, n), t = n.name, n.type === "radio" && t != null) {
					for (n = e; n.parentNode;) n = n.parentNode;
					for (n = n.querySelectorAll("input[name=" + JSON.stringify("" + t) + "][type=\"radio\"]"), t = 0; t < n.length; t++) {
						var i = n[t];
						if (i !== e && i.form === e.form) {
							var a = Ki(i);
							if (!a) throw Error(r(90));
							ge(i), xe(i, a);
						}
					}
				}
				break;
			case "textarea":
				Oe(e, n);
				break;
			case "select": t = n.value, t != null && Te(e, !!n.multiple, t, !1);
		}
	}, Xe = Ol, Ze = kl;
	var Tu = {
		usingClientEntryPoint: !1,
		Events: [
			Wi,
			Gi,
			Ki,
			Je,
			Ye,
			Ol
		]
	}, Eu = {
		findFiberByHostInstance: Ui,
		bundleType: 0,
		version: "18.3.1",
		rendererPackageName: "react-dom"
	}, Du = {
		bundleType: Eu.bundleType,
		version: Eu.version,
		rendererPackageName: Eu.rendererPackageName,
		rendererConfig: Eu.rendererConfig,
		overrideHookState: null,
		overrideHookStateDeletePath: null,
		overrideHookStateRenamePath: null,
		overrideProps: null,
		overridePropsDeletePath: null,
		overridePropsRenamePath: null,
		setErrorHandler: null,
		setSuspenseHandler: null,
		scheduleUpdate: null,
		currentDispatcherRef: C.ReactCurrentDispatcher,
		findHostInstanceByFiber: function(e) {
			return e = ht(e), e === null ? null : e.stateNode;
		},
		findFiberByHostInstance: Eu.findFiberByHostInstance || gu,
		findHostInstancesForRefresh: null,
		scheduleRefresh: null,
		scheduleRoot: null,
		setRefreshHandler: null,
		getCurrentFiber: null,
		reconcilerVersion: "18.3.1-next-f1338f8080-20240426"
	};
	if (typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ < "u") {
		var Ou = __REACT_DEVTOOLS_GLOBAL_HOOK__;
		if (!Ou.isDisabled && Ou.supportsFiber) try {
			Ot = Ou.inject(Du), kt = Ou;
		} catch (e) {}
	}
	e.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED = Tu, e.createPortal = function(e, t) {
		var n = 2 < arguments.length && arguments[2] !== void 0 ? arguments[2] : null;
		if (!bu(t)) throw Error(r(200));
		return lu(e, t, null, n);
	}, e.createRoot = function(e, t) {
		if (!bu(e)) throw Error(r(299));
		var n = !1, i = "", a = _u;
		return t != null && (!0 === t.unstable_strictMode && (n = !0), t.identifierPrefix !== void 0 && (i = t.identifierPrefix), t.onRecoverableError !== void 0 && (a = t.onRecoverableError)), t = cu(e, 1, !1, null, null, n, !1, i, a), e[zi] = t.current, pi(e.nodeType === 8 ? e.parentNode : e), new vu(t);
	}, e.findDOMNode = function(e) {
		if (e == null) return null;
		if (e.nodeType === 1) return e;
		var t = e._reactInternals;
		if (t === void 0) throw typeof e.render == "function" ? Error(r(188)) : (e = Object.keys(e).join(","), Error(r(268, e)));
		return e = ht(t), e = e === null ? null : e.stateNode, e;
	}, e.flushSync = function(e) {
		return kl(e);
	}, e.hydrate = function(e, t, n) {
		if (!xu(t)) throw Error(r(200));
		return wu(null, e, t, !0, n);
	}, e.hydrateRoot = function(e, t, n) {
		if (!bu(e)) throw Error(r(405));
		var i = n != null && n.hydratedSources || null, a = !1, o = "", s = _u;
		if (n != null && (!0 === n.unstable_strictMode && (a = !0), n.identifierPrefix !== void 0 && (o = n.identifierPrefix), n.onRecoverableError !== void 0 && (s = n.onRecoverableError)), t = du(t, null, e, 1, n == null ? null : n, a, !1, o, s), e[zi] = t.current, pi(e), i) for (e = 0; e < i.length; e++) n = i[e], a = n._getVersion, a = a(n._source), t.mutableSourceEagerHydrationData == null ? t.mutableSourceEagerHydrationData = [n, a] : t.mutableSourceEagerHydrationData.push(n, a);
		return new yu(t);
	}, e.render = function(e, t, n) {
		if (!xu(t)) throw Error(r(200));
		return wu(null, e, t, !1, n);
	}, e.unmountComponentAtNode = function(e) {
		if (!xu(e)) throw Error(r(40));
		return e._reactRootContainer ? (kl(function() {
			wu(null, null, e, !1, function() {
				e._reactRootContainer = null, e[zi] = null;
			});
		}), !0) : !1;
	}, e.unstable_batchedUpdates = Ol, e.unstable_renderSubtreeIntoContainer = function(e, t, n, i) {
		if (!xu(n)) throw Error(r(200));
		if (e == null || e._reactInternals === void 0) throw Error(r(38));
		return wu(e, t, n, !1, i);
	}, e.version = "18.3.1-next-f1338f8080-20240426";
})), h = /* @__PURE__ */ o(((e, t) => {
	function n() {
		if (!(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ > "u" || typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE != "function")) try {
			__REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE(n);
		} catch (e) {
			console.error(e);
		}
	}
	n(), t.exports = m();
})), g = /* @__PURE__ */ o(((e) => {
	var t = h();
	e.createRoot = t.createRoot, e.hydrateRoot = t.hydrateRoot;
})), _ = (...e) => e.filter((e, t, n) => !!e && e.trim() !== "" && n.indexOf(e) === t).join(" ").trim(), v = (e) => e.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase(), y = (e) => e.replace(/^([A-Z])|[\s-_]+(\w)/g, (e, t, n) => n ? n.toUpperCase() : t.toLowerCase()), b = (e) => {
	let t = y(e);
	return t.charAt(0).toUpperCase() + t.slice(1);
}, x = {
	xmlns: "http://www.w3.org/2000/svg",
	width: 24,
	height: 24,
	viewBox: "0 0 24 24",
	fill: "none",
	stroke: "currentColor",
	strokeWidth: 2,
	strokeLinecap: "round",
	strokeLinejoin: "round"
}, S = (e) => {
	for (let t in e) if (t.startsWith("aria-") || t === "role" || t === "title") return !0;
	return !1;
}, C = /* @__PURE__ */ l(d(), 1), w = (0, C.createContext)({}), T = () => (0, C.useContext)(w), E = (0, C.forwardRef)(({ color: e, size: t, strokeWidth: n, absoluteStrokeWidth: r, className: i = "", children: a, iconNode: o, ...s }, c) => {
	var l, u, d;
	let { size: f = 24, strokeWidth: p = 2, absoluteStrokeWidth: m = !1, color: h = "currentColor", className: g = "" } = (l = T()) == null ? {} : l, v = (r == null ? m : r) ? Number(n == null ? p : n) * 24 / Number(t == null ? f : t) : n == null ? p : n;
	return (0, C.createElement)("svg", {
		ref: c,
		...x,
		width: (u = t == null ? f : t) == null ? x.width : u,
		height: (d = t == null ? f : t) == null ? x.height : d,
		stroke: e == null ? h : e,
		strokeWidth: v,
		className: _("lucide", g, i),
		...!a && !S(s) && { "aria-hidden": "true" },
		...s
	}, [...o.map(([e, t]) => (0, C.createElement)(e, t)), ...Array.isArray(a) ? a : [a]]);
}), D = (e, t) => {
	let n = (0, C.forwardRef)(({ className: n, ...r }, i) => (0, C.createElement)(E, {
		ref: i,
		iconNode: t,
		className: _(`lucide-${v(b(e))}`, `lucide-${e}`, n),
		...r
	}));
	return n.displayName = b(e), n;
}, O = D("activity", [["path", {
	d: "M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2",
	key: "169zse"
}]]), k = D("check", [["path", {
	d: "M20 6 9 17l-5-5",
	key: "1gmf2c"
}]]), A = D("chevron-down", [["path", {
	d: "m6 9 6 6 6-6",
	key: "qrunsl"
}]]), j = D("chevron-right", [["path", {
	d: "m9 18 6-6-6-6",
	key: "mthhwq"
}]]), M = D("chevron-up", [["path", {
	d: "m18 15-6-6-6 6",
	key: "153udz"
}]]), N = D("circle-alert", [
	["circle", {
		cx: "12",
		cy: "12",
		r: "10",
		key: "1mglay"
	}],
	["line", {
		x1: "12",
		x2: "12",
		y1: "8",
		y2: "12",
		key: "1pkeuh"
	}],
	["line", {
		x1: "12",
		x2: "12.01",
		y1: "16",
		y2: "16",
		key: "4dfq90"
	}]
]), P = D("circle", [["circle", {
	cx: "12",
	cy: "12",
	r: "10",
	key: "1mglay"
}]]), ee = D("clock-3", [["circle", {
	cx: "12",
	cy: "12",
	r: "10",
	key: "1mglay"
}], ["path", {
	d: "M12 6v6h4",
	key: "135r8i"
}]]), te = D("database", [
	["ellipse", {
		cx: "12",
		cy: "5",
		rx: "9",
		ry: "3",
		key: "msslwz"
	}],
	["path", {
		d: "M3 5V19A9 3 0 0 0 21 19V5",
		key: "1wlel7"
	}],
	["path", {
		d: "M3 12A9 3 0 0 0 21 12",
		key: "mv7ke4"
	}]
]), ne = D("info", [
	["circle", {
		cx: "12",
		cy: "12",
		r: "10",
		key: "1mglay"
	}],
	["path", {
		d: "M12 16v-4",
		key: "1dtifu"
	}],
	["path", {
		d: "M12 8h.01",
		key: "e9boi3"
	}]
]), re = D("list-checks", [
	["path", {
		d: "M13 5h8",
		key: "a7qcls"
	}],
	["path", {
		d: "M13 12h8",
		key: "h98zly"
	}],
	["path", {
		d: "M13 19h8",
		key: "c3s6r1"
	}],
	["path", {
		d: "m3 17 2 2 4-4",
		key: "1jhpwq"
	}],
	["path", {
		d: "m3 7 2 2 4-4",
		key: "1obspn"
	}]
]), ie = D("messages-square", [["path", {
	d: "M16 10a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 14.286V4a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z",
	key: "1n2ejm"
}], ["path", {
	d: "M20 9a2 2 0 0 1 2 2v10.286a.71.71 0 0 1-1.212.502l-2.202-2.202A2 2 0 0 0 17.172 19H10a2 2 0 0 1-2-2v-1",
	key: "1qfcsi"
}]]), ae = D("play", [["path", {
	d: "M5 5a2 2 0 0 1 3.008-1.728l11.997 6.998a2 2 0 0 1 .003 3.458l-12 7A2 2 0 0 1 5 19z",
	key: "10ikf1"
}]]), oe = D("refresh-cw", [
	["path", {
		d: "M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8",
		key: "v9h5vc"
	}],
	["path", {
		d: "M21 3v5h-5",
		key: "1q7to0"
	}],
	["path", {
		d: "M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16",
		key: "3uifl3"
	}],
	["path", {
		d: "M8 16H3v5",
		key: "1cv678"
	}]
]), se = D("rotate-ccw", [["path", {
	d: "M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8",
	key: "1357e3"
}], ["path", {
	d: "M3 3v5h5",
	key: "1xhq8a"
}]]), ce = D("rows-3", [
	["rect", {
		width: "18",
		height: "18",
		x: "3",
		y: "3",
		rx: "2",
		key: "afitv7"
	}],
	["path", {
		d: "M21 9H3",
		key: "1338ky"
	}],
	["path", {
		d: "M21 15H3",
		key: "9uk58r"
	}]
]), le = D("search", [["path", {
	d: "m21 21-4.34-4.34",
	key: "14j7rj"
}], ["circle", {
	cx: "11",
	cy: "11",
	r: "8",
	key: "4ej97u"
}]]), ue = D("settings-2", [
	["path", {
		d: "M14 17H5",
		key: "gfn3mx"
	}],
	["path", {
		d: "M19 7h-9",
		key: "6i9tg"
	}],
	["circle", {
		cx: "17",
		cy: "17",
		r: "3",
		key: "18b49y"
	}],
	["circle", {
		cx: "7",
		cy: "7",
		r: "3",
		key: "dfmy0x"
	}]
]), de = D("shield-check", [["path", {
	d: "M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z",
	key: "oel41y"
}], ["path", {
	d: "m9 12 2 2 4-4",
	key: "dzmm74"
}]]), fe = D("triangle-alert", [
	["path", {
		d: "m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3",
		key: "wmoenq"
	}],
	["path", {
		d: "M12 9v4",
		key: "juzpu7"
	}],
	["path", {
		d: "M12 17h.01",
		key: "p32p05"
	}]
]), pe = D("wand-sparkles", [
	["path", {
		d: "m21.64 3.64-1.28-1.28a1.21 1.21 0 0 0-1.72 0L2.36 18.64a1.21 1.21 0 0 0 0 1.72l1.28 1.28a1.2 1.2 0 0 0 1.72 0L21.64 5.36a1.2 1.2 0 0 0 0-1.72",
		key: "ul74o6"
	}],
	["path", {
		d: "m14 7 3 3",
		key: "1r5n42"
	}],
	["path", {
		d: "M5 6v4",
		key: "ilb8ba"
	}],
	["path", {
		d: "M19 14v4",
		key: "blhpug"
	}],
	["path", {
		d: "M10 2v2",
		key: "7u0qdc"
	}],
	["path", {
		d: "M7 8H3",
		key: "zfb6yr"
	}],
	["path", {
		d: "M21 16h-4",
		key: "1cnmox"
	}],
	["path", {
		d: "M11 3H9",
		key: "1obp7u"
	}]
]);
//#endregion
//#region node_modules/clsx/dist/clsx.mjs
function me(e) {
	var t, n, r = "";
	if (typeof e == "string" || typeof e == "number") r += e;
	else if (typeof e == "object") if (Array.isArray(e)) {
		var i = e.length;
		for (t = 0; t < i; t++) e[t] && (n = me(e[t])) && (r && (r += " "), r += n);
	} else for (n in e) e[n] && (r && (r += " "), r += n);
	return r;
}
function he() {
	for (var e, t, n = 0, r = "", i = arguments.length; n < i; n++) (e = arguments[n]) && (t = me(e)) && (r && (r += " "), r += t);
	return r;
}
//#endregion
//#region node_modules/recharts/es6/util/excludeEventProps.js
var ge = /* @__PURE__ */ "dangerouslySetInnerHTML.onCopy.onCopyCapture.onCut.onCutCapture.onPaste.onPasteCapture.onCompositionEnd.onCompositionEndCapture.onCompositionStart.onCompositionStartCapture.onCompositionUpdate.onCompositionUpdateCapture.onFocus.onFocusCapture.onBlur.onBlurCapture.onChange.onChangeCapture.onBeforeInput.onBeforeInputCapture.onInput.onInputCapture.onReset.onResetCapture.onSubmit.onSubmitCapture.onInvalid.onInvalidCapture.onLoad.onLoadCapture.onError.onErrorCapture.onKeyDown.onKeyDownCapture.onKeyPress.onKeyPressCapture.onKeyUp.onKeyUpCapture.onAbort.onAbortCapture.onCanPlay.onCanPlayCapture.onCanPlayThrough.onCanPlayThroughCapture.onDurationChange.onDurationChangeCapture.onEmptied.onEmptiedCapture.onEncrypted.onEncryptedCapture.onEnded.onEndedCapture.onLoadedData.onLoadedDataCapture.onLoadedMetadata.onLoadedMetadataCapture.onLoadStart.onLoadStartCapture.onPause.onPauseCapture.onPlay.onPlayCapture.onPlaying.onPlayingCapture.onProgress.onProgressCapture.onRateChange.onRateChangeCapture.onSeeked.onSeekedCapture.onSeeking.onSeekingCapture.onStalled.onStalledCapture.onSuspend.onSuspendCapture.onTimeUpdate.onTimeUpdateCapture.onVolumeChange.onVolumeChangeCapture.onWaiting.onWaitingCapture.onAuxClick.onAuxClickCapture.onClick.onClickCapture.onContextMenu.onContextMenuCapture.onDoubleClick.onDoubleClickCapture.onDrag.onDragCapture.onDragEnd.onDragEndCapture.onDragEnter.onDragEnterCapture.onDragExit.onDragExitCapture.onDragLeave.onDragLeaveCapture.onDragOver.onDragOverCapture.onDragStart.onDragStartCapture.onDrop.onDropCapture.onMouseDown.onMouseDownCapture.onMouseEnter.onMouseLeave.onMouseMove.onMouseMoveCapture.onMouseOut.onMouseOutCapture.onMouseOver.onMouseOverCapture.onMouseUp.onMouseUpCapture.onSelect.onSelectCapture.onTouchCancel.onTouchCancelCapture.onTouchEnd.onTouchEndCapture.onTouchMove.onTouchMoveCapture.onTouchStart.onTouchStartCapture.onPointerDown.onPointerDownCapture.onPointerMove.onPointerMoveCapture.onPointerUp.onPointerUpCapture.onPointerCancel.onPointerCancelCapture.onPointerEnter.onPointerEnterCapture.onPointerLeave.onPointerLeaveCapture.onPointerOver.onPointerOverCapture.onPointerOut.onPointerOutCapture.onGotPointerCapture.onGotPointerCaptureCapture.onLostPointerCapture.onLostPointerCaptureCapture.onScroll.onScrollCapture.onWheel.onWheelCapture.onAnimationStart.onAnimationStartCapture.onAnimationEnd.onAnimationEndCapture.onAnimationIteration.onAnimationIterationCapture.onTransitionEnd.onTransitionEndCapture".split(".");
function _e(e) {
	return typeof e == "string" && ge.includes(e);
}
//#endregion
//#region node_modules/recharts/es6/util/svgPropertiesNoEvents.js
var ve = /* @__PURE__ */ new Set(/* @__PURE__ */ "aria-activedescendant.aria-atomic.aria-autocomplete.aria-busy.aria-checked.aria-colcount.aria-colindex.aria-colspan.aria-controls.aria-current.aria-describedby.aria-details.aria-disabled.aria-errormessage.aria-expanded.aria-flowto.aria-haspopup.aria-hidden.aria-invalid.aria-keyshortcuts.aria-label.aria-labelledby.aria-level.aria-live.aria-modal.aria-multiline.aria-multiselectable.aria-orientation.aria-owns.aria-placeholder.aria-posinset.aria-pressed.aria-readonly.aria-relevant.aria-required.aria-roledescription.aria-rowcount.aria-rowindex.aria-rowspan.aria-selected.aria-setsize.aria-sort.aria-valuemax.aria-valuemin.aria-valuenow.aria-valuetext.className.color.height.id.lang.max.media.method.min.name.style.target.width.role.tabIndex.accentHeight.accumulate.additive.alignmentBaseline.allowReorder.alphabetic.amplitude.arabicForm.ascent.attributeName.attributeType.autoReverse.azimuth.baseFrequency.baselineShift.baseProfile.bbox.begin.bias.by.calcMode.capHeight.clip.clipPath.clipPathUnits.clipRule.colorInterpolation.colorInterpolationFilters.colorProfile.colorRendering.contentScriptType.contentStyleType.cursor.cx.cy.d.decelerate.descent.diffuseConstant.direction.display.divisor.dominantBaseline.dur.dx.dy.edgeMode.elevation.enableBackground.end.exponent.externalResourcesRequired.fill.fillOpacity.fillRule.filter.filterRes.filterUnits.floodColor.floodOpacity.focusable.fontFamily.fontSize.fontSizeAdjust.fontStretch.fontStyle.fontVariant.fontWeight.format.from.fx.fy.g1.g2.glyphName.glyphOrientationHorizontal.glyphOrientationVertical.glyphRef.gradientTransform.gradientUnits.hanging.horizAdvX.horizOriginX.href.ideographic.imageRendering.in2.in.intercept.k1.k2.k3.k4.k.kernelMatrix.kernelUnitLength.kerning.keyPoints.keySplines.keyTimes.lengthAdjust.letterSpacing.lightingColor.limitingConeAngle.local.markerEnd.markerHeight.markerMid.markerStart.markerUnits.markerWidth.mask.maskContentUnits.maskUnits.mathematical.mode.numOctaves.offset.opacity.operator.order.orient.orientation.origin.overflow.overlinePosition.overlineThickness.paintOrder.panose1.pathLength.patternContentUnits.patternTransform.patternUnits.pointerEvents.pointsAtX.pointsAtY.pointsAtZ.preserveAlpha.preserveAspectRatio.primitiveUnits.r.radius.refX.refY.renderingIntent.repeatCount.repeatDur.requiredExtensions.requiredFeatures.restart.result.rotate.rx.ry.seed.shapeRendering.slope.spacing.specularConstant.specularExponent.speed.spreadMethod.startOffset.stdDeviation.stemh.stemv.stitchTiles.stopColor.stopOpacity.strikethroughPosition.strikethroughThickness.string.stroke.strokeDasharray.strokeDashoffset.strokeLinecap.strokeLinejoin.strokeMiterlimit.strokeOpacity.strokeWidth.surfaceScale.systemLanguage.tableValues.targetX.targetY.textAnchor.textDecoration.textLength.textRendering.to.transform.u1.u2.underlinePosition.underlineThickness.unicode.unicodeBidi.unicodeRange.unitsPerEm.vAlphabetic.values.vectorEffect.version.vertAdvY.vertOriginX.vertOriginY.vHanging.vIdeographic.viewTarget.visibility.vMathematical.widths.wordSpacing.writingMode.x1.x2.x.xChannelSelector.xHeight.xlinkActuate.xlinkArcrole.xlinkHref.xlinkRole.xlinkShow.xlinkTitle.xlinkType.xmlBase.xmlLang.xmlns.xmlnsXlink.xmlSpace.y1.y2.y.yChannelSelector.z.zoomAndPan.ref.key.angle".split("."));
function ye(e) {
	return typeof e == "string" && ve.has(e);
}
function be(e) {
	return typeof e == "string" && e.startsWith("data-");
}
function xe(e) {
	if (typeof e != "object" || !e) return {};
	var t = {};
	for (var n in e) Object.prototype.hasOwnProperty.call(e, n) && (ye(n) || be(n)) && (t[n] = e[n]);
	return t;
}
function Se(e) {
	if (e == null) return null;
	if (/*#__PURE__*/ (0, C.isValidElement)(e) && typeof e.props == "object" && e.props !== null) {
		var t = e.props;
		return xe(t);
	}
	return typeof e == "object" && !Array.isArray(e) ? xe(e) : null;
}
//#endregion
//#region node_modules/recharts/es6/util/svgPropertiesAndEvents.js
function Ce(e) {
	var t = {};
	for (var n in e) Object.prototype.hasOwnProperty.call(e, n) && (ye(n) || be(n) || _e(n)) && (t[n] = e[n]);
	return t;
}
//#endregion
//#region node_modules/recharts/es6/container/Surface.js
var we = [
	"children",
	"width",
	"height",
	"viewBox",
	"className",
	"style",
	"title",
	"desc"
];
function Te() {
	return Te = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, Te.apply(null, arguments);
}
function Ee(e, t) {
	if (e == null) return {};
	var n, r, i = De(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function De(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var Oe = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.children, r = e.width, i = e.height, a = e.viewBox, o = e.className, s = e.style, c = e.title, l = e.desc, u = Ee(e, we), d = a || {
		width: r,
		height: i,
		x: 0,
		y: 0
	}, f = he("recharts-surface", o);
	return /*#__PURE__*/ C.createElement("svg", Te({}, Ce(u), {
		className: f,
		width: r,
		height: i,
		style: s,
		viewBox: `${d.x} ${d.y} ${d.width} ${d.height}`,
		ref: t
	}), /*#__PURE__*/ C.createElement("title", null, c), /*#__PURE__*/ C.createElement("desc", null, l), n);
}), ke = ["children", "className"];
function Ae() {
	return Ae = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, Ae.apply(null, arguments);
}
function je(e, t) {
	if (e == null) return {};
	var n, r, i = Me(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function Me(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var Ne = /*#__PURE__*/ C.forwardRef((e, t) => {
	var n = e.children, r = e.className, i = je(e, ke), a = he("recharts-layer", r);
	return /*#__PURE__*/ C.createElement("g", Ae({ className: a }, Ce(i), { ref: t }), n);
}), Pe = /*#__PURE__*/ (0, C.createContext)(null);
//#endregion
//#region node_modules/d3-shape/src/constant.js
function Fe(e) {
	return function() {
		return e;
	};
}
//#endregion
//#region node_modules/d3-path/src/path.js
var Ie = Math.PI, Le = 2 * Ie, Re = 1e-6, ze = Le - Re;
function Be(e) {
	this._ += e[0];
	for (let t = 1, n = e.length; t < n; ++t) this._ += arguments[t] + e[t];
}
function Ve(e) {
	let t = Math.floor(e);
	if (!(t >= 0)) throw Error(`invalid digits: ${e}`);
	if (t > 15) return Be;
	let n = 10 ** t;
	return function(e) {
		this._ += e[0];
		for (let t = 1, r = e.length; t < r; ++t) this._ += Math.round(arguments[t] * n) / n + e[t];
	};
}
var He = class {
	constructor(e) {
		this._x0 = this._y0 = this._x1 = this._y1 = null, this._ = "", this._append = e == null ? Be : Ve(e);
	}
	moveTo(e, t) {
		this._append`M${this._x0 = this._x1 = +e},${this._y0 = this._y1 = +t}`;
	}
	closePath() {
		this._x1 !== null && (this._x1 = this._x0, this._y1 = this._y0, this._append`Z`);
	}
	lineTo(e, t) {
		this._append`L${this._x1 = +e},${this._y1 = +t}`;
	}
	quadraticCurveTo(e, t, n, r) {
		this._append`Q${+e},${+t},${this._x1 = +n},${this._y1 = +r}`;
	}
	bezierCurveTo(e, t, n, r, i, a) {
		this._append`C${+e},${+t},${+n},${+r},${this._x1 = +i},${this._y1 = +a}`;
	}
	arcTo(e, t, n, r, i) {
		if (e = +e, t = +t, n = +n, r = +r, i = +i, i < 0) throw Error(`negative radius: ${i}`);
		let a = this._x1, o = this._y1, s = n - e, c = r - t, l = a - e, u = o - t, d = l * l + u * u;
		if (this._x1 === null) this._append`M${this._x1 = e},${this._y1 = t}`;
		else if (d > Re) if (!(Math.abs(u * s - c * l) > Re) || !i) this._append`L${this._x1 = e},${this._y1 = t}`;
		else {
			let f = n - a, p = r - o, m = s * s + c * c, h = f * f + p * p, g = Math.sqrt(m), _ = Math.sqrt(d), v = i * Math.tan((Ie - Math.acos((m + d - h) / (2 * g * _))) / 2), y = v / _, b = v / g;
			Math.abs(y - 1) > Re && this._append`L${e + y * l},${t + y * u}`, this._append`A${i},${i},0,0,${+(u * f > l * p)},${this._x1 = e + b * s},${this._y1 = t + b * c}`;
		}
	}
	arc(e, t, n, r, i, a) {
		if (e = +e, t = +t, n = +n, a = !!a, n < 0) throw Error(`negative radius: ${n}`);
		let o = n * Math.cos(r), s = n * Math.sin(r), c = e + o, l = t + s, u = 1 ^ a, d = a ? r - i : i - r;
		this._x1 === null ? this._append`M${c},${l}` : (Math.abs(this._x1 - c) > Re || Math.abs(this._y1 - l) > Re) && this._append`L${c},${l}`, n && (d < 0 && (d = d % Le + Le), d > ze ? this._append`A${n},${n},0,1,${u},${e - o},${t - s}A${n},${n},0,1,${u},${this._x1 = c},${this._y1 = l}` : d > Re && this._append`A${n},${n},0,${+(d >= Ie)},${u},${this._x1 = e + n * Math.cos(i)},${this._y1 = t + n * Math.sin(i)}`);
	}
	rect(e, t, n, r) {
		this._append`M${this._x0 = this._x1 = +e},${this._y0 = this._y1 = +t}h${n = +n}v${+r}h${-n}Z`;
	}
	toString() {
		return this._;
	}
};
function Ue() {
	return new He();
}
Ue.prototype = He.prototype;
//#endregion
//#region node_modules/d3-shape/src/path.js
function We(e) {
	let t = 3;
	return e.digits = function(n) {
		if (!arguments.length) return t;
		if (n == null) t = null;
		else {
			let e = Math.floor(n);
			if (!(e >= 0)) throw RangeError(`invalid digits: ${n}`);
			t = e;
		}
		return e;
	}, () => new He(t);
}
Array.prototype.slice;
function Ge(e) {
	return typeof e == "object" && "length" in e ? e : Array.from(e);
}
//#endregion
//#region node_modules/d3-shape/src/curve/linear.js
function Ke(e) {
	this._context = e;
}
Ke.prototype = {
	areaStart: function() {
		this._line = 0;
	},
	areaEnd: function() {
		this._line = NaN;
	},
	lineStart: function() {
		this._point = 0;
	},
	lineEnd: function() {
		(this._line || this._line !== 0 && this._point === 1) && this._context.closePath(), this._line = 1 - this._line;
	},
	point: function(e, t) {
		switch (e = +e, t = +t, this._point) {
			case 0:
				this._point = 1, this._line ? this._context.lineTo(e, t) : this._context.moveTo(e, t);
				break;
			case 1: this._point = 2;
			default:
				this._context.lineTo(e, t);
				break;
		}
	}
};
function qe(e) {
	return new Ke(e);
}
//#endregion
//#region node_modules/d3-shape/src/point.js
function Je(e) {
	return e[0];
}
function Ye(e) {
	return e[1];
}
//#endregion
//#region node_modules/d3-shape/src/line.js
function Xe(e, t) {
	var n = Fe(!0), r = null, i = qe, a = null, o = We(s);
	e = typeof e == "function" ? e : e === void 0 ? Je : Fe(e), t = typeof t == "function" ? t : t === void 0 ? Ye : Fe(t);
	function s(s) {
		var c, l = (s = Ge(s)).length, u, d = !1, f;
		for (r == null && (a = i(f = o())), c = 0; c <= l; ++c) !(c < l && n(u = s[c], c, s)) === d && ((d = !d) ? a.lineStart() : a.lineEnd()), d && a.point(+e(u, c, s), +t(u, c, s));
		if (f) return a = null, f + "" || null;
	}
	return s.x = function(t) {
		return arguments.length ? (e = typeof t == "function" ? t : Fe(+t), s) : e;
	}, s.y = function(e) {
		return arguments.length ? (t = typeof e == "function" ? e : Fe(+e), s) : t;
	}, s.defined = function(e) {
		return arguments.length ? (n = typeof e == "function" ? e : Fe(!!e), s) : n;
	}, s.curve = function(e) {
		return arguments.length ? (i = e, r != null && (a = i(r)), s) : i;
	}, s.context = function(e) {
		return arguments.length ? (e == null ? r = a = null : a = i(r = e), s) : r;
	}, s;
}
//#endregion
//#region node_modules/d3-shape/src/area.js
function Ze(e, t, n) {
	var r = null, i = Fe(!0), a = null, o = qe, s = null, c = We(l);
	e = typeof e == "function" ? e : e === void 0 ? Je : Fe(+e), t = typeof t == "function" ? t : Fe(t === void 0 ? 0 : +t), n = typeof n == "function" ? n : n === void 0 ? Ye : Fe(+n);
	function l(l) {
		var u, d, f, p = (l = Ge(l)).length, m, h = !1, g, _ = Array(p), v = Array(p);
		for (a == null && (s = o(g = c())), u = 0; u <= p; ++u) {
			if (!(u < p && i(m = l[u], u, l)) === h) if (h = !h) d = u, s.areaStart(), s.lineStart();
			else {
				for (s.lineEnd(), s.lineStart(), f = u - 1; f >= d; --f) s.point(_[f], v[f]);
				s.lineEnd(), s.areaEnd();
			}
			h && (_[u] = +e(m, u, l), v[u] = +t(m, u, l), s.point(r ? +r(m, u, l) : _[u], n ? +n(m, u, l) : v[u]));
		}
		if (g) return s = null, g + "" || null;
	}
	function u() {
		return Xe().defined(i).curve(o).context(a);
	}
	return l.x = function(t) {
		return arguments.length ? (e = typeof t == "function" ? t : Fe(+t), r = null, l) : e;
	}, l.x0 = function(t) {
		return arguments.length ? (e = typeof t == "function" ? t : Fe(+t), l) : e;
	}, l.x1 = function(e) {
		return arguments.length ? (r = e == null ? null : typeof e == "function" ? e : Fe(+e), l) : r;
	}, l.y = function(e) {
		return arguments.length ? (t = typeof e == "function" ? e : Fe(+e), n = null, l) : t;
	}, l.y0 = function(e) {
		return arguments.length ? (t = typeof e == "function" ? e : Fe(+e), l) : t;
	}, l.y1 = function(e) {
		return arguments.length ? (n = e == null ? null : typeof e == "function" ? e : Fe(+e), l) : n;
	}, l.lineX0 = l.lineY0 = function() {
		return u().x(e).y(t);
	}, l.lineY1 = function() {
		return u().x(e).y(n);
	}, l.lineX1 = function() {
		return u().x(r).y(t);
	}, l.defined = function(e) {
		return arguments.length ? (i = typeof e == "function" ? e : Fe(!!e), l) : i;
	}, l.curve = function(e) {
		return arguments.length ? (o = e, a != null && (s = o(a)), l) : o;
	}, l.context = function(e) {
		return arguments.length ? (e == null ? a = s = null : s = o(a = e), l) : a;
	}, l;
}
//#endregion
//#region node_modules/d3-shape/src/curve/bump.js
var Qe = class {
	constructor(e, t) {
		this._context = e, this._x = t;
	}
	areaStart() {
		this._line = 0;
	}
	areaEnd() {
		this._line = NaN;
	}
	lineStart() {
		this._point = 0;
	}
	lineEnd() {
		(this._line || this._line !== 0 && this._point === 1) && this._context.closePath(), this._line = 1 - this._line;
	}
	point(e, t) {
		switch (e = +e, t = +t, this._point) {
			case 0:
				this._point = 1, this._line ? this._context.lineTo(e, t) : this._context.moveTo(e, t);
				break;
			case 1: this._point = 2;
			default:
				this._x ? this._context.bezierCurveTo(this._x0 = (this._x0 + e) / 2, this._y0, this._x0, t, e, t) : this._context.bezierCurveTo(this._x0, this._y0 = (this._y0 + t) / 2, e, this._y0, e, t);
				break;
		}
		this._x0 = e, this._y0 = t;
	}
};
function $e(e) {
	return new Qe(e, !0);
}
function et(e) {
	return new Qe(e, !1);
}
//#endregion
//#region node_modules/d3-shape/src/noop.js
function tt() {}
//#endregion
//#region node_modules/d3-shape/src/curve/basis.js
function nt(e, t, n) {
	e._context.bezierCurveTo((2 * e._x0 + e._x1) / 3, (2 * e._y0 + e._y1) / 3, (e._x0 + 2 * e._x1) / 3, (e._y0 + 2 * e._y1) / 3, (e._x0 + 4 * e._x1 + t) / 6, (e._y0 + 4 * e._y1 + n) / 6);
}
function rt(e) {
	this._context = e;
}
rt.prototype = {
	areaStart: function() {
		this._line = 0;
	},
	areaEnd: function() {
		this._line = NaN;
	},
	lineStart: function() {
		this._x0 = this._x1 = this._y0 = this._y1 = NaN, this._point = 0;
	},
	lineEnd: function() {
		switch (this._point) {
			case 3: nt(this, this._x1, this._y1);
			case 2:
				this._context.lineTo(this._x1, this._y1);
				break;
		}
		(this._line || this._line !== 0 && this._point === 1) && this._context.closePath(), this._line = 1 - this._line;
	},
	point: function(e, t) {
		switch (e = +e, t = +t, this._point) {
			case 0:
				this._point = 1, this._line ? this._context.lineTo(e, t) : this._context.moveTo(e, t);
				break;
			case 1:
				this._point = 2;
				break;
			case 2: this._point = 3, this._context.lineTo((5 * this._x0 + this._x1) / 6, (5 * this._y0 + this._y1) / 6);
			default:
				nt(this, e, t);
				break;
		}
		this._x0 = this._x1, this._x1 = e, this._y0 = this._y1, this._y1 = t;
	}
};
function it(e) {
	return new rt(e);
}
//#endregion
//#region node_modules/d3-shape/src/curve/basisClosed.js
function at(e) {
	this._context = e;
}
at.prototype = {
	areaStart: tt,
	areaEnd: tt,
	lineStart: function() {
		this._x0 = this._x1 = this._x2 = this._x3 = this._x4 = this._y0 = this._y1 = this._y2 = this._y3 = this._y4 = NaN, this._point = 0;
	},
	lineEnd: function() {
		switch (this._point) {
			case 1:
				this._context.moveTo(this._x2, this._y2), this._context.closePath();
				break;
			case 2:
				this._context.moveTo((this._x2 + 2 * this._x3) / 3, (this._y2 + 2 * this._y3) / 3), this._context.lineTo((this._x3 + 2 * this._x2) / 3, (this._y3 + 2 * this._y2) / 3), this._context.closePath();
				break;
			case 3:
				this.point(this._x2, this._y2), this.point(this._x3, this._y3), this.point(this._x4, this._y4);
				break;
		}
	},
	point: function(e, t) {
		switch (e = +e, t = +t, this._point) {
			case 0:
				this._point = 1, this._x2 = e, this._y2 = t;
				break;
			case 1:
				this._point = 2, this._x3 = e, this._y3 = t;
				break;
			case 2:
				this._point = 3, this._x4 = e, this._y4 = t, this._context.moveTo((this._x0 + 4 * this._x1 + e) / 6, (this._y0 + 4 * this._y1 + t) / 6);
				break;
			default:
				nt(this, e, t);
				break;
		}
		this._x0 = this._x1, this._x1 = e, this._y0 = this._y1, this._y1 = t;
	}
};
function ot(e) {
	return new at(e);
}
//#endregion
//#region node_modules/d3-shape/src/curve/basisOpen.js
function st(e) {
	this._context = e;
}
st.prototype = {
	areaStart: function() {
		this._line = 0;
	},
	areaEnd: function() {
		this._line = NaN;
	},
	lineStart: function() {
		this._x0 = this._x1 = this._y0 = this._y1 = NaN, this._point = 0;
	},
	lineEnd: function() {
		(this._line || this._line !== 0 && this._point === 3) && this._context.closePath(), this._line = 1 - this._line;
	},
	point: function(e, t) {
		switch (e = +e, t = +t, this._point) {
			case 0:
				this._point = 1;
				break;
			case 1:
				this._point = 2;
				break;
			case 2:
				this._point = 3;
				var n = (this._x0 + 4 * this._x1 + e) / 6, r = (this._y0 + 4 * this._y1 + t) / 6;
				this._line ? this._context.lineTo(n, r) : this._context.moveTo(n, r);
				break;
			case 3: this._point = 4;
			default:
				nt(this, e, t);
				break;
		}
		this._x0 = this._x1, this._x1 = e, this._y0 = this._y1, this._y1 = t;
	}
};
function ct(e) {
	return new st(e);
}
//#endregion
//#region node_modules/d3-shape/src/curve/linearClosed.js
function lt(e) {
	this._context = e;
}
lt.prototype = {
	areaStart: tt,
	areaEnd: tt,
	lineStart: function() {
		this._point = 0;
	},
	lineEnd: function() {
		this._point && this._context.closePath();
	},
	point: function(e, t) {
		e = +e, t = +t, this._point ? this._context.lineTo(e, t) : (this._point = 1, this._context.moveTo(e, t));
	}
};
function ut(e) {
	return new lt(e);
}
//#endregion
//#region node_modules/d3-shape/src/curve/monotone.js
function dt(e) {
	return e < 0 ? -1 : 1;
}
function ft(e, t, n) {
	var r = e._x1 - e._x0, i = t - e._x1, a = (e._y1 - e._y0) / (r || i < 0 && -0), o = (n - e._y1) / (i || r < 0 && -0), s = (a * i + o * r) / (r + i);
	return (dt(a) + dt(o)) * Math.min(Math.abs(a), Math.abs(o), .5 * Math.abs(s)) || 0;
}
function pt(e, t) {
	var n = e._x1 - e._x0;
	return n ? (3 * (e._y1 - e._y0) / n - t) / 2 : t;
}
function mt(e, t, n) {
	var r = e._x0, i = e._y0, a = e._x1, o = e._y1, s = (a - r) / 3;
	e._context.bezierCurveTo(r + s, i + s * t, a - s, o - s * n, a, o);
}
function ht(e) {
	this._context = e;
}
ht.prototype = {
	areaStart: function() {
		this._line = 0;
	},
	areaEnd: function() {
		this._line = NaN;
	},
	lineStart: function() {
		this._x0 = this._x1 = this._y0 = this._y1 = this._t0 = NaN, this._point = 0;
	},
	lineEnd: function() {
		switch (this._point) {
			case 2:
				this._context.lineTo(this._x1, this._y1);
				break;
			case 3:
				mt(this, this._t0, pt(this, this._t0));
				break;
		}
		(this._line || this._line !== 0 && this._point === 1) && this._context.closePath(), this._line = 1 - this._line;
	},
	point: function(e, t) {
		var n = NaN;
		if (e = +e, t = +t, !(e === this._x1 && t === this._y1)) {
			switch (this._point) {
				case 0:
					this._point = 1, this._line ? this._context.lineTo(e, t) : this._context.moveTo(e, t);
					break;
				case 1:
					this._point = 2;
					break;
				case 2:
					this._point = 3, mt(this, pt(this, n = ft(this, e, t)), n);
					break;
				default:
					mt(this, this._t0, n = ft(this, e, t));
					break;
			}
			this._x0 = this._x1, this._x1 = e, this._y0 = this._y1, this._y1 = t, this._t0 = n;
		}
	}
};
function gt(e) {
	this._context = new _t(e);
}
(gt.prototype = Object.create(ht.prototype)).point = function(e, t) {
	ht.prototype.point.call(this, t, e);
};
function _t(e) {
	this._context = e;
}
_t.prototype = {
	moveTo: function(e, t) {
		this._context.moveTo(t, e);
	},
	closePath: function() {
		this._context.closePath();
	},
	lineTo: function(e, t) {
		this._context.lineTo(t, e);
	},
	bezierCurveTo: function(e, t, n, r, i, a) {
		this._context.bezierCurveTo(t, e, r, n, a, i);
	}
};
function vt(e) {
	return new ht(e);
}
function yt(e) {
	return new gt(e);
}
//#endregion
//#region node_modules/d3-shape/src/curve/natural.js
function bt(e) {
	this._context = e;
}
bt.prototype = {
	areaStart: function() {
		this._line = 0;
	},
	areaEnd: function() {
		this._line = NaN;
	},
	lineStart: function() {
		this._x = [], this._y = [];
	},
	lineEnd: function() {
		var e = this._x, t = this._y, n = e.length;
		if (n) if (this._line ? this._context.lineTo(e[0], t[0]) : this._context.moveTo(e[0], t[0]), n === 2) this._context.lineTo(e[1], t[1]);
		else for (var r = xt(e), i = xt(t), a = 0, o = 1; o < n; ++a, ++o) this._context.bezierCurveTo(r[0][a], i[0][a], r[1][a], i[1][a], e[o], t[o]);
		(this._line || this._line !== 0 && n === 1) && this._context.closePath(), this._line = 1 - this._line, this._x = this._y = null;
	},
	point: function(e, t) {
		this._x.push(+e), this._y.push(+t);
	}
};
function xt(e) {
	var t, n = e.length - 1, r, i = Array(n), a = Array(n), o = Array(n);
	for (i[0] = 0, a[0] = 2, o[0] = e[0] + 2 * e[1], t = 1; t < n - 1; ++t) i[t] = 1, a[t] = 4, o[t] = 4 * e[t] + 2 * e[t + 1];
	for (i[n - 1] = 2, a[n - 1] = 7, o[n - 1] = 8 * e[n - 1] + e[n], t = 1; t < n; ++t) r = i[t] / a[t - 1], a[t] -= r, o[t] -= r * o[t - 1];
	for (i[n - 1] = o[n - 1] / a[n - 1], t = n - 2; t >= 0; --t) i[t] = (o[t] - i[t + 1]) / a[t];
	for (a[n - 1] = (e[n] + i[n - 1]) / 2, t = 0; t < n - 1; ++t) a[t] = 2 * e[t + 1] - i[t + 1];
	return [i, a];
}
function St(e) {
	return new bt(e);
}
//#endregion
//#region node_modules/d3-shape/src/curve/step.js
function Ct(e, t) {
	this._context = e, this._t = t;
}
Ct.prototype = {
	areaStart: function() {
		this._line = 0;
	},
	areaEnd: function() {
		this._line = NaN;
	},
	lineStart: function() {
		this._x = this._y = NaN, this._point = 0;
	},
	lineEnd: function() {
		0 < this._t && this._t < 1 && this._point === 2 && this._context.lineTo(this._x, this._y), (this._line || this._line !== 0 && this._point === 1) && this._context.closePath(), this._line >= 0 && (this._t = 1 - this._t, this._line = 1 - this._line);
	},
	point: function(e, t) {
		switch (e = +e, t = +t, this._point) {
			case 0:
				this._point = 1, this._line ? this._context.lineTo(e, t) : this._context.moveTo(e, t);
				break;
			case 1: this._point = 2;
			default:
				if (this._t <= 0) this._context.lineTo(this._x, t), this._context.lineTo(e, t);
				else {
					var n = this._x * (1 - this._t) + e * this._t;
					this._context.lineTo(n, this._y), this._context.lineTo(n, t);
				}
				break;
		}
		this._x = e, this._y = t;
	}
};
function wt(e) {
	return new Ct(e, .5);
}
function Tt(e) {
	return new Ct(e, 0);
}
function Et(e) {
	return new Ct(e, 1);
}
//#endregion
//#region node_modules/d3-shape/src/offset/none.js
function Dt(e, t) {
	if ((o = e.length) > 1) for (var n = 1, r, i, a = e[t[0]], o, s = a.length; n < o; ++n) for (i = a, a = e[t[n]], r = 0; r < s; ++r) a[r][1] += a[r][0] = isNaN(i[r][1]) ? i[r][0] : i[r][1];
}
//#endregion
//#region node_modules/d3-shape/src/order/none.js
function Ot(e) {
	for (var t = e.length, n = Array(t); --t >= 0;) n[t] = t;
	return n;
}
//#endregion
//#region node_modules/d3-shape/src/stack.js
function kt(e, t) {
	return e[t];
}
function At(e) {
	let t = [];
	return t.key = e, t;
}
function jt() {
	var e = Fe([]), t = Ot, n = Dt, r = kt;
	function i(i) {
		var a = Array.from(e.apply(this, arguments), At), o, s = a.length, c = -1, l;
		for (let e of i) for (o = 0, ++c; o < s; ++o) (a[o][c] = [0, +r(e, a[o].key, c, i)]).data = e;
		for (o = 0, l = Ge(t(a)); o < s; ++o) a[l[o]].index = o;
		return n(a, l), a;
	}
	return i.keys = function(t) {
		return arguments.length ? (e = typeof t == "function" ? t : Fe(Array.from(t)), i) : e;
	}, i.value = function(e) {
		return arguments.length ? (r = typeof e == "function" ? e : Fe(+e), i) : r;
	}, i.order = function(e) {
		return arguments.length ? (t = e == null ? Ot : typeof e == "function" ? e : Fe(Array.from(e)), i) : t;
	}, i.offset = function(e) {
		return arguments.length ? (n = e == null ? Dt : e, i) : n;
	}, i;
}
//#endregion
//#region node_modules/d3-shape/src/offset/expand.js
function Mt(e, t) {
	if ((r = e.length) > 0) {
		for (var n, r, i = 0, a = e[0].length, o; i < a; ++i) {
			for (o = n = 0; n < r; ++n) o += e[n][i][1] || 0;
			if (o) for (n = 0; n < r; ++n) e[n][i][1] /= o;
		}
		Dt(e, t);
	}
}
//#endregion
//#region node_modules/d3-shape/src/offset/silhouette.js
function Nt(e, t) {
	if ((i = e.length) > 0) {
		for (var n = 0, r = e[t[0]], i, a = r.length; n < a; ++n) {
			for (var o = 0, s = 0; o < i; ++o) s += e[o][n][1] || 0;
			r[n][1] += r[n][0] = -s / 2;
		}
		Dt(e, t);
	}
}
//#endregion
//#region node_modules/d3-shape/src/offset/wiggle.js
function Pt(e, t) {
	if (!(!((o = e.length) > 0) || !((a = (i = e[t[0]]).length) > 0))) {
		for (var n = 0, r = 1, i, a, o; r < a; ++r) {
			for (var s = 0, c = 0, l = 0; s < o; ++s) {
				for (var u = e[t[s]], d = u[r][1] || 0, f = (d - (u[r - 1][1] || 0)) / 2, p = 0; p < s; ++p) {
					var m = e[t[p]], h = m[r][1] || 0, g = m[r - 1][1] || 0;
					f += h - g;
				}
				c += d, l += f * d;
			}
			i[r - 1][1] += i[r - 1][0] = n, c && (n -= l / c);
		}
		i[r - 1][1] += i[r - 1][0] = n, Dt(e, t);
	}
}
//#endregion
//#region node_modules/es-toolkit/dist/_internal/isUnsafeProperty.mjs
function Ft(e) {
	return e === "__proto__";
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/isDeepKey.mjs
function It(e) {
	switch (typeof e) {
		case "number":
		case "symbol": return !1;
		case "string": return e.includes(".") || e.includes("[") || e.includes("]");
	}
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/toKey.mjs
function Lt(e) {
	var t;
	return typeof e == "string" || typeof e == "symbol" ? e : Object.is(e == null || (t = e.valueOf) == null ? void 0 : t.call(e), -0) ? "-0" : String(e);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/util/toString.mjs
function Rt(e) {
	if (e == null) return "";
	if (typeof e == "string") return e;
	if (Array.isArray(e)) return e.map(Rt).join(",");
	let t = String(e);
	return t === "0" && Object.is(Number(e), -0) ? "-0" : t;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/util/toPath.mjs
function zt(e) {
	if (Array.isArray(e)) return e.map(Lt);
	if (typeof e == "symbol") return [e];
	e = Rt(e);
	let t = [], n = e.length;
	if (n === 0) return t;
	let r = 0, i = "", a = "", o = !1;
	for (e.charCodeAt(0) === 46 && t.push(""); r < n;) {
		let s = e[r];
		if (a) s === "\\" && r + 1 < n ? (r++, i += e[r]) : s === a ? a = "" : i += s;
		else if (o) s === "\"" || s === "'" ? a = s : s === "]" ? (o = !1, t.push(i), i = "") : i += s;
		else if (s === "[") o = !0, i && (t.push(i), i = "");
		else if (s === ".") {
			i && (t.push(i), i = "");
			let n = e[r + 1];
			(n === void 0 || n === ".") && t.push("");
		} else i += s;
		r++;
	}
	return i && t.push(i), t;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/object/get.mjs
function Bt(e, t, n) {
	if (e == null) return n;
	switch (typeof t) {
		case "string": {
			if (Ft(t)) return n;
			let r = e[t];
			return r === void 0 ? It(t) && !Object.hasOwn(e, t) ? Bt(e, zt(t), n) : n : r;
		}
		case "number":
		case "symbol": {
			typeof t == "number" && (t = Lt(t));
			let r = e[t];
			return r === void 0 ? n : r;
		}
		default: {
			if (Array.isArray(t)) return Vt(e, t, n);
			if (t = Object.is(t == null ? void 0 : t.valueOf(), -0) ? "-0" : String(t), Ft(t)) return n;
			let r = e[t];
			return r === void 0 ? n : r;
		}
	}
}
function Vt(e, t, n) {
	if (t.length === 0) return n;
	let r = e;
	for (let e = 0; e < t.length; e++) {
		if (r == null || Ft(t[e])) return n;
		r = r[t[e]];
	}
	return r === void 0 ? n : r;
}
//#endregion
//#region node_modules/recharts/es6/util/round.js
var Ht = 4;
function Ut(e) {
	var t = 10 ** (arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : Ht), n = Math.round(e * t) / t;
	return Object.is(n, -0) ? 0 : n;
}
function Wt(e) {
	var t = [...arguments].slice(1);
	return e.reduce((e, n, r) => {
		var i = t[r - 1];
		return typeof i == "string" ? e + i + n : i === void 0 ? e + n : e + Ut(i) + n;
	}, "");
}
//#endregion
//#region node_modules/recharts/es6/util/DataUtils.js
var Gt = (e) => e === 0 ? 0 : e > 0 ? 1 : -1, Kt = (e) => typeof e == "number" && e != +e, F = (e) => typeof e == "string" && e.length > 1 && e.indexOf("%") === e.length - 1, I = (e) => (typeof e == "number" || e instanceof Number) && !Kt(e), qt = (e) => I(e) || typeof e == "string", Jt = 0, Yt = (e) => {
	var t = ++Jt;
	return `${e || ""}${t}`;
}, Xt = function(e, t) {
	var n = arguments.length > 2 && arguments[2] !== void 0 ? arguments[2] : 0, r = arguments.length > 3 && arguments[3] !== void 0 && arguments[3];
	if (!I(e) && typeof e != "string") return n;
	var i;
	if (F(e)) {
		if (t == null) return n;
		var a = e.indexOf("%");
		i = t * parseFloat(e.slice(0, a)) / 100;
	} else i = +e;
	return Kt(i) && (i = n), r && t != null && i > t && (i = t), i;
}, Zt = (e) => {
	if (!Array.isArray(e)) return !1;
	for (var t = e.length, n = {}, r = 0; r < t; r++) if (!n[String(e[r])]) n[String(e[r])] = !0;
	else return !0;
	return !1;
};
function Qt(e, t, n) {
	return I(e) && I(t) ? Ut(e + n * (t - e)) : t;
}
function $t(e, t, n) {
	if (!(!e || !e.length)) return e.find((e) => e && (typeof t == "function" ? t(e) : Bt(e, t)) === n);
}
var en = (e) => e == null, tn = (e) => en(e) ? e : `${e.charAt(0).toUpperCase()}${e.slice(1)}`;
function nn(e) {
	return e != null;
}
function rn() {}
//#endregion
//#region node_modules/recharts/es6/util/types.js
var an = (e) => "radius" in e && "startAngle" in e && "endAngle" in e, on = (e, t) => {
	if (!e || typeof e == "function" || typeof e == "boolean") return null;
	var n = e;
	if (/*#__PURE__*/ (0, C.isValidElement)(e) && (n = e.props), typeof n != "object" && typeof n != "function") return null;
	var r = {};
	return Object.keys(n).forEach((e) => {
		_e(e) && typeof n[e] == "function" && (r[e] = t || ((t) => n[e](n, t)));
	}), r;
}, sn = (e, t, n) => (r) => (e(t, n, r), null), cn = (e, t, n) => {
	if (e === null || typeof e != "object" && typeof e != "function") return null;
	var r = null;
	return Object.keys(e).forEach((i) => {
		var a = e[i];
		_e(i) && typeof a == "function" && (r || (r = {}), r[i] = sn(a, t, n));
	}), r;
};
//#endregion
//#region node_modules/recharts/es6/util/resolveDefaultProps.js
function ln(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function un(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? ln(Object(n), !0).forEach(function(t) {
			dn(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : ln(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function dn(e, t, n) {
	return (t = fn(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function fn(e) {
	var t = pn(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function pn(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function mn(e, t) {
	var n = un({}, e), r = t;
	return Object.keys(t).reduce((e, t) => (e[t] === void 0 && r[t] !== void 0 && (e[t] = r[t]), e), n);
}
//#endregion
//#region node_modules/es-toolkit/dist/array/uniqBy.mjs
function hn(e, t) {
	let n = /* @__PURE__ */ new Map();
	for (let r = 0; r < e.length; r++) {
		let i = e[r], a = t(i, r, e);
		n.has(a) || n.set(a, i);
	}
	return Array.from(n.values());
}
//#endregion
//#region node_modules/es-toolkit/dist/function/ary.mjs
function gn(e, t) {
	return function(...n) {
		return e.apply(this, n.slice(0, t));
	};
}
//#endregion
//#region node_modules/es-toolkit/dist/function/identity.mjs
function _n(e) {
	return e;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/object/property.mjs
function vn(e) {
	return function(t) {
		return Bt(t, e);
	};
}
//#endregion
//#region node_modules/es-toolkit/dist/predicate/isPrimitive.mjs
function yn(e) {
	return e == null || typeof e != "object" && typeof e != "function";
}
//#endregion
//#region node_modules/es-toolkit/dist/predicate/isTypedArray.mjs
function bn(e) {
	return ArrayBuffer.isView(e) && !(e instanceof DataView);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/getSymbols.mjs
function xn(e) {
	return Object.getOwnPropertySymbols(e).filter((t) => Object.prototype.propertyIsEnumerable.call(e, t));
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/getTag.mjs
function Sn(e) {
	return e == null ? e === void 0 ? "[object Undefined]" : "[object Null]" : Object.prototype.toString.call(e);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/tags.mjs
var Cn = "[object RegExp]", wn = "[object String]", Tn = "[object Number]", En = "[object Boolean]", Dn = "[object Arguments]", On = "[object Symbol]", kn = "[object Date]", An = "[object Map]", jn = "[object Set]", Mn = "[object Array]", Nn = "[object ArrayBuffer]", Pn = "[object Object]", Fn = "[object DataView]", In = "[object Uint8Array]", Ln = "[object Uint8ClampedArray]", Rn = "[object Uint16Array]", zn = "[object Uint32Array]", Bn = "[object Int8Array]", Vn = "[object Int16Array]", Hn = "[object Int32Array]", Un = "[object Float32Array]", Wn = "[object Float64Array]", Gn = typeof globalThis == "object" && globalThis || typeof window == "object" && window || typeof self == "object" && self || typeof global == "object" && global || (function() {
	return this;
})();
//#endregion
//#region node_modules/es-toolkit/dist/predicate/isBuffer.mjs
function Kn(e) {
	return Gn.Buffer !== void 0 && Gn.Buffer.isBuffer(e);
}
//#endregion
//#region node_modules/es-toolkit/dist/object/cloneDeepWith.mjs
function qn(e, t) {
	return Jn(e, void 0, e, /* @__PURE__ */ new Map(), t);
}
function Jn(e, t, n, r = /* @__PURE__ */ new Map(), i = void 0) {
	let a = i == null ? void 0 : i(e, t, n, r);
	if (a !== void 0) return a;
	if (yn(e)) return e;
	if (r.has(e)) return r.get(e);
	if (Array.isArray(e)) {
		let t = Array(e.length);
		r.set(e, t);
		for (let a = 0; a < e.length; a++) t[a] = Jn(e[a], a, n, r, i);
		return Object.hasOwn(e, "index") && (t.index = e.index), Object.hasOwn(e, "input") && (t.input = e.input), t;
	}
	if (e instanceof Date) return new Date(e.getTime());
	if (e instanceof RegExp) {
		let t = new RegExp(e.source, e.flags);
		return t.lastIndex = e.lastIndex, t;
	}
	if (e instanceof Map) {
		let t = /* @__PURE__ */ new Map();
		r.set(e, t);
		for (let [a, o] of e) t.set(a, Jn(o, a, n, r, i));
		return t;
	}
	if (e instanceof Set) {
		let t = /* @__PURE__ */ new Set();
		r.set(e, t);
		for (let a of e) t.add(Jn(a, void 0, n, r, i));
		return t;
	}
	if (Kn(e)) return e.subarray();
	if (bn(e)) {
		let t = new (Object.getPrototypeOf(e)).constructor(e.length);
		r.set(e, t);
		for (let a = 0; a < e.length; a++) t[a] = Jn(e[a], a, n, r, i);
		return t;
	}
	if (e instanceof ArrayBuffer || typeof SharedArrayBuffer < "u" && e instanceof SharedArrayBuffer) return e.slice(0);
	if (e instanceof DataView) {
		let t = new DataView(e.buffer.slice(0), e.byteOffset, e.byteLength);
		return r.set(e, t), Yn(t, e, n, r, i), t;
	}
	if (typeof File < "u" && e instanceof File) {
		let t = new File([e], e.name, { type: e.type });
		return r.set(e, t), Yn(t, e, n, r, i), t;
	}
	if (typeof Blob < "u" && e instanceof Blob) {
		let t = new Blob([e], { type: e.type });
		return r.set(e, t), Yn(t, e, n, r, i), t;
	}
	if (e instanceof Error) {
		let t = structuredClone(e);
		return r.set(e, t), t.message = e.message, t.name = e.name, t.stack = e.stack, t.cause = e.cause, t.constructor = e.constructor, Yn(t, e, n, r, i), t;
	}
	if (e instanceof Boolean) {
		let t = new Boolean(e.valueOf());
		return r.set(e, t), Yn(t, e, n, r, i), t;
	}
	if (e instanceof Number) {
		let t = new Number(e.valueOf());
		return r.set(e, t), Yn(t, e, n, r, i), t;
	}
	if (e instanceof String) {
		let t = new String(e.valueOf());
		return r.set(e, t), Yn(t, e, n, r, i), t;
	}
	if (typeof e == "object" && Xn(e)) {
		let t = Object.create(Object.getPrototypeOf(e));
		return r.set(e, t), Yn(t, e, n, r, i), t;
	}
	return e;
}
function Yn(e, t, n = e, r, i) {
	let a = [...Object.keys(t), ...xn(t)];
	for (let o = 0; o < a.length; o++) {
		let s = a[o], c = Object.getOwnPropertyDescriptor(e, s);
		(c == null || c.writable) && (e[s] = Jn(t[s], s, n, r, i));
	}
}
function Xn(e) {
	switch (Sn(e)) {
		case Dn:
		case Mn:
		case Nn:
		case Fn:
		case En:
		case kn:
		case Un:
		case Wn:
		case Bn:
		case Vn:
		case Hn:
		case An:
		case Tn:
		case Pn:
		case Cn:
		case jn:
		case wn:
		case On:
		case In:
		case Ln:
		case Rn:
		case zn: return !0;
		default: return !1;
	}
}
//#endregion
//#region node_modules/es-toolkit/dist/object/cloneDeep.mjs
function Zn(e) {
	return Jn(e, void 0, e, /* @__PURE__ */ new Map(), void 0);
}
//#endregion
//#region node_modules/es-toolkit/dist/_internal/isEqualsSameValueZero.mjs
function Qn(e, t) {
	return e === t || Number.isNaN(e) && Number.isNaN(t);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isObject.mjs
function $n(e) {
	return e !== null && (typeof e == "object" || typeof e == "function");
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isMatchWith.mjs
function er(e, t, n) {
	return typeof n == "function" ? tr(e, t, function e(t, r, i, a, o, s) {
		let c = n(t, r, i, a, o, s);
		return c === void 0 ? tr(t, r, e, s, !1) : !!c;
	}, /* @__PURE__ */ new Map(), !0) : er(e, t, () => void 0);
}
function tr(e, t, n, r, i = !1) {
	if (t === e) return !0;
	switch (typeof t) {
		case "object": return nr(e, t, n, r);
		case "function": return Object.keys(t).length > 0 ? tr(e, { ...t }, n, r, i) : Qn(e, t);
		default: return $n(e) && i ? typeof t != "string" || t === "" : Qn(e, t);
	}
}
function nr(e, t, n, r) {
	if (t == null) return !0;
	if (Array.isArray(t)) return ir(e, t, n, r);
	if (t instanceof Map) return rr(e, t, n, r);
	if (t instanceof Set) return ar(e, t, n, r);
	let i = Object.keys(t);
	if (e == null || yn(e)) return i.length === 0;
	if (i.length === 0) return !0;
	if (r != null && r.has(t)) return r.get(t) === e;
	r == null || r.set(t, e);
	try {
		for (let a = 0; a < i.length; a++) {
			let o = i[a];
			if (!yn(e) && !(o in e) || t[o] === void 0 && e[o] !== void 0 || t[o] === null && e[o] !== null || !n(e[o], t[o], o, e, t, r)) return !1;
		}
		return !0;
	} finally {
		r == null || r.delete(t);
	}
}
function rr(e, t, n, r) {
	if (t.size === 0) return !0;
	if (!(e instanceof Map)) return !1;
	for (let [i, a] of t.entries()) if (n(e.get(i), a, i, e, t, r) === !1) return !1;
	return !0;
}
function ir(e, t, n, r) {
	if (t.length === 0) return !0;
	if (!Array.isArray(e)) return !1;
	let i = /* @__PURE__ */ new Set();
	for (let a = 0; a < t.length; a++) {
		let o = t[a], s = !1;
		for (let c = 0; c < e.length; c++) {
			if (i.has(c)) continue;
			let l = e[c], u = !1;
			if (n(l, o, a, e, t, r) && (u = !0), u) {
				i.add(c), s = !0;
				break;
			}
		}
		if (!s) return !1;
	}
	return !0;
}
function ar(e, t, n, r) {
	return t.size === 0 || e instanceof Set && ir([...e], [...t], n, r);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isMatch.mjs
function or(e, t) {
	return er(e, t, () => void 0);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/matches.mjs
function sr(e) {
	return e = Zn(e), (t) => or(t, e);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/object/cloneDeepWith.mjs
function cr(e, t) {
	return qn(e, (n, r, i, a) => {
		let o = t == null ? void 0 : t(n, r, i, a);
		if (o !== void 0) return o;
		if (typeof e == "object") {
			if (Sn(e) === "[object Object]" && typeof e.constructor != "function") {
				let t = {};
				return a.set(e, t), Yn(t, e, i, a), t;
			}
			switch (Object.prototype.toString.call(e)) {
				case Tn:
				case wn:
				case En: {
					let t = new e.constructor(e == null ? void 0 : e.valueOf());
					return Yn(t, e), t;
				}
				case Dn: {
					let t = {};
					return Yn(t, e), t.length = e.length, t[Symbol.iterator] = e[Symbol.iterator], t;
				}
				default: return;
			}
		}
	});
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/object/cloneDeep.mjs
function lr(e) {
	return cr(e);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/isIndex.mjs
var ur = /^(?:0|[1-9]\d*)$/;
function dr(e, t = 2 ** 53 - 1) {
	switch (typeof e) {
		case "number": return Number.isInteger(e) && e >= 0 && e < t;
		case "symbol": return !1;
		case "string": return ur.test(e);
	}
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isArguments.mjs
function fr(e) {
	return typeof e == "object" && !!e && Sn(e) === "[object Arguments]";
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/object/has.mjs
function pr(e, t) {
	let n;
	if (n = Array.isArray(t) ? t : typeof t == "string" && It(t) && (e == null ? void 0 : e[t]) == null ? zt(t) : [t], n.length === 0) return !1;
	let r = e;
	for (let e = 0; e < n.length; e++) {
		let t = n[e];
		if ((r == null || !Object.hasOwn(r, t)) && !((Array.isArray(r) || fr(r)) && dr(t) && t < r.length)) return !1;
		r = r[t];
	}
	return !0;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/matchesProperty.mjs
function mr(e, t) {
	switch (typeof e) {
		case "object":
			Object.is(e == null ? void 0 : e.valueOf(), -0) && (e = "-0");
			break;
		case "number":
			e = Lt(e);
			break;
	}
	return t = lr(t), function(n) {
		let r = Bt(n, e);
		return r === void 0 ? pr(n, e) : t === void 0 ? r === void 0 : or(r, t);
	};
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/util/iteratee.mjs
function hr(e) {
	if (e == null) return _n;
	switch (typeof e) {
		case "function": return e;
		case "object": return Array.isArray(e) && e.length === 2 ? mr(e[0], e[1]) : sr(e);
		case "string":
		case "symbol":
		case "number": return vn(e);
	}
}
//#endregion
//#region node_modules/es-toolkit/dist/predicate/isLength.mjs
function gr(e) {
	return Number.isSafeInteger(e) && e >= 0;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isArrayLike.mjs
function _r(e) {
	return e != null && typeof e != "function" && gr(e.length);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isObjectLike.mjs
function vr(e) {
	return typeof e == "object" && !!e;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isArrayLikeObject.mjs
function yr(e) {
	return vr(e) && _r(e);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/array/uniqBy.mjs
function br(e, t = _n) {
	return yr(e) ? hn(Array.from(e), gn(hr(t), 1)) : [];
}
//#endregion
//#region node_modules/recharts/es6/util/payload/getUniqPayload.js
function xr(e, t, n) {
	return t === !0 ? br(e, n) : typeof t == "function" ? br(e, t) : e;
}
//#endregion
//#region node_modules/use-sync-external-store/cjs/use-sync-external-store-shim.production.js
var Sr = /* @__PURE__ */ o(((e) => {
	var t = d();
	function n(e, t) {
		return e === t && (e !== 0 || 1 / e == 1 / t) || e !== e && t !== t;
	}
	var r = typeof Object.is == "function" ? Object.is : n, i = t.useState, a = t.useEffect, o = t.useLayoutEffect, s = t.useDebugValue;
	function c(e, t) {
		var n = t(), r = i({ inst: {
			value: n,
			getSnapshot: t
		} }), c = r[0].inst, u = r[1];
		return o(function() {
			c.value = n, c.getSnapshot = t, l(c) && u({ inst: c });
		}, [
			e,
			n,
			t
		]), a(function() {
			return l(c) && u({ inst: c }), e(function() {
				l(c) && u({ inst: c });
			});
		}, [e]), s(n), n;
	}
	function l(e) {
		var t = e.getSnapshot;
		e = e.value;
		try {
			var n = t();
			return !r(e, n);
		} catch (e) {
			return !0;
		}
	}
	function u(e, t) {
		return t();
	}
	var f = typeof window > "u" || window.document === void 0 || window.document.createElement === void 0 ? u : c;
	e.useSyncExternalStore = t.useSyncExternalStore === void 0 ? f : t.useSyncExternalStore;
})), Cr = /* @__PURE__ */ o(((e, t) => {
	t.exports = Sr();
})), wr = /* @__PURE__ */ o(((e) => {
	var t = d(), n = Cr();
	function r(e, t) {
		return e === t && (e !== 0 || 1 / e == 1 / t) || e !== e && t !== t;
	}
	var i = typeof Object.is == "function" ? Object.is : r, a = n.useSyncExternalStore, o = t.useRef, s = t.useEffect, c = t.useMemo, l = t.useDebugValue;
	e.useSyncExternalStoreWithSelector = function(e, t, n, r, u) {
		var d = o(null);
		if (d.current === null) {
			var f = {
				hasValue: !1,
				value: null
			};
			d.current = f;
		} else f = d.current;
		d = c(function() {
			function e(e) {
				if (!a) {
					if (a = !0, o = e, e = r(e), u !== void 0 && f.hasValue) {
						var t = f.value;
						if (u(t, e)) return s = t;
					}
					return s = e;
				}
				if (t = s, i(o, e)) return t;
				var n = r(e);
				return u !== void 0 && u(t, n) ? (o = e, t) : (o = e, s = n);
			}
			var a = !1, o, s, c = n === void 0 ? null : n;
			return [function() {
				return e(t());
			}, c === null ? void 0 : function() {
				return e(c());
			}];
		}, [
			t,
			n,
			r,
			u
		]);
		var p = a(e, d[0], d[1]);
		return s(function() {
			f.hasValue = !0, f.value = p;
		}, [p]), l(p), p;
	};
})), Tr = /* @__PURE__ */ o(((e, t) => {
	t.exports = wr();
})), Er = /*#__PURE__*/ (0, C.createContext)(null), Dr = Tr(), Or = (e) => e, kr = () => {
	var e = (0, C.useContext)(Er);
	return e ? e.store.dispatch : Or;
}, Ar = () => {}, jr = () => Ar, Mr = (e, t) => e === t;
function L(e) {
	var t = (0, C.useContext)(Er), n = (0, C.useMemo)(() => t ? (t) => {
		if (t != null) return e(t);
	} : Ar, [t, e]);
	return (0, Dr.useSyncExternalStoreWithSelector)(t ? t.subscription.addNestedSub : jr, t ? t.store.getState : Ar, t ? t.store.getState : Ar, n, Mr);
}
//#endregion
//#region \0@oxc-project+runtime@0.139.0/helpers/esm/typeof.js
function Nr(e) {
	"@babel/helpers - typeof";
	return Nr = typeof Symbol == "function" && typeof Symbol.iterator == "symbol" ? function(e) {
		return typeof e;
	} : function(e) {
		return e && typeof Symbol == "function" && e.constructor === Symbol && e !== Symbol.prototype ? "symbol" : typeof e;
	}, Nr(e);
}
//#endregion
//#region \0@oxc-project+runtime@0.139.0/helpers/esm/toPrimitive.js
function Pr(e, t) {
	if (Nr(e) != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (Nr(r) != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
//#endregion
//#region \0@oxc-project+runtime@0.139.0/helpers/esm/toPropertyKey.js
function Fr(e) {
	var t = Pr(e, "string");
	return Nr(t) == "symbol" ? t : t + "";
}
//#endregion
//#region \0@oxc-project+runtime@0.139.0/helpers/esm/defineProperty.js
function Ir(e, t, n) {
	return (t = Fr(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
//#endregion
//#region node_modules/reselect/dist/reselect.mjs
function Lr(e, t = `expected a function, instead received ${typeof e}`) {
	if (typeof e != "function") throw TypeError(t);
}
function Rr(e, t = "expected all items to be functions, instead received the following types: ") {
	if (!e.every((e) => typeof e == "function")) {
		let n = e.map((e) => typeof e == "function" ? `function ${e.name || "unnamed"}()` : typeof e).join(", ");
		throw TypeError(`${t}[${n}]`);
	}
}
var zr = (e) => Array.isArray(e) ? e : [e];
function Br(e) {
	let t = Array.isArray(e[0]) ? e[0] : e;
	return Rr(t, "createSelector expects all input-selectors to be functions, but received the following types: "), t;
}
function Vr(e, t) {
	let n = [], { length: r } = e;
	for (let i = 0; i < r; i++) n.push(e[i].apply(null, t));
	return n;
}
var Hr = class {
	constructor(e) {
		this.value = e;
	}
	deref() {
		return this.value;
	}
}, Ur = typeof WeakRef > "u" ? Hr : WeakRef, Wr = 0, Gr = 1;
function Kr() {
	return {
		s: Wr,
		v: void 0,
		o: null,
		p: null
	};
}
function qr(e) {
	return e instanceof Ur ? e.deref() : e;
}
function Jr(e, t = {}) {
	let n = Kr(), { resultEqualityCheck: r } = t, i, a = 0;
	function o() {
		let t = n, { length: o } = arguments;
		for (let e = 0, n = o; e < n; e++) {
			let n = arguments[e];
			if (typeof n == "function" || typeof n == "object" && n) {
				let e = t.o;
				e === null && (t.o = e = /* @__PURE__ */ new WeakMap());
				let r = e.get(n);
				r === void 0 ? (t = Kr(), e.set(n, t)) : t = r;
			} else {
				let e = t.p;
				e === null && (t.p = e = /* @__PURE__ */ new Map());
				let r = e.get(n);
				r === void 0 ? (t = Kr(), e.set(n, t)) : t = r;
			}
		}
		let s = t, c;
		if (t.s === Gr) c = t.v;
		else if (c = e.apply(null, arguments), a++, r) {
			let e = qr(i);
			e != null && r(e, c) && (c = e, a !== 0 && a--), i = typeof c == "object" && c || typeof c == "function" ? /* @__PURE__ */ new Ur(c) : c;
		}
		return s.s = Gr, s.v = c, c;
	}
	return o.clearCache = () => {
		n = Kr(), o.resetResultsCount();
	}, o.resultsCount = () => a, o.resetResultsCount = () => {
		a = 0;
	}, o;
}
function Yr(e, ...t) {
	let n = typeof e == "function" ? {
		memoize: e,
		memoizeOptions: t
	} : e, r = (...e) => {
		let t = 0, r = 0, i, a = {}, o = e.pop();
		typeof o == "object" && (a = o, o = e.pop()), Lr(o, `createSelector expects an output function after the inputs, but received: [${typeof o}]`);
		let { memoize: s, memoizeOptions: c = [], argsMemoize: l = Jr, argsMemoizeOptions: u = [] } = {
			...n,
			...a
		}, d = zr(c), f = zr(u), p = Br(e), m = s(function() {
			return t++, o.apply(null, arguments);
		}, ...d), h = l(function() {
			r++;
			let e = Vr(p, arguments);
			return i = m.apply(null, e), i;
		}, ...f);
		return Object.assign(h, {
			resultFunc: o,
			memoizedResultFunc: m,
			dependencies: p,
			dependencyRecomputations: () => r,
			resetDependencyRecomputations: () => {
				r = 0;
			},
			lastResult: () => i,
			recomputations: () => t,
			resetRecomputations: () => {
				t = 0;
			},
			memoize: s,
			argsMemoize: l
		});
	};
	return Object.assign(r, { withTypes: () => r }), r;
}
var R = /* @__PURE__ */ Yr(Jr);
//#endregion
//#region node_modules/es-toolkit/dist/array/flatten.mjs
function Xr(e, t = 1) {
	let n = [], r = Math.floor(t), i = (e, t) => {
		for (let a = 0; a < e.length; a++) {
			let o = e[a];
			Array.isArray(o) && t < r ? i(o, t + 1) : n.push(o);
		}
	};
	return i(e, 0), n;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/isIterateeCall.mjs
function Zr(e, t, n) {
	return $n(n) && (typeof t == "number" && _r(n) && dr(t) && t < n.length || typeof t == "string" && t in n) ? Qn(n[t], e) : !1;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/compareValues.mjs
function Qr(e) {
	return typeof e == "symbol" ? 1 : e === null ? 2 : e === void 0 ? 3 : e === e ? 0 : 4;
}
var $r = (e, t, n) => {
	if (e !== t) {
		let r = Qr(e), i = Qr(t);
		if (r === i && r === 0) {
			if (e < t) return n === "desc" ? 1 : -1;
			if (e > t) return n === "desc" ? -1 : 1;
		}
		return n === "desc" ? i - r : r - i;
	}
	return 0;
};
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isSymbol.mjs
function ei(e) {
	return typeof e == "symbol" || e instanceof Symbol;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/isKey.mjs
var ti = /\.|\[(?:[^[\]]*|(["'])(?:(?!\1)[^\\]|\\.)*?\1)\]/, ni = /^\w*$/;
function ri(e, t) {
	return Array.isArray(e) ? !1 : typeof e == "number" || typeof e == "boolean" || e == null || ei(e) ? !0 : typeof e == "string" && (ni.test(e) || !ti.test(e)) || t != null && Object.hasOwn(t, e);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/array/orderBy.mjs
function ii(e, t, n, r) {
	if (e == null) return [];
	n = r ? void 0 : n, Array.isArray(e) || (e = Object.values(e)), Array.isArray(t) || (t = t == null ? [null] : [t]), t.length === 0 && (t = [null]), Array.isArray(n) || (n = n == null ? [] : [n]), n = n.map((e) => String(e));
	let i = (e, t) => {
		let n = e;
		for (let e = 0; e < t.length && n != null; ++e) n = n[t[e]];
		return n;
	}, a = (e, t) => t == null || e == null ? t : typeof e == "object" && "key" in e ? Object.hasOwn(t, e.key) ? t[e.key] : i(t, e.path) : typeof e == "function" ? e(t) : Array.isArray(e) ? i(t, e) : typeof t == "object" ? t[e] : t, o = t.map((e) => (Array.isArray(e) && e.length === 1 && (e = e[0]), e == null || typeof e == "function" || Array.isArray(e) || ri(e) ? e : {
		key: e,
		path: zt(e)
	}));
	return e.map((e) => ({
		original: e,
		criteria: o.map((t) => a(t, e))
	})).slice().sort((e, t) => {
		for (let r = 0; r < o.length; r++) {
			let i = $r(e.criteria[r], t.criteria[r], n[r]);
			if (i !== 0) return i;
		}
		return 0;
	}).map((e) => e.original);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/array/sortBy.mjs
function ai(e, ...t) {
	let n = t.length;
	return n > 1 && Zr(e, t[0], t[1]) ? t = [] : n > 2 && Zr(t[0], t[1], t[2]) && (t = [t[0]]), ii(e, Xr(t), ["asc"]);
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/legendSelectors.js
var oi = (e) => e.legend.settings, si = (e) => e.legend.size;
R([(e) => e.legend.payload, oi], (e, t) => {
	var n = t.itemSorter, r = e.flat(1);
	return n ? ai(r, n) : r;
});
//#endregion
//#region node_modules/recharts/es6/util/useElementOffset.js
function ci(e, t) {
	return pi(e) || fi(e, t) || ui(e, t) || li();
}
function li() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function ui(e, t) {
	if (e) {
		if (typeof e == "string") return di(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? di(e, t) : void 0;
	}
}
function di(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function fi(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function pi(e) {
	if (Array.isArray(e)) return e;
}
var mi = 1;
function hi(e, t) {
	return Math.abs(e.height - t.height) > mi || Math.abs(e.left - t.left) > mi || Math.abs(e.top - t.top) > mi || Math.abs(e.width - t.width) > mi;
}
function gi(e) {
	var t = e.getBoundingClientRect();
	return {
		height: t.height,
		left: t.left,
		top: t.top,
		width: t.width
	};
}
function _i() {
	var e = arguments.length > 0 && arguments[0] !== void 0 ? arguments[0] : [], t = ci((0, C.useState)({
		height: 0,
		left: 0,
		top: 0,
		width: 0
	}), 2), n = t[0], r = t[1], i = (0, C.useRef)(null), a = (0, C.useRef)(n);
	a.current = n;
	var o = (0, C.useCallback)((e) => {
		if (i.current != null && (i.current.disconnect(), i.current = null), e != null) {
			var t = gi(e);
			if (hi(t, a.current) && r(t), typeof ResizeObserver < "u") {
				var n = new ResizeObserver(() => {
					var t = gi(e);
					hi(t, a.current) && r(t);
				});
				n.observe(e), i.current = n;
			}
		}
	}, [...e]);
	return (0, C.useEffect)(() => () => {
		var e;
		(e = i.current) == null || e.disconnect();
	}, []), [n, o];
}
//#endregion
//#region node_modules/redux/dist/redux.mjs
function vi(e) {
	return `Minified Redux error #${e}; visit https://redux.js.org/Errors?code=${e} for the full message or use the non-minified dev environment for full errors. `;
}
var yi = typeof Symbol == "function" && Symbol.observable || "@@observable", bi = () => Math.random().toString(36).substring(7).split("").join("."), xi = {
	INIT: `@@redux/INIT${/* @__PURE__ */ bi()}`,
	REPLACE: `@@redux/REPLACE${/* @__PURE__ */ bi()}`,
	PROBE_UNKNOWN_ACTION: () => `@@redux/PROBE_UNKNOWN_ACTION${bi()}`
};
function Si(e) {
	if (typeof e != "object" || !e) return !1;
	let t = e;
	for (; Object.getPrototypeOf(t) !== null;) t = Object.getPrototypeOf(t);
	return Object.getPrototypeOf(e) === t || Object.getPrototypeOf(e) === null;
}
function Ci(e, t, n) {
	if (typeof e != "function") throw Error(vi(2));
	if (typeof t == "function" && typeof n == "function" || typeof n == "function" && typeof arguments[3] == "function") throw Error(vi(0));
	if (typeof t == "function" && n === void 0 && (n = t, t = void 0), n !== void 0) {
		if (typeof n != "function") throw Error(vi(1));
		return n(Ci)(e, t);
	}
	let r = e, i = t, a = /* @__PURE__ */ new Map(), o = a, s = 0, c = !1;
	function l() {
		o === a && (o = /* @__PURE__ */ new Map(), a.forEach((e, t) => {
			o.set(t, e);
		}));
	}
	function u() {
		if (c) throw Error(vi(3));
		return i;
	}
	function d(e) {
		if (typeof e != "function") throw Error(vi(4));
		if (c) throw Error(vi(5));
		let t = !0;
		l();
		let n = s++;
		return o.set(n, e), function() {
			if (t) {
				if (c) throw Error(vi(6));
				t = !1, l(), o.delete(n), a = null;
			}
		};
	}
	function f(e) {
		if (!Si(e)) throw Error(vi(7));
		if (e.type === void 0) throw Error(vi(8));
		if (typeof e.type != "string") throw Error(vi(17));
		if (c) throw Error(vi(9));
		try {
			c = !0, i = r(i, e);
		} finally {
			c = !1;
		}
		return (a = o).forEach((e) => {
			e();
		}), e;
	}
	function p(e) {
		if (typeof e != "function") throw Error(vi(10));
		r = e, f({ type: xi.REPLACE });
	}
	function m() {
		let e = d;
		return {
			subscribe(t) {
				if (typeof t != "object" || !t) throw Error(vi(11));
				function n() {
					let e = t;
					e.next && e.next(u());
				}
				return n(), { unsubscribe: e(n) };
			},
			[yi]() {
				return this;
			}
		};
	}
	return f({ type: xi.INIT }), {
		dispatch: f,
		subscribe: d,
		getState: u,
		replaceReducer: p,
		[yi]: m
	};
}
function wi(e) {
	Object.keys(e).forEach((t) => {
		let n = e[t];
		if (n(void 0, { type: xi.INIT }) === void 0) throw Error(vi(12));
		if (n(void 0, { type: xi.PROBE_UNKNOWN_ACTION() }) === void 0) throw Error(vi(13));
	});
}
function Ti(e) {
	let t = Object.keys(e), n = {};
	for (let r = 0; r < t.length; r++) {
		let i = t[r];
		typeof e[i] == "function" && (n[i] = e[i]);
	}
	let r = Object.keys(n), i;
	try {
		wi(n);
	} catch (e) {
		i = e;
	}
	return function(e = {}, t) {
		if (i) throw i;
		let a = !1, o = {};
		for (let i = 0; i < r.length; i++) {
			let s = r[i], c = n[s], l = e[s], u = c(l, t);
			if (u === void 0) throw t && t.type, Error(vi(14));
			o[s] = u, a = a || u !== l;
		}
		return a = a || r.length !== Object.keys(e).length, a ? o : e;
	};
}
function Ei(...e) {
	return e.length === 0 ? (e) => e : e.length === 1 ? e[0] : e.reduce((e, t) => (...n) => e(t(...n)));
}
function Di(...e) {
	return (t) => (n, r) => {
		let i = t(n, r), a = () => {
			throw Error(vi(15));
		}, o = {
			getState: i.getState,
			dispatch: (e, ...t) => a(e, ...t)
		};
		return a = Ei(...e.map((e) => e(o)))(i.dispatch), {
			...i,
			dispatch: a
		};
	};
}
function Oi(e) {
	return Si(e) && "type" in e && typeof e.type == "string";
}
//#endregion
//#region node_modules/immer/dist/immer.mjs
var ki = Symbol.for("immer-nothing"), Ai = Symbol.for("immer-draftable"), ji = Symbol.for("immer-state");
function Mi(e, ...t) {
	throw Error(`[Immer] minified error nr: ${e}. Full error at: https://bit.ly/3cXEKWf`);
}
var Ni = Object, Pi = Ni.getPrototypeOf, Fi = "constructor", Ii = "prototype", Li = "configurable", Ri = "enumerable", zi = "writable", Bi = "value", Vi = (e) => !!e && !!e[ji];
function Hi(e) {
	var t;
	return e ? Gi(e) || Xi(e) || !!e[Ai] || !!((t = e[Fi]) != null && t[Ai]) || Zi(e) || Qi(e) : !1;
}
var Ui = Ni[Ii][Fi].toString(), Wi = /* @__PURE__ */ new WeakMap();
function Gi(e) {
	if (!e || !$i(e)) return !1;
	let t = Pi(e);
	if (t === null || t === Ni[Ii]) return !0;
	let n = Ni.hasOwnProperty.call(t, Fi) && t[Fi];
	if (n === Object) return !0;
	if (!ea(n)) return !1;
	let r = Wi.get(n);
	return r === void 0 && (r = Function.toString.call(n), Wi.set(n, r)), r === Ui;
}
function Ki(e, t, n = !0) {
	qi(e) === 0 ? (n ? Reflect.ownKeys(e) : Ni.keys(e)).forEach((n) => {
		t(n, e[n], e);
	}) : e.forEach((n, r) => t(r, n, e));
}
function qi(e) {
	let t = e[ji];
	return t ? t.type_ : Xi(e) ? 1 : Zi(e) ? 2 : Qi(e) ? 3 : 0;
}
var Ji = (e, t, n = qi(e)) => n === 2 ? e.has(t) : Ni[Ii].hasOwnProperty.call(e, t), Yi = (e, t, n = qi(e)) => n === 2 ? e.get(t) : e[t], z = (e, t, n, r = qi(e)) => {
	r === 2 ? e.set(t, n) : r === 3 ? e.add(n) : e[t] = n;
};
function B(e, t) {
	return e === t ? e !== 0 || 1 / e == 1 / t : e !== e && t !== t;
}
var Xi = Array.isArray, Zi = (e) => e instanceof Map, Qi = (e) => e instanceof Set, $i = (e) => typeof e == "object", ea = (e) => typeof e == "function", ta = (e) => typeof e == "boolean";
function na(e) {
	let t = +e;
	return Number.isInteger(t) && String(t) === e;
}
var ra = (e) => e.copy_ || e.base_, ia = (e) => e.modified_ ? e.copy_ : e.base_;
function aa(e, t) {
	if (Zi(e)) return new Map(e);
	if (Qi(e)) return new Set(e);
	if (Xi(e)) return Array[Ii].slice.call(e);
	let n = Gi(e);
	if (t === !0 || t === "class_only" && !n) {
		let t = Ni.getOwnPropertyDescriptors(e);
		delete t[ji];
		let n = Reflect.ownKeys(t);
		for (let r = 0; r < n.length; r++) {
			let i = n[r], a = t[i];
			a[zi] === !1 && (a[zi] = !0, a[Li] = !0), (a.get || a.set) && (t[i] = {
				[Li]: !0,
				[zi]: !0,
				[Ri]: a[Ri],
				[Bi]: e[i]
			});
		}
		return Ni.create(Pi(e), t);
	} else {
		let t = Pi(e);
		if (t !== null && n) return { ...e };
		let r = Ni.create(t);
		return Ni.assign(r, e);
	}
}
function oa(e, t = !1) {
	return la(e) || Vi(e) || !Hi(e) ? e : (qi(e) > 1 && Ni.defineProperties(e, {
		set: ca,
		add: ca,
		clear: ca,
		delete: ca
	}), Ni.freeze(e), t && Ki(e, (e, t) => {
		oa(t, !0);
	}, !1), e);
}
function sa() {
	Mi(2);
}
var ca = { [Bi]: sa };
function la(e) {
	return e === null || !$i(e) || Ni.isFrozen(e);
}
var ua = "MapSet", da = "Patches", fa = "ArrayMethods", pa = {};
function ma(e) {
	let t = pa[e];
	return t || Mi(0, e), t;
}
var ha = (e) => !!pa[e], ga, _a = () => ga, va = (e, t) => ({
	drafts_: [],
	parent_: e,
	immer_: t,
	canAutoFreeze_: !0,
	unfinalizedDrafts_: 0,
	handledSet_: /* @__PURE__ */ new Set(),
	processedForPatches_: /* @__PURE__ */ new Set(),
	mapSetPlugin_: ha(ua) ? ma(ua) : void 0,
	arrayMethodsPlugin_: ha(fa) ? ma(fa) : void 0
});
function ya(e, t) {
	t && (e.patchPlugin_ = ma(da), e.patches_ = [], e.inversePatches_ = [], e.patchListener_ = t);
}
function ba(e) {
	xa(e), e.drafts_.forEach(Ca), e.drafts_ = null;
}
function xa(e) {
	e === ga && (ga = e.parent_);
}
var Sa = (e) => ga = va(ga, e);
function Ca(e) {
	let t = e[ji];
	t.type_ === 0 || t.type_ === 1 ? t.revoke_() : t.revoked_ = !0;
}
function wa(e, t) {
	t.unfinalizedDrafts_ = t.drafts_.length;
	let n = t.drafts_[0];
	if (e !== void 0 && e !== n) {
		n[ji].modified_ && (ba(t), Mi(4)), Hi(e) && (e = Ta(t, e));
		let { patchPlugin_: r } = t;
		r && r.generateReplacementPatches_(n[ji].base_, e, t);
	} else e = Ta(t, n);
	return Ea(t, e, !0), ba(t), t.patches_ && t.patchListener_(t.patches_, t.inversePatches_), e === ki ? void 0 : e;
}
function Ta(e, t) {
	if (la(t)) return t;
	let n = t[ji];
	if (!n) return Na(t, e.handledSet_, e);
	if (!V(n, e)) return t;
	if (!n.modified_) return n.base_;
	if (!n.finalized_) {
		let { callbacks_: t } = n;
		if (t) for (; t.length > 0;) t.pop()(e);
		ja(n, e);
	}
	return n.copy_;
}
function Ea(e, t, n = !1) {
	!e.parent_ && e.immer_.autoFreeze_ && e.canAutoFreeze_ && oa(t, n);
}
function Da(e) {
	e.finalized_ = !0, e.scope_.unfinalizedDrafts_--;
}
var V = (e, t) => e.scope_ === t, Oa = [];
function ka(e, t, n, r) {
	var i;
	let a = ra(e), o = e.type_;
	if (r !== void 0 && Yi(a, r, o) === t) {
		z(a, r, n, o);
		return;
	}
	if (!e.draftLocations_) {
		let t = e.draftLocations_ = /* @__PURE__ */ new Map();
		Ki(a, (e, n) => {
			if (Vi(n)) {
				let r = t.get(n) || [];
				r.push(e), t.set(n, r);
			}
		});
	}
	let s = (i = e.draftLocations_.get(t)) == null ? Oa : i;
	for (let e of s) z(a, e, n, o);
}
function Aa(e, t, n) {
	e.callbacks_.push(function(r) {
		var i, a;
		let o = t;
		if (!o || !V(o, r)) return;
		(i = r.mapSetPlugin_) == null || i.fixSetContents(o);
		let s = ia(o);
		ka(e, (a = o.draft_) == null ? o : a, s, n), ja(o, r);
	});
}
function ja(e, t) {
	var n, r;
	if (e.modified_ && !e.finalized_ && (e.type_ === 3 || e.type_ === 1 && e.allIndicesReassigned_ || ((n = (r = e.assigned_) == null ? void 0 : r.size) == null ? 0 : n) > 0)) {
		let { patchPlugin_: n } = t;
		if (n) {
			let r = n.getPath(e);
			r && n.generatePatches_(e, r, t);
		}
		Da(e);
	}
}
function Ma(e, t, n) {
	let { scope_: r } = e;
	if (Vi(n)) {
		let i = n[ji];
		V(i, r) && i.callbacks_.push(function() {
			Ha(e), ka(e, n, ia(i), t);
		});
	} else Hi(n) && e.callbacks_.push(function() {
		let i = ra(e);
		if (e.type_ === 3) i.has(n) && Na(n, r.handledSet_, r);
		else if (Yi(i, t, e.type_) === n) {
			var a;
			r.drafts_.length > 1 && ((a = e.assigned_.get(t)) != null && a) === !0 && e.copy_ && Na(Yi(e.copy_, t, e.type_), r.handledSet_, r);
		}
	});
}
function Na(e, t, n) {
	return !n.immer_.autoFreeze_ && n.unfinalizedDrafts_ < 1 || Vi(e) || t.has(e) || !Hi(e) || la(e) ? e : (t.add(e), Ki(e, (r, i) => {
		if (Vi(i)) {
			let t = i[ji];
			V(t, n) && (z(e, r, ia(t), e.type_), Da(t));
		} else Hi(i) && Na(i, t, n);
	}), e);
}
function Pa(e, t) {
	let n = Xi(e), r = {
		type_: +!!n,
		scope_: t ? t.scope_ : _a(),
		modified_: !1,
		finalized_: !1,
		assigned_: void 0,
		parent_: t,
		base_: e,
		draft_: null,
		copy_: null,
		revoke_: null,
		isManual_: !1,
		callbacks_: void 0
	}, i = r, a = Fa;
	n && (i = [r], a = Ia);
	let { revoke: o, proxy: s } = Proxy.revocable(i, a);
	return r.draft_ = s, r.revoke_ = o, [s, r];
}
var Fa = {
	get(e, t) {
		if (t === ji) return e;
		let n = e.scope_.arrayMethodsPlugin_, r = e.type_ === 1 && typeof t == "string";
		if (r && n != null && n.isArrayOperationMethod(t)) return n.createMethodInterceptor(e, t);
		let i = ra(e);
		if (!Ji(i, t, e.type_)) return za(e, i, t);
		let a = i[t];
		if (e.finalized_ || !Hi(a) || r && e.operationMethod && n != null && n.isMutatingArrayMethod(e.operationMethod) && na(t)) return a;
		if (a === La(e.base_, t) || Ra(e, t, a)) {
			Ha(e);
			let n = e.type_ === 1 ? +t : t, r = Wa(e.scope_, a, e, n);
			return e.copy_[n] = r;
		}
		return a;
	},
	has(e, t) {
		return t in ra(e);
	},
	ownKeys(e) {
		return Reflect.ownKeys(ra(e));
	},
	set(e, t, n) {
		let r = Ba(ra(e), t);
		if (r != null && r.set) return r.set.call(e.draft_, n), !0;
		if (!e.modified_) {
			let r = La(ra(e), t), i = r == null ? void 0 : r[ji];
			if (i && i.base_ === n) return e.copy_[t] = n, e.assigned_.set(t, !1), !0;
			if (B(n, r) && (n !== void 0 || Ji(e.base_, t, e.type_))) return !0;
			Ha(e), Va(e);
		}
		return e.copy_[t] === n && (n !== void 0 || Ji(e.copy_, t, e.type_)) || Number.isNaN(n) && Number.isNaN(e.copy_[t]) ? !0 : (e.copy_[t] = n, e.assigned_.set(t, !0), Ma(e, t, n), !0);
	},
	deleteProperty(e, t) {
		return Ha(e), La(e.base_, t) !== void 0 || t in e.base_ ? (e.assigned_.set(t, !1), Va(e)) : e.assigned_.delete(t), e.copy_ && delete e.copy_[t], !0;
	},
	getOwnPropertyDescriptor(e, t) {
		let n = ra(e), r = Reflect.getOwnPropertyDescriptor(n, t);
		return r && {
			[zi]: !0,
			[Li]: e.type_ !== 1 || t !== "length",
			[Ri]: r[Ri],
			[Bi]: n[t]
		};
	},
	defineProperty() {
		Mi(11);
	},
	getPrototypeOf(e) {
		return Pi(e.base_);
	},
	setPrototypeOf() {
		Mi(12);
	}
}, Ia = {};
for (let e in Fa) {
	let t = Fa[e];
	Ia[e] = function() {
		let e = arguments;
		return e[0] = e[0][0], t.apply(this, e);
	};
}
Ia.deleteProperty = function(e, t) {
	return Ia.set.call(this, e, t, void 0);
}, Ia.set = function(e, t, n) {
	return Fa.set.call(this, e[0], t, n, e[0]);
};
function La(e, t) {
	let n = e[ji];
	return (n ? ra(n) : e)[t];
}
function Ra(e, t, n) {
	var r;
	return e.type_ !== 1 || !e.allIndicesReassigned_ || (r = e.assigned_) != null && r.get(t) || !Hi(n) || n[ji] ? !1 : e.baseRefs_.has(n);
}
function za(e, t, n) {
	var r;
	let i = Ba(t, n);
	return i ? Bi in i ? i[Bi] : (r = i.get) == null ? void 0 : r.call(e.draft_) : void 0;
}
function Ba(e, t) {
	if (!(t in e)) return;
	let n = Pi(e);
	for (; n;) {
		let e = Object.getOwnPropertyDescriptor(n, t);
		if (e) return e;
		n = Pi(n);
	}
}
function Va(e) {
	e.modified_ || (e.modified_ = !0, e.parent_ && Va(e.parent_));
}
function Ha(e) {
	e.copy_ || (e.assigned_ = /* @__PURE__ */ new Map(), e.copy_ = aa(e.base_, e.scope_.immer_.useStrictShallowCopy_));
}
var Ua = class {
	constructor(e) {
		this.autoFreeze_ = !0, this.useStrictShallowCopy_ = !1, this.useStrictIteration_ = !1, this.produce = (e, t, n) => {
			if (ea(e) && !ea(t)) {
				let n = t;
				t = e;
				let r = this;
				return function(e = n, ...i) {
					return r.produce(e, (e) => t.call(this, e, ...i));
				};
			}
			ea(t) || Mi(6), n !== void 0 && !ea(n) && Mi(7);
			let r;
			if (Hi(e)) {
				let i = Sa(this), a = Wa(i, e, void 0), o = !0;
				try {
					r = t(a), o = !1;
				} finally {
					o ? ba(i) : xa(i);
				}
				return ya(i, n), wa(r, i);
			} else if (!e || !$i(e)) {
				if (r = t(e), r === void 0 && (r = e), r === ki && (r = void 0), this.autoFreeze_ && oa(r, !0), n) {
					let t = [], i = [];
					ma(da).generateReplacementPatches_(e, r, {
						patches_: t,
						inversePatches_: i
					}), n(t, i);
				}
				return r;
			} else Mi(1, e);
		}, this.produceWithPatches = (e, t) => {
			if (ea(e)) return (t, ...n) => this.produceWithPatches(t, (t) => e(t, ...n));
			let n, r;
			return [
				this.produce(e, t, (e, t) => {
					n = e, r = t;
				}),
				n,
				r
			];
		}, ta(e == null ? void 0 : e.autoFreeze) && this.setAutoFreeze(e.autoFreeze), ta(e == null ? void 0 : e.useStrictShallowCopy) && this.setUseStrictShallowCopy(e.useStrictShallowCopy), ta(e == null ? void 0 : e.useStrictIteration) && this.setUseStrictIteration(e.useStrictIteration);
	}
	createDraft(e) {
		Hi(e) || Mi(8), Vi(e) && (e = Ga(e));
		let t = Sa(this), n = Wa(t, e, void 0);
		return n[ji].isManual_ = !0, xa(t), n;
	}
	finishDraft(e, t) {
		let n = e && e[ji];
		(!n || !n.isManual_) && Mi(9);
		let { scope_: r } = n;
		return ya(r, t), wa(void 0, r);
	}
	setAutoFreeze(e) {
		this.autoFreeze_ = e;
	}
	setUseStrictShallowCopy(e) {
		this.useStrictShallowCopy_ = e;
	}
	setUseStrictIteration(e) {
		this.useStrictIteration_ = e;
	}
	shouldUseStrictIteration() {
		return this.useStrictIteration_;
	}
	applyPatches(e, t) {
		let n;
		for (n = t.length - 1; n >= 0; n--) {
			let r = t[n];
			if (r.path.length === 0 && r.op === "replace") {
				e = r.value;
				break;
			}
		}
		n > -1 && (t = t.slice(n + 1));
		let r = ma(da).applyPatches_;
		return Vi(e) ? r(e, t) : this.produce(e, (e) => r(e, t));
	}
};
function Wa(e, t, n, r) {
	var i, a;
	let [o, s] = Zi(t) ? ma(ua).proxyMap_(t, n) : Qi(t) ? ma(ua).proxySet_(t, n) : Pa(t, n);
	return ((i = n == null ? void 0 : n.scope_) == null ? _a() : i).drafts_.push(o), s.callbacks_ = (a = n == null ? void 0 : n.callbacks_) == null ? [] : a, s.key_ = r, n && r !== void 0 ? Aa(n, s, r) : s.callbacks_.push(function(e) {
		var t;
		(t = e.mapSetPlugin_) == null || t.fixSetContents(s);
		let { patchPlugin_: n } = e;
		s.modified_ && n && n.generatePatches_(s, [], e);
	}), o;
}
function Ga(e) {
	return Vi(e) || Mi(10, e), Ka(e);
}
function Ka(e) {
	if (!Hi(e) || la(e)) return e;
	let t = e[ji], n, r = !0;
	if (t) {
		if (!t.modified_) return t.base_;
		t.finalized_ = !0, n = aa(e, t.scope_.immer_.useStrictShallowCopy_), r = t.scope_.immer_.shouldUseStrictIteration();
	} else n = aa(e, !0);
	return Ki(n, (e, t) => {
		z(n, e, Ka(t));
	}, r), t && (t.finalized_ = !1), n;
}
var qa = new Ua().produce, H = (e) => e;
//#endregion
//#region node_modules/redux-thunk/dist/redux-thunk.mjs
function Ja(e) {
	return ({ dispatch: t, getState: n }) => (r) => (i) => typeof i == "function" ? i(t, n, e) : r(i);
}
var Ya = Ja(), Xa = Ja, Za = typeof window < "u" && window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ ? window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ : function() {
	if (arguments.length !== 0) return typeof arguments[0] == "object" ? Ei : Ei.apply(null, arguments);
};
typeof window < "u" && window.__REDUX_DEVTOOLS_EXTENSION__ && window.__REDUX_DEVTOOLS_EXTENSION__;
function Qa(e, t) {
	function n(...n) {
		if (t) {
			let r = t(...n);
			if (!r) throw Error(cs(0));
			return {
				type: e,
				payload: r.payload,
				..."meta" in r && { meta: r.meta },
				..."error" in r && { error: r.error }
			};
		}
		return {
			type: e,
			payload: n[0]
		};
	}
	return n.toString = () => `${e}`, n.type = e, n.match = (t) => Oi(t) && t.type === e, n;
}
var $a = class e extends Array {
	constructor(...t) {
		super(...t), Object.setPrototypeOf(this, e.prototype);
	}
	static get [Symbol.species]() {
		return e;
	}
	concat(...e) {
		return super.concat.apply(this, e);
	}
	prepend(...t) {
		return t.length === 1 && Array.isArray(t[0]) ? new e(...t[0].concat(this)) : new e(...t.concat(this));
	}
};
function eo(e) {
	return Hi(e) ? qa(e, () => {}) : e;
}
function to(e, t, n) {
	return e.has(t) ? e.get(t) : e.set(t, n(t)).get(t);
}
function no(e) {
	return typeof e == "boolean";
}
var ro = () => function(e) {
	let { thunk: t = !0, immutableCheck: n = !0, serializableCheck: r = !0, actionCreatorCheck: i = !0 } = e == null ? {} : e, a = new $a();
	return t && (no(t) ? a.push(Ya) : a.push(Xa(t.extraArgument))), a;
}, io = "RTK_autoBatch", ao = () => (e) => ({
	payload: e,
	meta: { [io]: !0 }
}), oo = (e) => (t) => {
	setTimeout(t, e);
}, so = (e, t) => (n) => {
	let r = !1, i = () => {
		r || (r = !0, cancelAnimationFrame(a), clearTimeout(o), n());
	}, a = e(i), o = setTimeout(i, t);
}, co = (e = { type: "raf" }) => (t) => (...n) => {
	let r = t(...n), i = !0, a = !1, o = !1, s = /* @__PURE__ */ new Set(), c = e.type === "tick" ? queueMicrotask : e.type === "raf" ? typeof window < "u" && window.requestAnimationFrame ? so(window.requestAnimationFrame, 100) : oo(10) : e.type === "callback" ? e.queueNotification : oo(e.timeout), l = () => {
		o = !1, a && (a = !1, s.forEach((e) => e()));
	};
	return Object.assign({}, r, {
		subscribe(e) {
			let t = r.subscribe(() => i && e());
			return s.add(e), () => {
				t(), s.delete(e);
			};
		},
		dispatch(e) {
			try {
				var t;
				return i = !(!(e == null || (t = e.meta) == null) && t[io]), a = !i, a && (o || (o = !0, c(l))), r.dispatch(e);
			} finally {
				i = !0;
			}
		}
	});
}, lo = (e) => function(t) {
	let { autoBatch: n = !0 } = t == null ? {} : t, r = new $a(e);
	return n && r.push(co(typeof n == "object" ? n : void 0)), r;
};
function uo(e) {
	let t = ro(), { reducer: n = void 0, middleware: r, devTools: i = !0, duplicateMiddlewareCheck: a = !0, preloadedState: o = void 0, enhancers: s = void 0 } = e || {}, c;
	if (typeof n == "function") c = n;
	else if (Si(n)) c = Ti(n);
	else throw Error(cs(1));
	let l;
	l = typeof r == "function" ? r(t) : t();
	let u = Ei;
	i && (u = Za({
		trace: !1,
		...typeof i == "object" && i
	}));
	let d = lo(Di(...l)), f = typeof s == "function" ? s(d) : d(), p = u(...f);
	return Ci(c, o, p);
}
function fo(e) {
	let t = {}, n = [], r, i = {
		addCase(e, n) {
			let r = typeof e == "string" ? e : e.type;
			if (!r) throw Error(cs(28));
			if (r in t) throw Error(cs(29));
			return t[r] = n, i;
		},
		addAsyncThunk(e, r) {
			return r.pending && (t[e.pending.type] = r.pending), r.rejected && (t[e.rejected.type] = r.rejected), r.fulfilled && (t[e.fulfilled.type] = r.fulfilled), r.settled && n.push({
				matcher: e.settled,
				reducer: r.settled
			}), i;
		},
		addMatcher(e, t) {
			return n.push({
				matcher: e,
				reducer: t
			}), i;
		},
		addDefaultCase(e) {
			return r = e, i;
		}
	};
	return e(i), [
		t,
		n,
		r
	];
}
function po(e) {
	return typeof e == "function";
}
function mo(e, t) {
	let [n, r, i] = fo(t), a;
	if (po(e)) a = () => eo(e());
	else {
		let t = eo(e);
		a = () => t;
	}
	function o(e = a(), t) {
		let o = [n[t.type], ...r.filter(({ matcher: e }) => e(t)).map(({ reducer: e }) => e)];
		return o.filter((e) => !!e).length === 0 && (o = [i]), o.reduce((e, n) => {
			if (n) if (Vi(e)) {
				let r = n(e, t);
				return r === void 0 ? e : r;
			} else if (Hi(e)) return qa(e, (e) => n(e, t));
			else {
				let r = n(e, t);
				if (r === void 0) {
					if (e === null) return e;
					throw Error("A case reducer on a non-draftable value must not return undefined");
				}
				return r;
			}
			return e;
		}, e);
	}
	return o.getInitialState = a, o;
}
var ho = "ModuleSymbhasOwnPr-0123456789ABCDEFGHNRVfgctiUvz_KqYTJkLxpZXIjQW", go = (e = 21) => {
	let t = "", n = e;
	for (; n--;) t += ho[Math.random() * 64 | 0];
	return t;
}, _o = /* @__PURE__ */ Symbol.for("rtk-slice-createasyncthunk");
function vo(e, t) {
	return `${e}/${t}`;
}
function yo({ creators: e } = {}) {
	var t;
	let n = e == null || (t = e.asyncThunk) == null ? void 0 : t[_o];
	return function(e) {
		let { name: t, reducerPath: r = t } = e;
		if (!t) throw Error(cs(11));
		let i = (typeof e.reducers == "function" ? e.reducers(So()) : e.reducers) || {}, a = Object.keys(i), o = {
			sliceCaseReducersByName: {},
			sliceCaseReducersByType: {},
			actionCreators: {},
			sliceMatchers: []
		}, s = {
			addCase(e, t) {
				let n = typeof e == "string" ? e : e.type;
				if (!n) throw Error(cs(12));
				if (n in o.sliceCaseReducersByType) throw Error(cs(13));
				return o.sliceCaseReducersByType[n] = t, s;
			},
			addMatcher(e, t) {
				return o.sliceMatchers.push({
					matcher: e,
					reducer: t
				}), s;
			},
			exposeAction(e, t) {
				return o.actionCreators[e] = t, s;
			},
			exposeCaseReducer(e, t) {
				return o.sliceCaseReducersByName[e] = t, s;
			}
		};
		a.forEach((r) => {
			let a = i[r], o = {
				reducerName: r,
				type: vo(t, r),
				createNotation: typeof e.reducers == "function"
			};
			wo(a) ? Eo(o, a, s, n) : Co(o, a, s);
		});
		function c() {
			let [t = {}, n = [], r = void 0] = typeof e.extraReducers == "function" ? fo(e.extraReducers) : [e.extraReducers], i = {
				...t,
				...o.sliceCaseReducersByType
			};
			return mo(e.initialState, (e) => {
				for (let t in i) e.addCase(t, i[t]);
				for (let t of o.sliceMatchers) e.addMatcher(t.matcher, t.reducer);
				for (let t of n) e.addMatcher(t.matcher, t.reducer);
				r && e.addDefaultCase(r);
			});
		}
		let l = (e) => e, u = /* @__PURE__ */ new Map(), d = /* @__PURE__ */ new WeakMap(), f;
		function p(e, t) {
			return f || (f = c()), f(e, t);
		}
		function m() {
			return f || (f = c()), f.getInitialState();
		}
		function h(t, n = !1) {
			function r(e) {
				let i = e[t];
				return i === void 0 && n && (i = to(d, r, m)), i;
			}
			function i(t = l) {
				return to(to(u, n, () => /* @__PURE__ */ new WeakMap()), t, () => {
					var r;
					let i = {};
					for (let [a, o] of Object.entries((r = e.selectors) == null ? {} : r)) i[a] = bo(o, t, () => to(d, t, m), n);
					return i;
				});
			}
			return {
				reducerPath: t,
				getSelectors: i,
				get selectors() {
					return i(r);
				},
				selectSlice: r
			};
		}
		let g = {
			name: t,
			reducer: p,
			actions: o.actionCreators,
			caseReducers: o.sliceCaseReducersByName,
			getInitialState: m,
			...h(r),
			injectInto(e, { reducerPath: t, ...n } = {}) {
				let i = t == null ? r : t;
				return e.inject({
					reducerPath: i,
					reducer: p
				}, n), {
					...g,
					...h(i, !0)
				};
			}
		};
		return g;
	};
}
function bo(e, t, n, r) {
	function i(i, ...a) {
		let o = t(i);
		return o === void 0 && r && (o = n()), e(o, ...a);
	}
	return i.unwrapped = e, i;
}
var xo = /* @__PURE__ */ yo();
function So() {
	function e(e, t) {
		return {
			_reducerDefinitionType: "asyncThunk",
			payloadCreator: e,
			...t
		};
	}
	return e.withTypes = () => e, {
		reducer(e) {
			return Object.assign({ [e.name](...t) {
				return e(...t);
			} }[e.name], { _reducerDefinitionType: "reducer" });
		},
		preparedReducer(e, t) {
			return {
				_reducerDefinitionType: "reducerWithPrepare",
				prepare: e,
				reducer: t
			};
		},
		asyncThunk: e
	};
}
function Co({ type: e, reducerName: t, createNotation: n }, r, i) {
	let a, o;
	if ("reducer" in r) {
		if (n && !To(r)) throw Error(cs(17));
		a = r.reducer, o = r.prepare;
	} else a = r;
	i.addCase(e, a).exposeCaseReducer(t, a).exposeAction(t, o ? Qa(e, o) : Qa(e));
}
function wo(e) {
	return e._reducerDefinitionType === "asyncThunk";
}
function To(e) {
	return e._reducerDefinitionType === "reducerWithPrepare";
}
function Eo({ type: e, reducerName: t }, n, r, i) {
	if (!i) throw Error(cs(18));
	let { payloadCreator: a, fulfilled: o, pending: s, rejected: c, settled: l, options: u } = n, d = i(e, a, u);
	r.exposeAction(t, d), o && r.addCase(d.fulfilled, o), s && r.addCase(d.pending, s), c && r.addCase(d.rejected, c), l && r.addMatcher(d.settled, l), r.exposeCaseReducer(t, {
		fulfilled: o || Do,
		pending: s || Do,
		rejected: c || Do,
		settled: l || Do
	});
}
function Do() {}
var Oo = "task", ko = "listener", Ao = "completed", jo = "cancelled", Mo = `task-${jo}`, No = `task-${Ao}`, Po = `${ko}-${jo}`, Fo = `${ko}-${Ao}`, Io = class {
	constructor(e) {
		Ir(this, "code", void 0), Ir(this, "name", "TaskAbortError"), Ir(this, "message", void 0), this.code = e, this.message = `${Oo} ${jo} (reason: ${e})`;
	}
}, Lo = (e, t) => {
	if (typeof e != "function") throw TypeError(cs(32));
}, Ro = () => {}, zo = (e, t = Ro) => (e.catch(t), e), Bo = (e, t) => (e.addEventListener("abort", t, { once: !0 }), () => e.removeEventListener("abort", t)), Vo = (e) => {
	if (e.aborted) throw new Io(e.reason);
};
function Ho(e, t) {
	let n = Ro;
	return new Promise((r, i) => {
		let a = () => i(new Io(e.reason));
		if (e.aborted) {
			a();
			return;
		}
		n = Bo(e, a), t.finally(() => n()).then(r, i);
	}).finally(() => {
		n = Ro;
	});
}
var Uo = async (e, t) => {
	try {
		return await Promise.resolve(), {
			status: "ok",
			value: await e()
		};
	} catch (e) {
		return {
			status: e instanceof Io ? "cancelled" : "rejected",
			error: e
		};
	} finally {
		t == null || t();
	}
}, Wo = (e) => (t) => zo(Ho(e, t).then((t) => (Vo(e), t))), Go = (e) => {
	let t = Wo(e);
	return (e) => t(new Promise((t) => setTimeout(t, e)));
}, { assign: Ko } = Object, qo = {}, Jo = "listenerMiddleware", Yo = (e, t) => {
	let n = (t) => Bo(e, () => t.abort(e.reason));
	return (r, i) => {
		Lo(r, "taskExecutor");
		let a = new AbortController();
		n(a);
		let o = Uo(async () => {
			Vo(e), Vo(a.signal);
			let t = await r({
				pause: Wo(a.signal),
				delay: Go(a.signal),
				signal: a.signal
			});
			return Vo(a.signal), t;
		}, () => a.abort(No));
		return i != null && i.autoJoin && t.push(o.catch(Ro)), {
			result: Wo(e)(o),
			cancel() {
				a.abort(Mo);
			}
		};
	};
}, Xo = (e, t) => {
	let n = async (n, r) => {
		Vo(t);
		let i = () => {}, a = [new Promise((t, r) => {
			let a = e({
				predicate: n,
				effect: (e, n) => {
					n.unsubscribe(), t([
						e,
						n.getState(),
						n.getOriginalState()
					]);
				}
			});
			i = () => {
				a(), r();
			};
		})];
		r != null && a.push(new Promise((e) => setTimeout(e, r, null)));
		try {
			let e = await Ho(t, Promise.race(a));
			return Vo(t), e;
		} finally {
			i();
		}
	};
	return ((e, t) => zo(n(e, t)));
}, Zo = (e) => {
	let { type: t, actionCreator: n, matcher: r, predicate: i, effect: a } = e;
	if (t) i = Qa(t).match;
	else if (n) t = n.type, i = n.match;
	else if (r) i = r;
	else if (!i) throw Error(cs(21));
	return Lo(a, "options.listener"), {
		predicate: i,
		type: t,
		effect: a
	};
}, Qo = /* @__PURE__ */ Ko((e) => {
	let { type: t, predicate: n, effect: r } = Zo(e);
	return {
		id: go(),
		effect: r,
		type: t,
		predicate: n,
		pending: /* @__PURE__ */ new Set(),
		unsubscribe: () => {
			throw Error(cs(22));
		}
	};
}, { withTypes: () => Qo }), $o = (e, t) => {
	let { type: n, effect: r, predicate: i } = Zo(t);
	return Array.from(e.values()).find((e) => (typeof n == "string" ? e.type === n : e.predicate === i) && e.effect === r);
}, es = (e) => {
	e.pending.forEach((e) => {
		e.abort(Po);
	});
}, ts = (e, t) => () => {
	for (let e of t.keys()) es(e);
	e.clear();
}, ns = (e, t, n) => {
	try {
		e(t, n);
	} catch (e) {
		setTimeout(() => {
			throw e;
		}, 0);
	}
}, rs = /* @__PURE__ */ Ko(/* @__PURE__ */ Qa(`${Jo}/add`), { withTypes: () => rs }), is = /* @__PURE__ */ Qa(`${Jo}/removeAll`), as = /* @__PURE__ */ Ko(/* @__PURE__ */ Qa(`${Jo}/remove`), { withTypes: () => as }), os = (...e) => {
	console.error(`${Jo}/error`, ...e);
}, ss = (e = {}) => {
	let t = /* @__PURE__ */ new Map(), n = /* @__PURE__ */ new Map(), r = (e) => {
		var t;
		let r = (t = n.get(e)) == null ? 0 : t;
		n.set(e, r + 1);
	}, i = (e) => {
		var t;
		let r = (t = n.get(e)) == null ? 1 : t;
		r === 1 ? n.delete(e) : n.set(e, r - 1);
	}, { extra: a, onError: o = os } = e;
	Lo(o, "onError");
	let s = (e) => (e.unsubscribe = () => t.delete(e.id), t.set(e.id, e), (t) => {
		e.unsubscribe(), t != null && t.cancelActive && es(e);
	}), c = ((e) => {
		var n;
		let r = (n = $o(t, e)) == null ? Qo(e) : n;
		return s(r);
	});
	Ko(c, { withTypes: () => c });
	let l = (e) => {
		let n = $o(t, e);
		return n && (n.unsubscribe(), e.cancelActive && es(n)), !!n;
	};
	Ko(l, { withTypes: () => l });
	let u = async (e, n, s, l) => {
		let u = new AbortController(), d = Xo(c, u.signal), f = [];
		try {
			e.pending.add(u), r(e), await Promise.resolve(e.effect(n, Ko({}, s, {
				getOriginalState: l,
				condition: (e, t) => d(e, t).then(Boolean),
				take: d,
				delay: Go(u.signal),
				pause: Wo(u.signal),
				extra: a,
				signal: u.signal,
				fork: Yo(u.signal, f),
				unsubscribe: e.unsubscribe,
				subscribe: () => {
					t.set(e.id, e);
				},
				cancelActiveListeners: () => {
					e.pending.forEach((e, t, n) => {
						e !== u && (e.abort(Po), n.delete(e));
					});
				},
				cancel: () => {
					u.abort(Po), e.pending.delete(u);
				},
				throwIfCancelled: () => {
					Vo(u.signal);
				}
			})));
		} catch (e) {
			e instanceof Io || ns(o, e, { raisedBy: "effect" });
		} finally {
			await Promise.all(f), u.abort(Fo), i(e), e.pending.delete(u);
		}
	}, d = ts(t, n);
	return {
		middleware: (e) => (n) => (r) => {
			if (!Oi(r)) return n(r);
			if (rs.match(r)) return c(r.payload);
			if (is.match(r)) {
				d();
				return;
			}
			if (as.match(r)) return l(r.payload);
			let i = e.getState(), a = () => {
				if (i === qo) throw Error(cs(23));
				return i;
			}, s;
			try {
				if (s = n(r), t.size > 0) {
					let n = e.getState(), s = Array.from(t.values());
					for (let t of s) {
						let s = !1;
						try {
							s = t.predicate(r, n, i);
						} catch (e) {
							s = !1, ns(o, e, { raisedBy: "predicate" });
						}
						s && u(t, r, e, a);
					}
				}
			} finally {
				i = qo;
			}
			return s;
		},
		startListening: c,
		stopListening: l,
		clearListeners: d
	};
};
function cs(e) {
	return `Minified Redux Toolkit error #${e}; visit https://redux-toolkit.js.org/Errors?code=${e} for the full message or use the non-minified dev environment for full errors. `;
}
//#endregion
//#region node_modules/recharts/es6/state/layoutSlice.js
var ls = xo({
	name: "chartLayout",
	initialState: {
		layoutType: "horizontal",
		width: 0,
		height: 0,
		margin: {
			top: 5,
			right: 5,
			bottom: 5,
			left: 5
		},
		scale: 1
	},
	reducers: {
		setLayout(e, t) {
			e.layoutType = t.payload;
		},
		setChartSize(e, t) {
			e.width = t.payload.width, e.height = t.payload.height;
		},
		setMargin(e, t) {
			var n, r, i, a;
			e.margin.top = (n = t.payload.top) == null ? 0 : n, e.margin.right = (r = t.payload.right) == null ? 0 : r, e.margin.bottom = (i = t.payload.bottom) == null ? 0 : i, e.margin.left = (a = t.payload.left) == null ? 0 : a;
		},
		setScale(e, t) {
			e.scale = t.payload;
		}
	}
}), us = ls.actions, ds = us.setMargin, fs = us.setLayout, ps = us.setChartSize, ms = us.setScale, hs = ls.reducer;
//#endregion
//#region node_modules/recharts/es6/util/getSliced.js
function gs(e, t, n) {
	return Array.isArray(e) && e && t + n !== 0 ? e.slice(t, n + 1) : e;
}
//#endregion
//#region node_modules/recharts/es6/util/isWellBehavedNumber.js
function U(e) {
	return Number.isFinite(e);
}
function _s(e) {
	return typeof e == "number" && e > 0 && Number.isFinite(e);
}
//#endregion
//#region node_modules/recharts/es6/util/ChartUtils.js
function vs(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function ys(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? vs(Object(n), !0).forEach(function(t) {
			bs(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : vs(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function bs(e, t, n) {
	return (t = xs(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function xs(e) {
	var t = Ss(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Ss(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function W(e, t, n) {
	return en(e) || en(t) ? n : qt(t) ? Bt(e, t, n) : typeof t == "function" ? t(e) : n;
}
var Cs = (e, t, n) => {
	if (t && n) {
		var r = n.width, i = n.height, a = t.align, o = t.verticalAlign, s = t.layout;
		if ((s === "vertical" || s === "horizontal" && o === "middle") && a !== "center" && I(e[a])) return ys(ys({}, e), {}, { [a]: e[a] + (r || 0) });
		if ((s === "horizontal" || s === "vertical" && a === "center") && o !== "middle" && I(e[o])) return ys(ys({}, e), {}, { [o]: e[o] + (i || 0) });
	}
	return e;
}, ws = (e, t) => e === "horizontal" && t === "xAxis" || e === "vertical" && t === "yAxis" || e === "centric" && t === "angleAxis" || e === "radial" && t === "radiusAxis", Ts = (e, t) => {
	if (!t || t.length !== 2 || !I(t[0]) || !I(t[1])) return e;
	var n = Math.min(t[0], t[1]), r = Math.max(t[0], t[1]), i = [e[0], e[1]];
	return (!I(e[0]) || e[0] < n) && (i[0] = n), (!I(e[1]) || e[1] > r) && (i[1] = r), i[0] > r && (i[0] = r), i[1] < n && (i[1] = n), i;
}, Es = {
	sign: (e) => {
		var t, n = e.length;
		if (!(n <= 0)) {
			var r = (t = e[0]) == null ? void 0 : t.length;
			if (!(r == null || r <= 0)) for (var i = 0; i < r; ++i) for (var a = 0, o = 0, s = 0; s < n; ++s) {
				var c = e[s], l = c == null ? void 0 : c[i];
				if (l != null) {
					var u = l[1], d = l[0], f = Kt(u) ? d : u;
					f >= 0 ? (l[0] = a, a += f, l[1] = a) : (l[0] = o, o += f, l[1] = o);
				}
			}
		}
	},
	expand: Mt,
	none: Dt,
	silhouette: Nt,
	wiggle: Pt,
	positive: (e) => {
		var t, n = e.length;
		if (!(n <= 0)) {
			var r = (t = e[0]) == null ? void 0 : t.length;
			if (!(r == null || r <= 0)) for (var i = 0; i < r; ++i) for (var a = 0, o = 0; o < n; ++o) {
				var s = e[o], c = s == null ? void 0 : s[i];
				if (c != null) {
					var l = Kt(c[1]) ? c[0] : c[1];
					l >= 0 ? (c[0] = a, a += l, c[1] = a) : (c[0] = 0, c[1] = 0);
				}
			}
		}
	}
}, Ds = (e, t, n) => {
	var r, i = (r = Es[n]) == null ? Dt : r, a = jt().keys(t).value((e, t) => Number(W(e, t, 0))).order(Ot).offset(i)(e);
	return a.forEach((n, r) => {
		n.forEach((n, i) => {
			var a = W(e[i], t[r], 0);
			Array.isArray(a) && a.length === 2 && I(a[0]) && I(a[1]) && (n[0] = a[0], n[1] = a[1]);
		});
	}), a;
};
function Os(e) {
	return e == null ? void 0 : String(e);
}
var ks = (e) => {
	var t = e.axis, n = e.ticks, r = e.offset, i = e.bandSize, a = e.entry, o = e.index;
	if (t.type === "category") return n[o] ? n[o].coordinate + r : null;
	var s = W(a, t.dataKey, t.scale.domain()[o]);
	if (en(s)) return null;
	var c = t.scale.map(s);
	return I(c) ? c - i / 2 + r : null;
}, As = (e) => {
	var t = e.numericAxis, n = t.scale.domain();
	if (t.type === "number") {
		var r = Math.min(n[0], n[1]), i = Math.max(n[0], n[1]);
		return r <= 0 && i >= 0 ? 0 : i < 0 ? i : r;
	}
	return n[0];
}, js = (e) => {
	var t = e.flat(2).filter(I);
	return [Math.min(...t), Math.max(...t)];
}, Ms = (e) => [e[0] === Infinity ? 0 : e[0], e[1] === -Infinity ? 0 : e[1]], Ns = (e, t, n) => {
	if (!(e == null || Object.keys(e).length === 0)) return Ms(Object.keys(e).reduce((r, i) => {
		var a = e[i];
		if (!a) return r;
		var o = a.stackedData.reduce((e, r) => {
			var i = js(gs(r, t, n));
			return !U(i[0]) || !U(i[1]) ? e : [Math.min(e[0], i[0]), Math.max(e[1], i[1])];
		}, [Infinity, -Infinity]);
		return [Math.min(o[0], r[0]), Math.max(o[1], r[1])];
	}, [Infinity, -Infinity]));
}, Ps = /^dataMin[\s]*-[\s]*([0-9]+([.]{1}[0-9]+){0,1})$/, Fs = /^dataMax[\s]*\+[\s]*([0-9]+([.]{1}[0-9]+){0,1})$/, Is = (e, t, n) => {
	if (e && e.scale && e.scale.bandwidth) {
		var r = e.scale.bandwidth();
		if (!n || r > 0) return r;
	}
	if (e && t && t.length >= 2) {
		for (var i = ai(t, (e) => e.coordinate), a = Infinity, o = 1, s = i.length; o < s; o++) {
			var c = i[o], l = i[o - 1];
			a = Math.min(((c == null ? void 0 : c.coordinate) || 0) - ((l == null ? void 0 : l.coordinate) || 0), a);
		}
		return a === Infinity ? 0 : a;
	}
	return n ? void 0 : 0;
};
function Ls(e) {
	var t = e.tooltipEntrySettings, n = e.dataKey, r = e.payload, i = e.value, a = e.name;
	return ys(ys({}, t), {}, {
		dataKey: n,
		payload: r,
		value: i,
		name: a
	});
}
function Rs(e, t) {
	if (e != null) return String(e);
	if (typeof t == "string") return t;
}
var zs = (e, t) => {
	if (t === "horizontal") return e.relativeX;
	if (t === "vertical") return e.relativeY;
}, Bs = (e, t) => t === "centric" ? e.angle : e.radius, Vs = (e) => e.layout.width, Hs = (e) => e.layout.height, Us = (e) => e.layout.scale, Ws = (e) => e.layout.margin, Gs = R((e) => e.cartesianAxis.xAxis, (e) => Object.values(e)), Ks = R((e) => e.cartesianAxis.yAxis, (e) => Object.values(e)), qs = "data-recharts-item-index";
//#endregion
//#region node_modules/recharts/es6/state/selectors/selectChartOffsetInternal.js
function Js(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Ys(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Js(Object(n), !0).forEach(function(t) {
			Xs(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Js(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Xs(e, t, n) {
	return (t = Zs(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function Zs(e) {
	var t = Qs(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Qs(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var $s = (e) => e.brush.height;
function ec(e) {
	return Ks(e).reduce((e, t) => t.orientation === "left" && !t.mirror && !t.hide ? e + (typeof t.width == "number" ? t.width : 60) : e, 0);
}
function tc(e) {
	return Ks(e).reduce((e, t) => t.orientation === "right" && !t.mirror && !t.hide ? e + (typeof t.width == "number" ? t.width : 60) : e, 0);
}
function nc(e) {
	return Gs(e).reduce((e, t) => t.orientation === "top" && !t.mirror && !t.hide ? e + t.height : e, 0);
}
function rc(e) {
	return Gs(e).reduce((e, t) => t.orientation === "bottom" && !t.mirror && !t.hide ? e + t.height : e, 0);
}
var ic = R([
	Vs,
	Hs,
	Ws,
	$s,
	ec,
	tc,
	nc,
	rc,
	oi,
	si
], (e, t, n, r, i, a, o, s, c, l) => {
	var u = {
		left: (n.left || 0) + i,
		right: (n.right || 0) + a
	}, d = Ys(Ys({}, {
		top: (n.top || 0) + o,
		bottom: (n.bottom || 0) + s
	}), u), f = d.bottom;
	d.bottom += r, d = Cs(d, c, l);
	var p = e - d.left - d.right, m = t - d.top - d.bottom;
	return Ys(Ys({ brushBottom: f }, d), {}, {
		width: Math.max(p, 0),
		height: Math.max(m, 0)
	});
}), ac = R(ic, (e) => ({
	x: e.left,
	y: e.top,
	width: e.width,
	height: e.height
})), oc = R(Vs, Hs, (e, t) => ({
	x: 0,
	y: 0,
	width: e,
	height: t
})), sc = /*#__PURE__*/ (0, C.createContext)(null), cc = () => (0, C.useContext)(sc) != null, lc = (e) => e.brush, uc = R([
	lc,
	ic,
	Ws
], (e, t, n) => ({
	height: e.height,
	x: I(e.x) ? e.x : t.left,
	y: I(e.y) ? e.y : t.top + t.height + t.brushBottom - ((n == null ? void 0 : n.bottom) || 0),
	width: I(e.width) ? e.width : t.width
}));
//#endregion
//#region node_modules/es-toolkit/dist/function/debounce.mjs
function dc(e, t, { signal: n, edges: r } = {}) {
	let i, a = null, o = r != null && r.includes("leading"), s = r == null || r.includes("trailing"), c = () => {
		a !== null && (e.apply(i, a), i = void 0, a = null);
	}, l = () => {
		s && c(), p();
	}, u = null, d = () => {
		u != null && clearTimeout(u), u = setTimeout(() => {
			u = null, l();
		}, t);
	}, f = () => {
		u !== null && (clearTimeout(u), u = null);
	}, p = () => {
		f(), i = void 0, a = null;
	}, m = () => {
		c();
	}, h = function(...e) {
		if (n != null && n.aborted) return;
		i = this, a = e;
		let t = u == null;
		d(), o && t && c();
	};
	return h.schedule = d, h.cancel = p, h.flush = m, n == null || n.addEventListener("abort", p, { once: !0 }), h;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/function/debounce.mjs
function fc(e, t = 0, n = {}) {
	typeof n != "object" && (n = {});
	let { leading: r = !1, trailing: i = !0, maxWait: a } = n, o = [, ,];
	r && (o[0] = "leading"), i && (o[1] = "trailing");
	let s, c = null, l = dc(function(...t) {
		s = e.apply(this, t), c = null;
	}, t, { edges: o }), u = function(...t) {
		return a != null && (c === null && (c = Date.now()), Date.now() - c >= a) ? (s = e.apply(this, t), c = Date.now(), l.cancel(), l.schedule(), s) : (l.apply(this, t), s);
	};
	return u.cancel = l.cancel, u.flush = () => (l.flush(), s), u;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/function/throttle.mjs
function pc(e, t = 0, n = {}) {
	let { leading: r = !0, trailing: i = !0 } = n;
	return fc(e, t, {
		leading: r,
		maxWait: t,
		trailing: i
	});
}
//#endregion
//#region node_modules/recharts/es6/util/LogUtils.js
var mc = function(e, t) {
	var n = [...arguments].slice(2);
	if (typeof console < "u" && console.warn && (t === void 0 && console.warn("LogUtils requires an error message argument"), !e)) if (t === void 0) console.warn("Minified exception occurred; use the non-minified dev environment for the full error message and additional helpful warnings.");
	else {
		var r = 0;
		console.warn(t.replace(/%s/g, () => n[r++]));
	}
}, hc = {
	width: "100%",
	height: "100%",
	debounce: 0,
	minWidth: 0,
	initialDimension: {
		width: -1,
		height: -1
	}
}, gc = (e, t, n) => {
	var r = n.width, i = r === void 0 ? hc.width : r, a = n.height, o = a === void 0 ? hc.height : a, s = n.aspect, c = n.maxHeight, l = F(i) ? e : Number(i), u = F(o) ? t : Number(o);
	return s && s > 0 && (l ? u = l / s : u && (l = u * s), c && u != null && u > c && (u = c)), {
		calculatedWidth: l,
		calculatedHeight: u
	};
}, _c = {
	width: 0,
	height: 0,
	overflow: "visible"
}, vc = {
	width: 0,
	overflowX: "visible"
}, G = {
	height: 0,
	overflowY: "visible"
}, yc = {}, bc = (e) => {
	var t = e.width, n = e.height, r = F(t), i = F(n);
	return r && i ? _c : r ? vc : i ? G : yc;
};
function xc(e) {
	var t = e.width, n = e.height, r = e.aspect, i = t, a = n;
	return i === void 0 && a === void 0 ? (i = hc.width, a = hc.height) : i === void 0 ? i = r && r > 0 ? void 0 : hc.width : a === void 0 && (a = r && r > 0 ? void 0 : hc.height), {
		width: i,
		height: a
	};
}
//#endregion
//#region node_modules/recharts/es6/component/ResponsiveContainer.js
var Sc = [
	"aspect",
	"initialDimension",
	"width",
	"height",
	"minWidth",
	"minHeight",
	"maxHeight",
	"children",
	"debounce",
	"id",
	"className",
	"onResize",
	"style"
];
function Cc() {
	return Cc = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, Cc.apply(null, arguments);
}
function wc(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Tc(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? wc(Object(n), !0).forEach(function(t) {
			Ec(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : wc(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Ec(e, t, n) {
	return (t = Dc(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function Dc(e) {
	var t = Oc(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Oc(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function kc(e, t) {
	return Pc(e) || Nc(e, t) || jc(e, t) || Ac();
}
function Ac() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function jc(e, t) {
	if (e) {
		if (typeof e == "string") return Mc(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? Mc(e, t) : void 0;
	}
}
function Mc(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function Nc(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function Pc(e) {
	if (Array.isArray(e)) return e;
}
function Fc(e, t) {
	if (e == null) return {};
	var n, r, i = Ic(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function Ic(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var Lc = /*#__PURE__*/ (0, C.createContext)(hc.initialDimension);
function Rc(e) {
	return _s(e.width) && _s(e.height);
}
function zc(e) {
	var t = e.children, n = e.width, r = e.height, i = (0, C.useMemo)(() => ({
		width: n,
		height: r
	}), [n, r]);
	return Rc(i) ? /*#__PURE__*/ C.createElement(Lc.Provider, { value: i }, t) : null;
}
var Bc = () => (0, C.useContext)(Lc), Vc = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.aspect, r = e.initialDimension, i = r === void 0 ? hc.initialDimension : r, a = e.width, o = e.height, s = e.minWidth, c = s === void 0 ? hc.minWidth : s, l = e.minHeight, u = e.maxHeight, d = e.children, f = e.debounce, p = f === void 0 ? hc.debounce : f, m = e.id, h = e.className, g = e.onResize, _ = e.style, v = _ === void 0 ? {} : _, y = Fc(e, Sc), b = (0, C.useRef)(null), x = (0, C.useRef)();
	x.current = g, (0, C.useImperativeHandle)(t, () => b.current);
	var S = kc((0, C.useState)({
		containerWidth: i.width,
		containerHeight: i.height
	}), 2), w = S[0], T = S[1], E = (0, C.useCallback)((e, t) => {
		T((n) => {
			var r = Math.round(e), i = Math.round(t);
			return n.containerWidth === r && n.containerHeight === i ? n : {
				containerWidth: r,
				containerHeight: i
			};
		});
	}, []);
	(0, C.useEffect)(() => {
		if (b.current == null || typeof ResizeObserver > "u") return rn;
		var e = (e) => {
			var t, n = e[0];
			if (n != null) {
				var r = n.contentRect, i = r.width, a = r.height;
				E(i, a), (t = x.current) == null || t.call(x, i, a);
			}
		};
		p > 0 && (e = pc(e, p, {
			trailing: !0,
			leading: !1
		}));
		var t = new ResizeObserver(e), n = b.current.getBoundingClientRect(), r = n.width, i = n.height;
		return E(r, i), t.observe(b.current), () => {
			t.disconnect();
		};
	}, [E, p]);
	var D = w.containerWidth, O = w.containerHeight;
	mc(!n || n > 0, "The aspect(%s) must be greater than zero.", n);
	var k = gc(D, O, {
		width: a,
		height: o,
		aspect: n,
		maxHeight: u
	}), A = k.calculatedWidth, j = k.calculatedHeight;
	return mc(D < 0 || O < 0 || A != null && A > 0 || j != null && j > 0, "The width(%s) and height(%s) of chart should be greater than 0,\n       please check the style of container, or the props width(%s) and height(%s),\n       or add a minWidth(%s) or minHeight(%s) or use aspect(%s) to control the\n       height and width.", A, j, a, o, c, l, n), /*#__PURE__*/ C.createElement("div", Cc({
		id: m ? `${m}` : void 0,
		className: he("recharts-responsive-container", h),
		style: Tc(Tc({}, v), {}, {
			width: a,
			height: o,
			minWidth: c,
			minHeight: l,
			maxHeight: u
		}),
		ref: b
	}, y), /*#__PURE__*/ C.createElement("div", { style: bc({
		width: a,
		height: o
	}) }, /*#__PURE__*/ C.createElement(zc, {
		width: A,
		height: j
	}, d)));
}), Hc = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = Bc();
	if (_s(n.width) && _s(n.height)) return e.children;
	var r = xc({
		width: e.width,
		height: e.height,
		aspect: e.aspect
	}), i = r.width, a = r.height, o = gc(void 0, void 0, {
		width: i,
		height: a,
		aspect: e.aspect,
		maxHeight: e.maxHeight
	}), s = o.calculatedWidth, c = o.calculatedHeight;
	return I(s) && I(c) ? /*#__PURE__*/ C.createElement(zc, {
		width: s,
		height: c
	}, e.children) : /*#__PURE__*/ C.createElement(Vc, Cc({}, e, {
		width: i,
		height: a,
		ref: t
	}));
});
//#endregion
//#region node_modules/recharts/es6/context/chartLayoutContext.js
function Uc(e) {
	if (e) return {
		x: e.x,
		y: e.y,
		upperWidth: "upperWidth" in e ? e.upperWidth : e.width,
		lowerWidth: "lowerWidth" in e ? e.lowerWidth : e.width,
		width: e.width,
		height: e.height
	};
}
var Wc = () => {
	var e, t = cc(), n = L(ac), r = L(uc), i = (e = L(lc)) == null ? void 0 : e.padding;
	return !t || !r || !i ? n : {
		width: r.width - i.left - i.right,
		height: r.height - i.top - i.bottom,
		x: i.left,
		y: i.top
	};
}, Gc = {
	top: 0,
	bottom: 0,
	left: 0,
	right: 0,
	width: 0,
	height: 0,
	brushBottom: 0
}, Kc = () => {
	var e;
	return (e = L(ic)) == null ? Gc : e;
}, qc = () => L(Vs), K = () => L(Hs), q = (e) => e.layout.layoutType, Jc = () => L(q), Yc = () => {
	var e = Jc();
	if (e === "horizontal" || e === "vertical") return e;
}, Xc = (e) => {
	var t = e.layout.layoutType;
	if (t === "centric" || t === "radial") return t;
}, Zc = () => Jc() !== void 0, Qc = (e) => {
	var t = kr(), n = cc(), r = e.width, i = e.height, a = Bc(), o = r, s = i;
	return a && (o = a.width > 0 ? a.width : r, s = a.height > 0 ? a.height : i), (0, C.useEffect)(() => {
		!n && _s(o) && _s(s) && t(ps({
			width: o,
			height: s
		}));
	}, [
		t,
		n,
		o,
		s
	]), null;
}, $c = xo({
	name: "legend",
	initialState: {
		settings: {
			layout: "horizontal",
			align: "center",
			verticalAlign: "bottom",
			itemSorter: "value"
		},
		size: {
			width: 0,
			height: 0
		},
		payload: []
	},
	reducers: {
		setLegendSize(e, t) {
			e.size.width = t.payload.width, e.size.height = t.payload.height;
		},
		setLegendSettings(e, t) {
			e.settings.align = t.payload.align, e.settings.layout = t.payload.layout, e.settings.verticalAlign = t.payload.verticalAlign, e.settings.itemSorter = t.payload.itemSorter;
		},
		addLegendPayload: {
			reducer(e, t) {
				e.payload.push(H(t.payload));
			},
			prepare: ao()
		},
		replaceLegendPayload: {
			reducer(e, t) {
				var n = t.payload, r = n.prev, i = n.next, a = Ga(e).payload.indexOf(H(r));
				a > -1 && (e.payload[a] = H(i));
			},
			prepare: ao()
		},
		removeLegendPayload: {
			reducer(e, t) {
				var n = Ga(e).payload.indexOf(H(t.payload));
				n > -1 && e.payload.splice(n, 1);
			},
			prepare: ao()
		}
	}
}), el = $c.actions;
el.setLegendSize, el.setLegendSettings;
var tl = el.addLegendPayload, nl = el.replaceLegendPayload, rl = el.removeLegendPayload, il = $c.reducer, al = /* @__PURE__ */ o(((e) => {
	var t = d();
	t.useSyncExternalStore, t.useRef, t.useEffect, t.useMemo, t.useDebugValue;
}));
(/* @__PURE__ */ o(((e, t) => {
	t.exports = al();
})))();
function ol(e) {
	e();
}
function sl() {
	let e = null, t = null;
	return {
		clear() {
			e = null, t = null;
		},
		notify() {
			ol(() => {
				let t = e;
				for (; t;) t.callback(), t = t.next;
			});
		},
		get() {
			let t = [], n = e;
			for (; n;) t.push(n), n = n.next;
			return t;
		},
		subscribe(n) {
			let r = !0, i = t = {
				callback: n,
				next: null,
				prev: t
			};
			return i.prev ? i.prev.next = i : e = i, function() {
				!r || e === null || (r = !1, i.next ? i.next.prev = i.prev : t = i.prev, i.prev ? i.prev.next = i.next : e = i.next);
			};
		}
	};
}
var cl = {
	notify() {},
	get: () => []
};
function ll(e, t) {
	let n, r = cl, i = 0, a = !1;
	function o(e) {
		u();
		let t = r.subscribe(e), n = !1;
		return () => {
			n || (n = !0, t(), d());
		};
	}
	function s() {
		r.notify();
	}
	function c() {
		m.onStateChange && m.onStateChange();
	}
	function l() {
		return a;
	}
	function u() {
		i++, n || (n = t ? t.addNestedSub(c) : e.subscribe(c), r = sl());
	}
	function d() {
		i--, n && i === 0 && (n(), n = void 0, r.clear(), r = cl);
	}
	function f() {
		a || (a = !0, u());
	}
	function p() {
		a && (a = !1, d());
	}
	let m = {
		addNestedSub: o,
		notifyNestedSubs: s,
		handleChangeWrapper: c,
		isSubscribed: l,
		trySubscribe: f,
		tryUnsubscribe: p,
		getListeners: () => r
	};
	return m;
}
var ul = typeof window < "u" && window.document !== void 0 && window.document.createElement !== void 0, dl = typeof navigator < "u" && navigator.product === "ReactNative", fl = ul || dl ? C.useLayoutEffect : C.useEffect;
function pl(e, t) {
	return e === t ? e !== 0 || t !== 0 || 1 / e == 1 / t : e !== e && t !== t;
}
function ml(e, t) {
	if (pl(e, t)) return !0;
	if (typeof e != "object" || !e || typeof t != "object" || !t) return !1;
	let n = Object.keys(e), r = Object.keys(t);
	if (n.length !== r.length) return !1;
	for (let r = 0; r < n.length; r++) if (!Object.prototype.hasOwnProperty.call(t, n[r]) || !pl(e[n[r]], t[n[r]])) return !1;
	return !0;
}
var hl = /* @__PURE__ */ Symbol.for("react-redux-context"), gl = typeof globalThis < "u" ? globalThis : {};
function _l() {
	var e;
	if (!C.createContext) return {};
	let t = (e = gl[hl]) == null ? gl[hl] = /* @__PURE__ */ new Map() : e, n = t.get(C.createContext);
	return n || (n = C.createContext(null), t.set(C.createContext, n)), n;
}
var vl = /* @__PURE__ */ _l();
function yl(e) {
	let { children: t, context: n, serverState: r, store: i } = e, a = C.useMemo(() => {
		let e = ll(i);
		return {
			store: i,
			subscription: e,
			getServerState: r ? () => r : void 0
		};
	}, [i, r]), o = C.useMemo(() => i.getState(), [i]);
	fl(() => {
		let { subscription: e } = a;
		return e.onStateChange = e.notifyNestedSubs, e.trySubscribe(), o !== i.getState() && e.notifyNestedSubs(), () => {
			e.tryUnsubscribe(), e.onStateChange = void 0;
		};
	}, [a, o]);
	let s = n || vl;
	return /* @__PURE__ */ C.createElement(s.Provider, { value: a }, t);
}
var bl = yl, xl = /* @__PURE__ */ new Set([
	"axisLine",
	"tickLine",
	"activeBar",
	"activeDot",
	"activeLabel",
	"activeShape",
	"allowEscapeViewBox",
	"background",
	"cursor",
	"dot",
	"label",
	"line",
	"margin",
	"padding",
	"position",
	"shape",
	"style",
	"tick",
	"wrapperStyle",
	"radius",
	"throttledEvents"
]);
function Sl(e, t) {
	return e == null && t == null ? !0 : typeof e == "number" && typeof t == "number" ? e === t || e !== e && t !== t : e === t;
}
function Cl(e, t) {
	for (var n of /* @__PURE__ */ new Set([...Object.keys(e), ...Object.keys(t)])) if (xl.has(n)) {
		if (e[n] == null && t[n] == null) continue;
		if (!ml(e[n], t[n])) return !1;
	} else if (!Sl(e[n], t[n])) return !1;
	return !0;
}
//#endregion
//#region node_modules/recharts/es6/component/DefaultTooltipContent.js
function wl() {
	return wl = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, wl.apply(null, arguments);
}
function Tl(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function El(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Tl(Object(n), !0).forEach(function(t) {
			Dl(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Tl(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Dl(e, t, n) {
	return (t = Ol(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function Ol(e) {
	var t = kl(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function kl(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function Al(e, t) {
	return Fl(e) || Pl(e, t) || Ml(e, t) || jl();
}
function jl() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function Ml(e, t) {
	if (e) {
		if (typeof e == "string") return Nl(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? Nl(e, t) : void 0;
	}
}
function Nl(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function Pl(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function Fl(e) {
	if (Array.isArray(e)) return e;
}
function Il(e) {
	return Array.isArray(e) && qt(e[0]) && qt(e[1]) ? e.join(" ~ ") : e;
}
var Ll = {
	separator: " : ",
	contentStyle: {
		margin: 0,
		padding: 10,
		backgroundColor: "#fff",
		border: "1px solid #ccc",
		whiteSpace: "nowrap"
	},
	itemStyle: {
		display: "block",
		paddingTop: 4,
		paddingBottom: 4,
		color: "#000"
	},
	labelStyle: {},
	accessibilityLayer: !1
};
function Rl(e, t) {
	return t == null ? e : ai(e, t);
}
var zl = (e) => {
	var t = e.separator, n = t === void 0 ? Ll.separator : t, r = e.contentStyle, i = e.itemStyle, a = e.labelStyle, o = a === void 0 ? Ll.labelStyle : a, s = e.payload, c = e.formatter, l = e.itemSorter, u = e.wrapperClassName, d = e.labelClassName, f = e.label, p = e.labelFormatter, m = e.accessibilityLayer, h = m === void 0 ? Ll.accessibilityLayer : m, g = () => {
		if (s && s.length) {
			var e = {
				padding: 0,
				margin: 0
			}, t = Rl(s, l).map((e, t) => {
				if (!e || e.type === "none") return null;
				var r = e.formatter || c || Il, a = e.value, o = e.name, l = a, u = o;
				if (r) {
					var d = r(a, o, e, t, s);
					if (Array.isArray(d)) {
						var f = Al(d, 2);
						l = f[0], u = f[1];
					} else if (d != null) l = d;
					else return null;
				}
				var p = El(El({}, Ll.itemStyle), {}, { color: e.color || Ll.itemStyle.color }, i);
				return /*#__PURE__*/ C.createElement("li", {
					className: "recharts-tooltip-item",
					key: `tooltip-item-${t}`,
					style: p
				}, qt(u) ? /*#__PURE__*/ C.createElement("span", { className: "recharts-tooltip-item-name" }, u) : null, qt(u) ? /*#__PURE__*/ C.createElement("span", { className: "recharts-tooltip-item-separator" }, n) : null, /*#__PURE__*/ C.createElement("span", { className: "recharts-tooltip-item-value" }, l), /*#__PURE__*/ C.createElement("span", { className: "recharts-tooltip-item-unit" }, e.unit || ""));
			});
			return /*#__PURE__*/ C.createElement("ul", {
				className: "recharts-tooltip-item-list",
				style: e
			}, t);
		}
		return null;
	}, _ = El(El({}, Ll.contentStyle), r), v = El({ margin: 0 }, o), y = !en(f), b = y ? f : "", x = he("recharts-default-tooltip", u), S = he("recharts-tooltip-label", d);
	y && p && s != null && (b = p(f, s));
	var w = h ? {
		role: "status",
		"aria-live": "assertive"
	} : {};
	return /*#__PURE__*/ C.createElement("div", wl({
		className: x,
		style: _
	}, w), /*#__PURE__*/ C.createElement("p", {
		className: S,
		style: v
	}, /*#__PURE__*/ C.isValidElement(b) ? b : `${b}`), g());
}, Bl = "recharts-tooltip-wrapper", Vl = { visibility: "hidden" };
function Hl(e) {
	var t = e.coordinate, n = e.translateX, r = e.translateY;
	return he(Bl, {
		[`${Bl}-right`]: I(n) && t && I(t.x) && n >= t.x,
		[`${Bl}-left`]: I(n) && t && I(t.x) && n < t.x,
		[`${Bl}-bottom`]: I(r) && t && I(t.y) && r >= t.y,
		[`${Bl}-top`]: I(r) && t && I(t.y) && r < t.y
	});
}
function Ul(e) {
	var t = e.allowEscapeViewBox, n = e.coordinate, r = e.key, i = e.offset, a = e.position, o = e.reverseDirection, s = e.tooltipDimension, c = e.viewBox, l = e.viewBoxDimension;
	if (a && I(a[r])) return a[r];
	var u = n[r] - s - (i > 0 ? i : 0), d = n[r] + i;
	if (t[r]) return o[r] ? u : d;
	var f = c[r];
	return f == null ? 0 : o[r] ? Math.max(u < f ? d : u, f) : l == null ? 0 : d + s > f + l ? Math.max(u, f) : Math.max(d, f);
}
function Wl(e) {
	var t = e.translateX, n = e.translateY;
	return { transform: e.useTranslate3d ? `translate3d(${t}px, ${n}px, 0)` : `translate(${t}px, ${n}px)` };
}
function Gl(e) {
	var t = e.allowEscapeViewBox, n = e.coordinate, r = e.offsetTop, i = e.offsetLeft, a = e.position, o = e.reverseDirection, s = e.tooltipBox, c = e.useTranslate3d, l = e.viewBox, u, d, f;
	return s.height > 0 && s.width > 0 && n ? (d = Ul({
		allowEscapeViewBox: t,
		coordinate: n,
		key: "x",
		offset: i,
		position: a,
		reverseDirection: o,
		tooltipDimension: s.width,
		viewBox: l,
		viewBoxDimension: l.width
	}), f = Ul({
		allowEscapeViewBox: t,
		coordinate: n,
		key: "y",
		offset: r,
		position: a,
		reverseDirection: o,
		tooltipDimension: s.height,
		viewBox: l,
		viewBoxDimension: l.height
	}), u = Wl({
		translateX: d,
		translateY: f,
		useTranslate3d: c
	})) : u = Vl, {
		cssProperties: u,
		cssClasses: Hl({
			translateX: d,
			translateY: f,
			coordinate: n
		})
	};
}
var Kl = {
	devToolsEnabled: !0,
	isSsr: !(typeof window < "u" && window.document && window.document.createElement && window.setTimeout)
};
//#endregion
//#region node_modules/recharts/es6/util/usePrefersReducedMotion.js
function ql(e, t) {
	return Ql(e) || Zl(e, t) || Yl(e, t) || Jl();
}
function Jl() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function Yl(e, t) {
	if (e) {
		if (typeof e == "string") return Xl(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? Xl(e, t) : void 0;
	}
}
function Xl(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function Zl(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function Ql(e) {
	if (Array.isArray(e)) return e;
}
function $l() {
	var e = ql((0, C.useState)(() => Kl.isSsr || !window.matchMedia ? !1 : window.matchMedia("(prefers-reduced-motion: reduce)").matches), 2), t = e[0], n = e[1];
	return (0, C.useEffect)(() => {
		if (window.matchMedia) {
			var e = window.matchMedia("(prefers-reduced-motion: reduce)"), t = () => {
				n(e.matches);
			};
			return e.addEventListener("change", t), () => {
				e.removeEventListener("change", t);
			};
		}
	}, []), t;
}
//#endregion
//#region node_modules/recharts/es6/component/TooltipBoundingBox.js
function eu(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function tu(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? eu(Object(n), !0).forEach(function(t) {
			nu(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : eu(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function nu(e, t, n) {
	return (t = ru(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function ru(e) {
	var t = iu(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function iu(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function au(e, t) {
	return uu(e) || lu(e, t) || su(e, t) || ou();
}
function ou() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function su(e, t) {
	if (e) {
		if (typeof e == "string") return cu(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? cu(e, t) : void 0;
	}
}
function cu(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function lu(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function uu(e) {
	if (Array.isArray(e)) return e;
}
function du(e) {
	if (!(e.prefersReducedMotion && e.isAnimationActive === "auto") && e.isAnimationActive && e.active) {
		var t = typeof e.animationEasing == "string" ? e.animationEasing : "ease";
		return `transform ${e.animationDuration}ms ${t}`;
	}
}
function fu(e) {
	var t, n, r, i, a, o, s = $l(), c = au(C.useState(() => ({
		dismissed: !1,
		dismissedAtCoordinate: {
			x: 0,
			y: 0
		}
	})), 2), l = c[0], u = c[1];
	C.useEffect(() => {
		var t = (t) => {
			if (t.key === "Escape") {
				var n, r, i, a;
				u({
					dismissed: !0,
					dismissedAtCoordinate: {
						x: (n = (r = e.coordinate) == null ? void 0 : r.x) == null ? 0 : n,
						y: (i = (a = e.coordinate) == null ? void 0 : a.y) == null ? 0 : i
					}
				});
			}
		};
		return document.addEventListener("keydown", t), () => {
			document.removeEventListener("keydown", t);
		};
	}, [(t = e.coordinate) == null ? void 0 : t.x, (n = e.coordinate) == null ? void 0 : n.y]), l.dismissed && (((r = (i = e.coordinate) == null ? void 0 : i.x) == null ? 0 : r) !== l.dismissedAtCoordinate.x || ((a = (o = e.coordinate) == null ? void 0 : o.y) == null ? 0 : a) !== l.dismissedAtCoordinate.y) && u(tu(tu({}, l), {}, { dismissed: !1 }));
	var d = Gl({
		allowEscapeViewBox: e.allowEscapeViewBox,
		coordinate: e.coordinate,
		offsetLeft: typeof e.offset == "number" ? e.offset : e.offset.x,
		offsetTop: typeof e.offset == "number" ? e.offset : e.offset.y,
		position: e.position,
		reverseDirection: e.reverseDirection,
		tooltipBox: {
			height: e.lastBoundingBox.height,
			width: e.lastBoundingBox.width
		},
		useTranslate3d: e.useTranslate3d,
		viewBox: e.viewBox
	}), f = d.cssClasses, p = d.cssProperties, m = tu(tu({}, e.hasPortalFromProps ? {} : tu(tu({ transition: du({
		prefersReducedMotion: s,
		isAnimationActive: e.isAnimationActive,
		active: e.active,
		animationDuration: e.animationDuration,
		animationEasing: e.animationEasing
	}) }, p), {}, {
		pointerEvents: "none",
		position: "absolute",
		top: 0,
		left: 0
	})), {}, { visibility: !l.dismissed && e.active && e.hasPayload ? "visible" : "hidden" }, e.wrapperStyle);
	return /*#__PURE__*/ C.createElement("div", {
		xmlns: "http://www.w3.org/1999/xhtml",
		tabIndex: -1,
		className: f,
		style: m,
		ref: e.innerRef
	}, e.children);
}
var pu = /*#__PURE__*/ C.memo(fu), mu = () => {
	var e;
	return (e = L((e) => e.rootProps.accessibilityLayer)) == null || e;
};
//#endregion
//#region node_modules/recharts/es6/shape/Curve.js
function hu() {
	return hu = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, hu.apply(null, arguments);
}
function gu(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function _u(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? gu(Object(n), !0).forEach(function(t) {
			vu(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : gu(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function vu(e, t, n) {
	return (t = yu(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function yu(e) {
	var t = bu(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function bu(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var xu = {
	curveBasisClosed: ot,
	curveBasisOpen: ct,
	curveBasis: it,
	curveBumpX: $e,
	curveBumpY: et,
	curveLinearClosed: ut,
	curveLinear: qe,
	curveMonotoneX: vt,
	curveMonotoneY: yt,
	curveNatural: St,
	curveStep: wt,
	curveStepAfter: Et,
	curveStepBefore: Tt
}, Su = (e) => U(e.x) && U(e.y), Cu = (e) => e.base != null && Su(e.base) && Su(e), wu = (e) => e.x, Tu = (e) => e.y, Eu = (e, t) => {
	if (typeof e == "function") return e;
	var n = `curve${tn(e)}`;
	if ((n === "curveMonotone" || n === "curveBump") && t) {
		var r = xu[`${n}${t === "vertical" ? "Y" : "X"}`];
		if (r) return r;
	}
	return xu[n] || qe;
}, Du = {
	connectNulls: !1,
	type: "linear"
}, Ou = (e) => {
	var t = e.type, n = t === void 0 ? Du.type : t, r = e.points, i = r === void 0 ? [] : r, a = e.baseLine, o = e.layout, s = e.connectNulls, c = s === void 0 ? Du.connectNulls : s, l = Eu(n, o), u = c ? i.filter(Su) : i;
	if (Array.isArray(a)) {
		var d, f = i.map((e, t) => _u(_u({}, e), {}, { base: a[t] }));
		return d = o === "vertical" ? Ze().y(Tu).x1(wu).x0((e) => e.base.x) : Ze().x(wu).y1(Tu).y0((e) => e.base.y), d.defined(Cu).curve(l)(c ? f.filter(Cu) : f);
	}
	return (o === "vertical" && I(a) ? Ze().y(Tu).x1(wu).x0(a) : I(a) ? Ze().x(wu).y1(Tu).y0(a) : Xe().x(wu).y(Tu)).defined(Su).curve(l)(u);
}, ku = (e) => {
	var t = e.className, n = e.points, r = e.path, i = e.pathRef, a = Jc();
	if ((!n || !n.length) && !r) return null;
	var o = {
		type: e.type,
		points: e.points,
		baseLine: e.baseLine,
		layout: e.layout || a,
		connectNulls: e.connectNulls
	}, s = n && n.length ? Ou(o) : r;
	return /*#__PURE__*/ C.createElement("path", hu({}, xe(e), on(e), {
		className: he("recharts-curve", t),
		d: s === null ? void 0 : s,
		ref: i
	}));
}, Au = [
	"x",
	"y",
	"top",
	"left",
	"width",
	"height",
	"className"
];
function ju() {
	return ju = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, ju.apply(null, arguments);
}
function Mu(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Nu(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Mu(Object(n), !0).forEach(function(t) {
			Pu(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Mu(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Pu(e, t, n) {
	return (t = Fu(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function Fu(e) {
	var t = Iu(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Iu(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function Lu(e, t) {
	if (e == null) return {};
	var n, r, i = Ru(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function Ru(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var zu = (e, t, n, r, i, a) => `M${e},${i}v${r}M${a},${t}h${n}`, Bu = (e) => {
	var t = e.x, n = t === void 0 ? 0 : t, r = e.y, i = r === void 0 ? 0 : r, a = e.top, o = a === void 0 ? 0 : a, s = e.left, c = s === void 0 ? 0 : s, l = e.width, u = l === void 0 ? 0 : l, d = e.height, f = d === void 0 ? 0 : d, p = e.className, m = Lu(e, Au), h = Nu({
		x: n,
		y: i,
		top: o,
		left: c,
		width: u,
		height: f
	}, m);
	return !I(n) || !I(i) || !I(u) || !I(f) || !I(o) || !I(c) ? null : /*#__PURE__*/ C.createElement("path", ju({}, Ce(h), {
		className: he("recharts-cross", p),
		d: zu(n, i, u, f, o, c)
	}));
};
//#endregion
//#region node_modules/recharts/es6/util/cursor/getCursorRectangle.js
function Vu(e, t, n, r) {
	var i = r / 2;
	return {
		stroke: "none",
		fill: "#ccc",
		x: e === "horizontal" ? t.x - i : n.left + .5,
		y: e === "horizontal" ? n.top + .5 : t.y - i,
		width: e === "horizontal" ? r : n.width - 1,
		height: e === "horizontal" ? n.height - 1 : r
	};
}
var Hu = (e, t) => [
	0,
	3 * e,
	3 * t - 6 * e,
	3 * e - 3 * t + 1
], Uu = (e, t) => e.map((e, n) => e * t ** n).reduce((e, t) => e + t), Wu = (e, t) => (n) => Uu(Hu(e, t), n), Gu = (e, t) => (n) => Uu([...Hu(e, t).map((e, t) => e * t).slice(1), 0], n), Ku = (e) => {
	var t, n = e.split("(");
	if (n.length !== 2 || n[0] !== "cubic-bezier") return null;
	var r = (t = n[1]) == null || (t = t.split(")")[0]) == null ? void 0 : t.split(",");
	if (r == null || r.length !== 4) return null;
	var i = r.map((e) => parseFloat(e));
	return [
		i[0],
		i[1],
		i[2],
		i[3]
	];
}, qu = function() {
	var e = [...arguments];
	if (e.length === 1) switch (e[0]) {
		case "linear": return [
			0,
			0,
			1,
			1
		];
		case "ease": return [
			.25,
			.1,
			.25,
			1
		];
		case "ease-in": return [
			.42,
			0,
			1,
			1
		];
		case "ease-out": return [
			.42,
			0,
			.58,
			1
		];
		case "ease-in-out": return [
			0,
			0,
			.58,
			1
		];
		default:
			var t = Ku(e[0]);
			if (t) return t;
	}
	return e.length === 4 ? e : [
		0,
		0,
		1,
		1
	];
}, Ju = (e, t, n, r) => {
	var i = Wu(e, n), a = Wu(t, r), o = Gu(e, n), s = (e) => e > 1 ? 1 : e < 0 ? 0 : e, c = (e) => {
		for (var t = e > 1 ? 1 : e, n = t, r = 0; r < 8; ++r) {
			var c = i(n) - t, l = o(n);
			if (Math.abs(c - t) < 1e-4 || l < 1e-4) return a(n);
			n = s(n - c / l);
		}
		return a(n);
	};
	return c.isStepper = !1, c;
}, Yu = function() {
	return Ju(...qu(...arguments));
}, Xu = function() {
	for (var e = arguments.length > 0 && arguments[0] !== void 0 ? arguments[0] : {}, t = e.stiff, n = t === void 0 ? 100 : t, r = e.damping, i = r === void 0 ? 8 : r, a = e.dt, o = a === void 0 ? 16.67 : a, s = 1, c = [0], l = 0, u = 0, d = 1e4, f = 0; f < d;) {
		var p = -(l - s) * n, m = u * i;
		if (u += (p - m) * o / 1e3, l += u * o / 1e3, c.push(l), Math.abs(l - s) < 1e-4 && Math.abs(u) < 1e-4) break;
		f++;
	}
	c[c.length - 1] = s;
	var h = c.length - 1;
	return (e) => {
		var t, n, r;
		if (e <= 0) return 0;
		if (e >= 1) return s;
		var i = e * h, a = Math.floor(i), o = i - a;
		return ((t = c[a]) == null ? 0 : t) + (((n = c[a + 1]) == null ? 0 : n) - ((r = c[a]) == null ? 0 : r)) * o;
	};
}, Zu = (e) => {
	if (typeof e == "string") switch (e) {
		case "ease":
		case "ease-in-out":
		case "ease-out":
		case "ease-in":
		case "linear": return Yu(e);
		case "spring": return Xu();
		default: if (e.split("(")[0] === "cubic-bezier") return Yu(e);
	}
	return typeof e == "function" ? e : null;
}, Qu = /*#__PURE__*/ (0, C.createContext)((e, t, n) => {
	var r, i = (a) => {
		var o = t.tick(a);
		if (t.getState() === "active") {
			if (n(t.getInterpolated()), t.getProgress() === 1) {
				t.complete(), r = void 0;
				return;
			}
			r = e.setTimeout(i, o);
			return;
		}
		r = e.setTimeout(i, o);
	};
	return r = e.setTimeout(i, 0), () => {
		var e;
		return (e = r) == null ? void 0 : e();
	};
});
Qu.Provider;
function $u(e) {
	var t = (0, C.useContext)(Qu);
	return (0, C.useMemo)(() => e == null ? t : e, [e, t]);
}
//#endregion
//#region node_modules/recharts/es6/animation/AnimationHandle.js
function ed(e, t, n) {
	return (t = td(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function td(e) {
	var t = nd(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function nd(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var rd = "init", id = "pending", ad = "active", od = "completed";
function sd(e) {
	return Math.max(0, e);
}
var cd = class {
	getAnimationStartedTime() {
		return this.animationStartedTime;
	}
	getBeginStartedTime() {
		return this.beginStartedTime;
	}
	constructor(e) {
		var t;
		ed(this, "state", rd), this.animationId = e.animationId, this.onAnimationEnd = e.onAnimationEnd, this.animationDuration = sd(e.animationDuration), this.animationBegin = sd(e.animationBegin), this.progress = 0, this.from = e.from, this.to = e.to, this.easing = e.easing, (t = e.onAnimationStart) == null || t.call(e);
	}
	getState() {
		return this.state;
	}
	getEasing() {
		return this.easing;
	}
	getAnimationDuration() {
		return this.animationDuration;
	}
	tick(e) {
		if (this.getState() === rd) return this.state = id, this.beginStartedTime = e, this.animationBegin;
		if (this.getState() === id) {
			if (this.beginStartedTime == null) throw Error();
			var t = e - this.beginStartedTime;
			return t >= this.animationBegin ? (this.state = ad, this.animationStartedTime = e, this.nextAnimationUpdate(0)) : sd(this.animationBegin - t);
		}
		if (this.getState() === ad) {
			if (this.animationStartedTime == null) throw Error();
			var n = e - this.animationStartedTime;
			return this.setProgress(n / this.animationDuration), this.nextAnimationUpdate(n);
		}
		return 0;
	}
	setProgress(e) {
		this.progress = Math.min(1, Math.max(0, e));
	}
	getProgress() {
		return this.progress;
	}
	complete() {
		if (this.progress = 1, this.state === "active") {
			var e;
			(e = this.onAnimationEnd) == null || e.call(this);
		}
		this.state = od;
	}
	getFrom() {
		return this.from;
	}
	getTo() {
		return this.to;
	}
	getAnimationId() {
		return this.animationId;
	}
	getAnimationBegin() {
		return this.animationBegin;
	}
}, ld = class extends cd {
	nextAnimationUpdate() {
		return 0;
	}
	getInterpolated() {
		return this.easing(Qt(this.getFrom(), this.getTo(), this.getProgress()));
	}
}, ud = class {
	setTimeout(e) {
		var t = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : 0, n = performance.now(), r = null, i = (a) => {
			a - n >= t ? e(a) : r = requestAnimationFrame(i);
		};
		return r = requestAnimationFrame(i), () => {
			r != null && cancelAnimationFrame(r);
		};
	}
};
//#endregion
//#region node_modules/recharts/es6/animation/JavascriptAnimate.js
function dd(e, t) {
	return gd(e) || hd(e, t) || pd(e, t) || fd();
}
function fd() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function pd(e, t) {
	if (e) {
		if (typeof e == "string") return md(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? md(e, t) : void 0;
	}
}
function md(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function hd(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function gd(e) {
	if (Array.isArray(e)) return e;
}
var _d = {
	begin: 0,
	duration: 1e3,
	easing: "ease",
	isActive: !0,
	canBegin: !0,
	onAnimationEnd: () => {},
	onAnimationStart: () => {}
}, vd = 0, yd = 1;
function bd(e) {
	var t = mn(e, _d), n = t.animationId, r = t.isActive, i = t.canBegin, a = t.duration, o = t.easing, s = t.begin, c = t.onAnimationEnd, l = t.onAnimationStart, u = t.children, d = $l(), f = r === "auto" ? !Kl.isSsr && !d : r, p = $u(t.animationController), m = dd((0, C.useState)(f ? vd : yd), 2), h = m[0], g = m[1];
	return (0, C.useEffect)(() => {
		f || g(yd);
	}, [f]), (0, C.useEffect)(() => {
		var e = Zu(o);
		return !f || !i || e == null ? rn : p(new ud(), new ld({
			animationId: n,
			easing: e,
			animationDuration: a,
			animationBegin: s,
			onAnimationStart: l,
			onAnimationEnd: c,
			from: vd,
			to: yd
		}), g);
	}, [
		p,
		n,
		f,
		i,
		a,
		o,
		s,
		l,
		c
	]), u(Number(h));
}
//#endregion
//#region node_modules/recharts/es6/util/useAnimationId.js
function xd(e) {
	var t = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : "animation-", n = (0, C.useRef)(Yt(t)), r = (0, C.useRef)(e);
	return r.current !== e && (n.current = Yt(t), r.current = e), n.current;
}
//#endregion
//#region node_modules/recharts/es6/animation/util.js
var Sd = (e) => e.replace(/([A-Z])/g, (e) => `-${e.toLowerCase()}`), Cd = (e, t, n) => e.map((e) => `${Sd(e)} ${t}ms ${n}`).join(","), wd = ["radius"], Td = ["radius"], Ed, Dd, Od, kd, Ad, jd, Md, Nd, Pd, Fd;
function Id(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Ld(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Id(Object(n), !0).forEach(function(t) {
			Rd(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Id(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Rd(e, t, n) {
	return (t = zd(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function zd(e) {
	var t = Bd(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Bd(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function Vd() {
	return Vd = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, Vd.apply(null, arguments);
}
function Hd(e, t) {
	if (e == null) return {};
	var n, r, i = Ud(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function Ud(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function Wd(e, t) {
	return Yd(e) || Jd(e, t) || Kd(e, t) || Gd();
}
function Gd() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function Kd(e, t) {
	if (e) {
		if (typeof e == "string") return qd(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? qd(e, t) : void 0;
	}
}
function qd(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function Jd(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function Yd(e) {
	if (Array.isArray(e)) return e;
}
function Xd(e, t) {
	return t || (t = e.slice(0)), Object.freeze(Object.defineProperties(e, { raw: { value: Object.freeze(t) } }));
}
var Zd = (e, t, n, r, i) => {
	var a = Ut(n), o = Ut(r), s = Math.min(Math.abs(a) / 2, Math.abs(o) / 2), c = o >= 0 ? 1 : -1, l = a >= 0 ? 1 : -1, u = +(o >= 0 && a >= 0 || o < 0 && a < 0), d;
	if (s > 0 && Array.isArray(i)) {
		for (var f = [
			0,
			0,
			0,
			0
		], p = 0, m = 4; p < m; p++) {
			var h, g = (h = i[p]) == null ? 0 : h;
			f[p] = g > s ? s : g;
		}
		d = Wt(Ed || (Ed = Xd([
			"M",
			",",
			""
		])), e, t + c * f[0]), f[0] > 0 && (d += Wt(Dd || (Dd = Xd([
			"A ",
			",",
			",0,0,",
			",",
			",",
			""
		])), f[0], f[0], u, e + l * f[0], t)), d += Wt(Od || (Od = Xd([
			"L ",
			",",
			""
		])), e + n - l * f[1], t), f[1] > 0 && (d += Wt(kd || (kd = Xd([
			"A ",
			",",
			",0,0,",
			",\n        ",
			",",
			""
		])), f[1], f[1], u, e + n, t + c * f[1])), d += Wt(Ad || (Ad = Xd([
			"L ",
			",",
			""
		])), e + n, t + r - c * f[2]), f[2] > 0 && (d += Wt(jd || (jd = Xd([
			"A ",
			",",
			",0,0,",
			",\n        ",
			",",
			""
		])), f[2], f[2], u, e + n - l * f[2], t + r)), d += Wt(Md || (Md = Xd([
			"L ",
			",",
			""
		])), e + l * f[3], t + r), f[3] > 0 && (d += Wt(Nd || (Nd = Xd([
			"A ",
			",",
			",0,0,",
			",\n        ",
			",",
			""
		])), f[3], f[3], u, e, t + r - c * f[3])), d += "Z";
	} else if (s > 0 && i === +i && i > 0) {
		var _ = Math.min(s, i);
		d = Wt(Pd || (Pd = Xd(/* @__PURE__ */ "M .,.\n            A .,.,0,0,.,.,.\n            L .,.\n            A .,.,0,0,.,.,.\n            L .,.\n            A .,.,0,0,.,.,.\n            L .,.\n            A .,.,0,0,.,.,. Z".split("."))), e, t + c * _, _, _, u, e + l * _, t, e + n - l * _, t, _, _, u, e + n, t + c * _, e + n, t + r - c * _, _, _, u, e + n - l * _, t + r, e + l * _, t + r, _, _, u, e, t + r - c * _);
	} else d = Wt(Fd || (Fd = Xd([
		"M ",
		",",
		" h ",
		" v ",
		" h ",
		" Z"
	])), e, t, n, r, -n);
	return d;
}, Qd = {
	x: 0,
	y: 0,
	width: 0,
	height: 0,
	radius: 0,
	isAnimationActive: !1,
	isUpdateAnimationActive: !1,
	animationBegin: 0,
	animationDuration: 1500,
	animationEasing: "ease"
}, $d = (e) => {
	var t = mn(e, Qd), n = (0, C.useRef)(null), r = Wd((0, C.useState)(-1), 2), i = r[0], a = r[1];
	(0, C.useEffect)(() => {
		if (n.current && n.current.getTotalLength) try {
			var e = n.current.getTotalLength();
			e && a(e);
		} catch (e) {}
	}, []);
	var o = t.x, s = t.y, c = t.width, l = t.height, u = t.radius, d = t.className, f = t.animationEasing, p = t.animationDuration, m = t.animationBegin, h = t.isAnimationActive, g = t.isUpdateAnimationActive, _ = (0, C.useRef)(c), v = (0, C.useRef)(l), y = (0, C.useRef)(o), b = (0, C.useRef)(s), x = xd((0, C.useMemo)(() => ({
		x: o,
		y: s,
		width: c,
		height: l,
		radius: u
	}), [
		o,
		s,
		c,
		l,
		u
	]), "rectangle-");
	if (o !== +o || s !== +s || c !== +c || l !== +l || c === 0 || l === 0) return null;
	var S = he("recharts-rectangle", d);
	if (!g) {
		var w = Ce(t);
		w.radius;
		var T = Hd(w, wd);
		return /*#__PURE__*/ C.createElement("path", Vd({}, T, {
			x: Ut(o),
			y: Ut(s),
			width: Ut(c),
			height: Ut(l),
			radius: typeof u == "number" ? u : void 0,
			className: S,
			d: Zd(o, s, c, l, u)
		}));
	}
	var E = _.current, D = v.current, O = y.current, k = b.current, A = `0px ${i === -1 ? 1 : i}px`, j = `${i}px ${i}px`, M = Cd(["strokeDasharray"], p, typeof f == "string" ? f : Qd.animationEasing);
	return /*#__PURE__*/ C.createElement(bd, {
		animationId: x,
		key: x,
		canBegin: i > 0,
		duration: p,
		easing: f,
		isActive: g,
		begin: m
	}, (e) => {
		var r = Qt(E, c, e), i = Qt(D, l, e), a = Qt(O, o, e), d = Qt(k, s, e);
		n.current && (_.current = r, v.current = i, y.current = a, b.current = d);
		var f = h ? e > 0 ? {
			transition: M,
			strokeDasharray: j
		} : { strokeDasharray: A } : { strokeDasharray: j }, p = Ce(t);
		p.radius;
		var m = Hd(p, Td);
		return /*#__PURE__*/ C.createElement("path", Vd({}, m, {
			radius: typeof u == "number" ? u : void 0,
			className: S,
			d: Zd(a, d, r, i, u),
			ref: n,
			style: Ld(Ld({}, f), t.style)
		}));
	});
};
//#endregion
//#region node_modules/recharts/es6/util/PolarUtils.js
function ef(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function tf(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? ef(Object(n), !0).forEach(function(t) {
			nf(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : ef(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function nf(e, t, n) {
	return (t = rf(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function rf(e) {
	var t = af(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function af(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var of = Math.PI / 180, sf = (e) => e * 180 / Math.PI, cf = (e, t, n, r) => ({
	x: e + Math.cos(-of * r) * n,
	y: t + Math.sin(-of * r) * n
}), lf = function(e, t) {
	var n = arguments.length > 2 && arguments[2] !== void 0 ? arguments[2] : {
		top: 0,
		right: 0,
		bottom: 0,
		left: 0,
		width: 0,
		height: 0,
		brushBottom: 0
	};
	return Math.min(Math.abs(e - (n.left || 0) - (n.right || 0)), Math.abs(t - (n.top || 0) - (n.bottom || 0))) / 2;
}, uf = (e, t) => {
	var n = e.x, r = e.y, i = t.x, a = t.y;
	return Math.sqrt((n - i) ** 2 + (r - a) ** 2);
}, df = (e, t) => {
	var n = e.x, r = e.y, i = t.cx, a = t.cy, o = uf({
		x: n,
		y: r
	}, {
		x: i,
		y: a
	});
	if (o <= 0) return {
		radius: o,
		angle: 0
	};
	var s = (n - i) / o, c = Math.acos(s);
	return r > a && (c = 2 * Math.PI - c), {
		radius: o,
		angle: sf(c),
		angleInRadian: c
	};
}, ff = (e) => {
	var t = e.startAngle, n = e.endAngle, r = Math.floor(t / 360), i = Math.floor(n / 360), a = Math.min(r, i);
	return {
		startAngle: t - a * 360,
		endAngle: n - a * 360
	};
}, pf = (e, t) => {
	var n = t.startAngle, r = t.endAngle, i = Math.floor(n / 360), a = Math.floor(r / 360);
	return e + Math.min(i, a) * 360;
}, mf = (e, t) => {
	var n = e.relativeX, r = e.relativeY, i = df({
		x: n,
		y: r
	}, t), a = i.radius, o = i.angle, s = t.innerRadius, c = t.outerRadius;
	if (a < s || a > c || a === 0) return null;
	var l = ff(t), u = l.startAngle, d = l.endAngle, f = o, p;
	if (u <= d) {
		for (; f > d;) f -= 360;
		for (; f < u;) f += 360;
		p = f >= u && f <= d;
	} else {
		for (; f > u;) f -= 360;
		for (; f < d;) f += 360;
		p = f >= d && f <= u;
	}
	return p ? tf(tf({}, t), {}, {
		radius: a,
		angle: pf(f, t)
	}) : null;
};
//#endregion
//#region node_modules/recharts/es6/util/cursor/getRadialCursorPoints.js
function hf(e) {
	var t = e.cx, n = e.cy, r = e.radius, i = e.startAngle, a = e.endAngle;
	return {
		points: [cf(t, n, r, i), cf(t, n, r, a)],
		cx: t,
		cy: n,
		radius: r,
		startAngle: i,
		endAngle: a
	};
}
//#endregion
//#region node_modules/recharts/es6/shape/Sector.js
var gf, _f, vf, yf, bf, xf, Sf;
function Cf() {
	return Cf = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, Cf.apply(null, arguments);
}
function wf(e, t) {
	return t || (t = e.slice(0)), Object.freeze(Object.defineProperties(e, { raw: { value: Object.freeze(t) } }));
}
var Tf = (e, t) => Gt(t - e) * Math.min(Math.abs(t - e), 359.999), Ef = (e) => {
	var t = e.cx, n = e.cy, r = e.radius, i = e.angle, a = e.sign, o = e.isExternal, s = e.cornerRadius, c = e.cornerIsExternal, l = s * (o ? 1 : -1) + r, u = Math.asin(s / l) / of, d = c ? i : i + a * u, f = cf(t, n, l, d), p = cf(t, n, r, d), m = c ? i - a * u : i;
	return {
		center: f,
		circleTangency: p,
		lineTangency: cf(t, n, l * Math.cos(u * of), m),
		theta: u
	};
}, Df = (e) => {
	var t = e.cx, n = e.cy, r = e.innerRadius, i = e.outerRadius, a = e.startAngle, o = e.endAngle, s = Tf(a, o), c = a + s, l = cf(t, n, i, a), u = cf(t, n, i, c), d = Wt(gf || (gf = wf([
		"M ",
		",",
		"\n    A ",
		",",
		",0,\n    ",
		",",
		",\n    ",
		",",
		"\n  "
	])), l.x, l.y, i, i, +(Math.abs(s) > 180), +(a > c), u.x, u.y);
	if (r > 0) {
		var f = cf(t, n, r, a), p = cf(t, n, r, c);
		d += Wt(_f || (_f = wf([
			"L ",
			",",
			"\n            A ",
			",",
			",0,\n            ",
			",",
			",\n            ",
			",",
			" Z"
		])), p.x, p.y, r, r, +(Math.abs(s) > 180), +(a <= c), f.x, f.y);
	} else d += Wt(vf || (vf = wf([
		"L ",
		",",
		" Z"
	])), t, n);
	return d;
}, Of = (e) => {
	var t = e.cx, n = e.cy, r = e.innerRadius, i = e.outerRadius, a = e.cornerRadius, o = e.forceCornerRadius, s = e.cornerIsExternal, c = e.startAngle, l = e.endAngle, u = Gt(l - c), d = Ef({
		cx: t,
		cy: n,
		radius: i,
		angle: c,
		sign: u,
		cornerRadius: a,
		cornerIsExternal: s
	}), f = d.circleTangency, p = d.lineTangency, m = d.theta, h = Ef({
		cx: t,
		cy: n,
		radius: i,
		angle: l,
		sign: -u,
		cornerRadius: a,
		cornerIsExternal: s
	}), g = h.circleTangency, _ = h.lineTangency, v = h.theta, y = s ? Math.abs(c - l) : Math.abs(c - l) - m - v;
	if (y < 0) return o ? Wt(yf || (yf = wf([
		"M ",
		",",
		"\n        a",
		",",
		",0,0,1,",
		",0\n        a",
		",",
		",0,0,1,",
		",0\n      "
	])), p.x, p.y, a, a, a * 2, a, a, -a * 2) : Df({
		cx: t,
		cy: n,
		innerRadius: r,
		outerRadius: i,
		startAngle: c,
		endAngle: l
	});
	var b = Wt(bf || (bf = wf([
		"M ",
		",",
		"\n    A",
		",",
		",0,0,",
		",",
		",",
		"\n    A",
		",",
		",0,",
		",",
		",",
		",",
		"\n    A",
		",",
		",0,0,",
		",",
		",",
		"\n  "
	])), p.x, p.y, a, a, +(u < 0), f.x, f.y, i, i, +(y > 180), +(u < 0), g.x, g.y, a, a, +(u < 0), _.x, _.y);
	if (r > 0) {
		var x = Ef({
			cx: t,
			cy: n,
			radius: r,
			angle: c,
			sign: u,
			isExternal: !0,
			cornerRadius: a,
			cornerIsExternal: s
		}), S = x.circleTangency, C = x.lineTangency, w = x.theta, T = Ef({
			cx: t,
			cy: n,
			radius: r,
			angle: l,
			sign: -u,
			isExternal: !0,
			cornerRadius: a,
			cornerIsExternal: s
		}), E = T.circleTangency, D = T.lineTangency, O = T.theta, k = s ? Math.abs(c - l) : Math.abs(c - l) - w - O;
		if (k < 0 && a === 0) return `${b}L${t},${n}Z`;
		b += Wt(xf || (xf = wf([
			"L",
			",",
			"\n      A",
			",",
			",0,0,",
			",",
			",",
			"\n      A",
			",",
			",0,",
			",",
			",",
			",",
			"\n      A",
			",",
			",0,0,",
			",",
			",",
			"Z"
		])), D.x, D.y, a, a, +(u < 0), E.x, E.y, r, r, +(k > 180), +(u > 0), S.x, S.y, a, a, +(u < 0), C.x, C.y);
	} else b += Wt(Sf || (Sf = wf([
		"L",
		",",
		"Z"
	])), t, n);
	return b;
}, kf = {
	cx: 0,
	cy: 0,
	innerRadius: 0,
	outerRadius: 0,
	startAngle: 0,
	endAngle: 0,
	cornerRadius: 0,
	forceCornerRadius: !1,
	cornerIsExternal: !1
}, Af = (e) => {
	var t = mn(e, kf), n = t.cx, r = t.cy, i = t.innerRadius, a = t.outerRadius, o = t.cornerRadius, s = t.forceCornerRadius, c = t.cornerIsExternal, l = t.startAngle, u = t.endAngle, d = t.className;
	if (a < i || l === u) return null;
	var f = he("recharts-sector", d), p = a - i, m = Xt(o, p, 0, !0), h = m > 0 && Math.abs(l - u) < 360 ? Of({
		cx: n,
		cy: r,
		innerRadius: i,
		outerRadius: a,
		cornerRadius: Math.min(m, p / 2),
		forceCornerRadius: s,
		cornerIsExternal: c,
		startAngle: l,
		endAngle: u
	}) : Df({
		cx: n,
		cy: r,
		innerRadius: i,
		outerRadius: a,
		startAngle: l,
		endAngle: u
	});
	return /*#__PURE__*/ C.createElement("path", Cf({}, Ce(t), {
		className: f,
		d: h
	}));
};
//#endregion
//#region node_modules/recharts/es6/util/cursor/getCursorPoints.js
function jf(e, t, n) {
	if (e === "horizontal") return [{
		x: t.x,
		y: n.top
	}, {
		x: t.x,
		y: n.top + n.height
	}];
	if (e === "vertical") return [{
		x: n.left,
		y: t.y
	}, {
		x: n.left + n.width,
		y: t.y
	}];
	if (an(t)) {
		if (e === "centric") {
			var r = t.cx, i = t.cy, a = t.innerRadius, o = t.outerRadius, s = t.angle, c = cf(r, i, a, s), l = cf(r, i, o, s);
			return [{
				x: c.x,
				y: c.y
			}, {
				x: l.x,
				y: l.y
			}];
		}
		return hf(t);
	}
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/util/toNumber.mjs
function Mf(e) {
	return ei(e) ? NaN : Number(e);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/util/toFinite.mjs
function Nf(e) {
	return e ? (e = Mf(e), e === Infinity || e === -Infinity ? (e < 0 ? -1 : 1) * Number.MAX_VALUE : e === e ? e : 0) : e === 0 ? e : 0;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/math/range.mjs
function Pf(e, t, n) {
	n && typeof n != "number" && Zr(e, t, n) && (t = n = void 0), e = Nf(e), t === void 0 ? (t = e, e = 0) : t = Nf(t), n = n === void 0 ? e < t ? 1 : -1 : Nf(n);
	let r = Math.max(Math.ceil((t - e) / (n || 1)), 0), i = Array(r);
	for (let t = 0; t < r; t++) i[t] = e, e += n;
	return i;
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/dataSelectors.js
var Ff = (e) => e.chartData, If = R([Ff], (e) => {
	var t = e.chartData == null ? 0 : e.chartData.length - 1;
	return {
		chartData: e.chartData,
		computedData: e.computedData,
		dataEndIndex: t,
		dataStartIndex: 0
	};
}), Lf = (e, t, n, r) => r ? If(e) : Ff(e), Rf = (e, t, n) => n ? If(e) : Ff(e), zf = R([Lf], (e) => {
	var t = e.chartData, n = e.dataStartIndex, r = e.dataEndIndex;
	return t == null ? [] : t.slice(n, r + 1);
});
R([If], (e) => {
	var t = e.chartData, n = e.dataStartIndex, r = e.dataEndIndex;
	return t == null ? [] : t.slice(n, r + 1);
});
var Bf = R([Ff], (e) => {
	var t = e.chartData, n = e.dataStartIndex, r = e.dataEndIndex;
	return t == null ? [] : t.slice(n, r + 1);
});
//#endregion
//#region node_modules/recharts/es6/util/isDomainSpecifiedByUser.js
function Vf(e, t) {
	return Kf(e) || Gf(e, t) || Uf(e, t) || Hf();
}
function Hf() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function Uf(e, t) {
	if (e) {
		if (typeof e == "string") return Wf(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? Wf(e, t) : void 0;
	}
}
function Wf(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function Gf(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function Kf(e) {
	if (Array.isArray(e)) return e;
}
function qf(e) {
	if (Array.isArray(e) && e.length === 2) {
		var t = Vf(e, 2), n = t[0], r = t[1];
		if (U(n) && U(r)) return !0;
	}
	return !1;
}
function Jf(e, t, n) {
	return n ? e : [Math.min(e[0], t[0]), Math.max(e[1], t[1])];
}
function Yf(e, t) {
	if (t && typeof e != "function" && Array.isArray(e) && e.length === 2) {
		var n = Vf(e, 2), r = n[0], i = n[1], a, o;
		if (U(r)) a = r;
		else if (typeof r == "function") return;
		if (U(i)) o = i;
		else if (typeof i == "function") return;
		var s = [a, o];
		if (qf(s)) return s;
	}
}
function Xf(e, t, n) {
	if (!(!n && t == null)) {
		if (typeof e == "function" && t != null) try {
			var r = e(t, n);
			if (qf(r)) return Jf(r, t, n);
		} catch (e) {}
		if (Array.isArray(e) && e.length === 2) {
			var i = Vf(e, 2), a = i[0], o = i[1], s, c;
			if (a === "auto") t != null && (s = Math.min(...t));
			else if (I(a)) s = a;
			else if (typeof a == "function") try {
				t != null && (s = a(t == null ? void 0 : t[0]));
			} catch (e) {}
			else if (typeof a == "string" && Ps.test(a)) {
				var l = Ps.exec(a);
				if (l == null || l[1] == null || t == null) s = void 0;
				else {
					var u = +l[1];
					s = t[0] - u;
				}
			} else s = t == null ? void 0 : t[0];
			if (o === "auto") t != null && (c = Math.max(...t));
			else if (I(o)) c = o;
			else if (typeof o == "function") try {
				t != null && (c = o(t == null ? void 0 : t[1]));
			} catch (e) {}
			else if (typeof o == "string" && Fs.test(o)) {
				var d = Fs.exec(o);
				if (d == null || d[1] == null || t == null) c = void 0;
				else {
					var f = +d[1];
					c = t[1] + f;
				}
			} else c = t == null ? void 0 : t[1];
			var p = [s, c];
			if (qf(p)) return t == null ? p : Jf(p, t, n);
		}
	}
}
//#endregion
//#region node_modules/recharts/es6/util/scale/util/arithmetic.js
var J = /* @__PURE__ */ l((/* @__PURE__ */ o(((e, t) => {
	(function(e) {
		var n = 1e9, r = {
			precision: 20,
			rounding: 4,
			toExpNeg: -7,
			toExpPos: 21,
			LN10: "2.302585092994045684017991454684364207601101488628772976033327900967572609677352480235997205089598298341967784042286"
		}, i = !0, a = "[DecimalError] ", o = a + "Invalid argument: ", s = a + "Exponent out of range: ", c = Math.floor, l = Math.pow, u = /^(\d+(\.\d*)?|\.\d+)(e[+-]?\d+)?$/i, d, f = 1e7, p = 7, m = 9007199254740991, h = c(m / p), g = {};
		g.absoluteValue = g.abs = function() {
			var e = new this.constructor(this);
			return e.s && (e.s = 1), e;
		}, g.comparedTo = g.cmp = function(e) {
			var t, n, r, i, a = this;
			if (e = new a.constructor(e), a.s !== e.s) return a.s || -e.s;
			if (a.e !== e.e) return a.e > e.e ^ a.s < 0 ? 1 : -1;
			for (r = a.d.length, i = e.d.length, t = 0, n = r < i ? r : i; t < n; ++t) if (a.d[t] !== e.d[t]) return a.d[t] > e.d[t] ^ a.s < 0 ? 1 : -1;
			return r === i ? 0 : r > i ^ a.s < 0 ? 1 : -1;
		}, g.decimalPlaces = g.dp = function() {
			var e = this, t = e.d.length - 1, n = (t - e.e) * p;
			if (t = e.d[t], t) for (; t % 10 == 0; t /= 10) n--;
			return n < 0 ? 0 : n;
		}, g.dividedBy = g.div = function(e) {
			return b(this, new this.constructor(e));
		}, g.dividedToIntegerBy = g.idiv = function(e) {
			var t = this, n = t.constructor;
			return D(b(t, new n(e), 0, 1), n.precision);
		}, g.equals = g.eq = function(e) {
			return !this.cmp(e);
		}, g.exponent = function() {
			return S(this);
		}, g.greaterThan = g.gt = function(e) {
			return this.cmp(e) > 0;
		}, g.greaterThanOrEqualTo = g.gte = function(e) {
			return this.cmp(e) >= 0;
		}, g.isInteger = g.isint = function() {
			return this.e > this.d.length - 2;
		}, g.isNegative = g.isneg = function() {
			return this.s < 0;
		}, g.isPositive = g.ispos = function() {
			return this.s > 0;
		}, g.isZero = function() {
			return this.s === 0;
		}, g.lessThan = g.lt = function(e) {
			return this.cmp(e) < 0;
		}, g.lessThanOrEqualTo = g.lte = function(e) {
			return this.cmp(e) < 1;
		}, g.logarithm = g.log = function(e) {
			var t, n = this, r = n.constructor, o = r.precision, s = o + 5;
			if (e === void 0) e = new r(10);
			else if (e = new r(e), e.s < 1 || e.eq(d)) throw Error(a + "NaN");
			if (n.s < 1) throw Error(a + (n.s ? "NaN" : "-Infinity"));
			return n.eq(d) ? new r(0) : (i = !1, t = b(T(n, s), T(e, s), s), i = !0, D(t, o));
		}, g.minus = g.sub = function(e) {
			var t = this;
			return e = new t.constructor(e), t.s == e.s ? O(t, e) : _(t, (e.s = -e.s, e));
		}, g.modulo = g.mod = function(e) {
			var t, n = this, r = n.constructor, o = r.precision;
			if (e = new r(e), !e.s) throw Error(a + "NaN");
			return n.s ? (i = !1, t = b(n, e, 0, 1).times(e), i = !0, n.minus(t)) : D(new r(n), o);
		}, g.naturalExponential = g.exp = function() {
			return x(this);
		}, g.naturalLogarithm = g.ln = function() {
			return T(this);
		}, g.negated = g.neg = function() {
			var e = new this.constructor(this);
			return e.s = -e.s || 0, e;
		}, g.plus = g.add = function(e) {
			var t = this;
			return e = new t.constructor(e), t.s == e.s ? _(t, e) : O(t, (e.s = -e.s, e));
		}, g.precision = g.sd = function(e) {
			var t, n, r, i = this;
			if (e !== void 0 && e !== !!e && e !== 1 && e !== 0) throw Error(o + e);
			if (t = S(i) + 1, r = i.d.length - 1, n = r * p + 1, r = i.d[r], r) {
				for (; r % 10 == 0; r /= 10) n--;
				for (r = i.d[0]; r >= 10; r /= 10) n++;
			}
			return e && t > n ? t : n;
		}, g.squareRoot = g.sqrt = function() {
			var e, t, n, r, o, s, l, u = this, d = u.constructor;
			if (u.s < 1) {
				if (!u.s) return new d(0);
				throw Error(a + "NaN");
			}
			for (e = S(u), i = !1, o = Math.sqrt(+u), o == 0 || o == Infinity ? (t = y(u.d), (t.length + e) % 2 == 0 && (t += "0"), o = Math.sqrt(t), e = c((e + 1) / 2) - (e < 0 || e % 2), o == Infinity ? t = "5e" + e : (t = o.toExponential(), t = t.slice(0, t.indexOf("e") + 1) + e), r = new d(t)) : r = new d(o.toString()), n = d.precision, o = l = n + 3;;) if (s = r, r = s.plus(b(u, s, l + 2)).times(.5), y(s.d).slice(0, l) === (t = y(r.d)).slice(0, l)) {
				if (t = t.slice(l - 3, l + 1), o == l && t == "4999") {
					if (D(s, n + 1, 0), s.times(s).eq(u)) {
						r = s;
						break;
					}
				} else if (t != "9999") break;
				l += 4;
			}
			return i = !0, D(r, n);
		}, g.times = g.mul = function(e) {
			var t, n, r, a, o, s, c, l, u, d = this, p = d.constructor, m = d.d, h = (e = new p(e)).d;
			if (!d.s || !e.s) return new p(0);
			for (e.s *= d.s, n = d.e + e.e, l = m.length, u = h.length, l < u && (o = m, m = h, h = o, s = l, l = u, u = s), o = [], s = l + u, r = s; r--;) o.push(0);
			for (r = u; --r >= 0;) {
				for (t = 0, a = l + r; a > r;) c = o[a] + h[r] * m[a - r - 1] + t, o[a--] = c % f | 0, t = c / f | 0;
				o[a] = (o[a] + t) % f | 0;
			}
			for (; !o[--s];) o.pop();
			return t ? ++n : o.shift(), e.d = o, e.e = n, i ? D(e, p.precision) : e;
		}, g.toDecimalPlaces = g.todp = function(e, t) {
			var r = this, i = r.constructor;
			return r = new i(r), e === void 0 ? r : (v(e, 0, n), t === void 0 ? t = i.rounding : v(t, 0, 8), D(r, e + S(r) + 1, t));
		}, g.toExponential = function(e, t) {
			var r, i = this, a = i.constructor;
			return e === void 0 ? r = k(i, !0) : (v(e, 0, n), t === void 0 ? t = a.rounding : v(t, 0, 8), i = D(new a(i), e + 1, t), r = k(i, !0, e + 1)), r;
		}, g.toFixed = function(e, t) {
			var r, i, a = this, o = a.constructor;
			return e === void 0 ? k(a) : (v(e, 0, n), t === void 0 ? t = o.rounding : v(t, 0, 8), i = D(new o(a), e + S(a) + 1, t), r = k(i.abs(), !1, e + S(i) + 1), a.isneg() && !a.isZero() ? "-" + r : r);
		}, g.toInteger = g.toint = function() {
			var e = this, t = e.constructor;
			return D(new t(e), S(e) + 1, t.rounding);
		}, g.toNumber = function() {
			return +this;
		}, g.toPower = g.pow = function(e) {
			var t, n, r, o, s, l, u = this, f = u.constructor, h = 12, g = +(e = new f(e));
			if (!e.s) return new f(d);
			if (u = new f(u), !u.s) {
				if (e.s < 1) throw Error(a + "Infinity");
				return u;
			}
			if (u.eq(d)) return u;
			if (r = f.precision, e.eq(d)) return D(u, r);
			if (t = e.e, n = e.d.length - 1, l = t >= n, s = u.s, !l) {
				if (s < 0) throw Error(a + "NaN");
			} else if ((n = g < 0 ? -g : g) <= m) {
				for (o = new f(d), t = Math.ceil(r / p + 4), i = !1; n % 2 && (o = o.times(u), A(o.d, t)), n = c(n / 2), n !== 0;) u = u.times(u), A(u.d, t);
				return i = !0, e.s < 0 ? new f(d).div(o) : D(o, r);
			}
			return s = s < 0 && e.d[Math.max(t, n)] & 1 ? -1 : 1, u.s = 1, i = !1, o = e.times(T(u, r + h)), i = !0, o = x(o), o.s = s, o;
		}, g.toPrecision = function(e, t) {
			var r, i, a = this, o = a.constructor;
			return e === void 0 ? (r = S(a), i = k(a, r <= o.toExpNeg || r >= o.toExpPos)) : (v(e, 1, n), t === void 0 ? t = o.rounding : v(t, 0, 8), a = D(new o(a), e, t), r = S(a), i = k(a, e <= r || r <= o.toExpNeg, e)), i;
		}, g.toSignificantDigits = g.tosd = function(e, t) {
			var r = this, i = r.constructor;
			return e === void 0 ? (e = i.precision, t = i.rounding) : (v(e, 1, n), t === void 0 ? t = i.rounding : v(t, 0, 8)), D(new i(r), e, t);
		}, g.toString = g.valueOf = g.val = g.toJSON = function() {
			var e = this, t = S(e), n = e.constructor;
			return k(e, t <= n.toExpNeg || t >= n.toExpPos);
		};
		function _(e, t) {
			var n, r, a, o, s, c, l, u, d = e.constructor, m = d.precision;
			if (!e.s || !t.s) return t.s || (t = new d(e)), i ? D(t, m) : t;
			if (l = e.d, u = t.d, s = e.e, a = t.e, l = l.slice(), o = s - a, o) {
				for (o < 0 ? (r = l, o = -o, c = u.length) : (r = u, a = s, c = l.length), s = Math.ceil(m / p), c = s > c ? s + 1 : c + 1, o > c && (o = c, r.length = 1), r.reverse(); o--;) r.push(0);
				r.reverse();
			}
			for (c = l.length, o = u.length, c - o < 0 && (o = c, r = u, u = l, l = r), n = 0; o;) n = (l[--o] = l[o] + u[o] + n) / f | 0, l[o] %= f;
			for (n && (l.unshift(n), ++a), c = l.length; l[--c] == 0;) l.pop();
			return t.d = l, t.e = a, i ? D(t, m) : t;
		}
		function v(e, t, n) {
			if (e !== ~~e || e < t || e > n) throw Error(o + e);
		}
		function y(e) {
			var t, n, r, i = e.length - 1, a = "", o = e[0];
			if (i > 0) {
				for (a += o, t = 1; t < i; t++) r = e[t] + "", n = p - r.length, n && (a += w(n)), a += r;
				o = e[t], r = o + "", n = p - r.length, n && (a += w(n));
			} else if (o === 0) return "0";
			for (; o % 10 == 0;) o /= 10;
			return a + o;
		}
		var b = (function() {
			function e(e, t) {
				var n, r = 0, i = e.length;
				for (e = e.slice(); i--;) n = e[i] * t + r, e[i] = n % f | 0, r = n / f | 0;
				return r && e.unshift(r), e;
			}
			function t(e, t, n, r) {
				var i, a;
				if (n != r) a = n > r ? 1 : -1;
				else for (i = a = 0; i < n; i++) if (e[i] != t[i]) {
					a = e[i] > t[i] ? 1 : -1;
					break;
				}
				return a;
			}
			function n(e, t, n) {
				for (var r = 0; n--;) e[n] -= r, r = +(e[n] < t[n]), e[n] = r * f + e[n] - t[n];
				for (; !e[0] && e.length > 1;) e.shift();
			}
			return function(r, i, o, s) {
				var c, l, u, d, m, h, g, _, v, y, b, x, C, w, T, E, O, k, A = r.constructor, j = r.s == i.s ? 1 : -1, M = r.d, N = i.d;
				if (!r.s) return new A(r);
				if (!i.s) throw Error(a + "Division by zero");
				for (l = r.e - i.e, O = N.length, T = M.length, g = new A(j), _ = g.d = [], u = 0; N[u] == (M[u] || 0);) ++u;
				if (N[u] > (M[u] || 0) && --l, x = o == null ? o = A.precision : s ? o + (S(r) - S(i)) + 1 : o, x < 0) return new A(0);
				if (x = x / p + 2 | 0, u = 0, O == 1) for (d = 0, N = N[0], x++; (u < T || d) && x--; u++) C = d * f + (M[u] || 0), _[u] = C / N | 0, d = C % N | 0;
				else {
					for (d = f / (N[0] + 1) | 0, d > 1 && (N = e(N, d), M = e(M, d), O = N.length, T = M.length), w = O, v = M.slice(0, O), y = v.length; y < O;) v[y++] = 0;
					k = N.slice(), k.unshift(0), E = N[0], N[1] >= f / 2 && ++E;
					do
						d = 0, c = t(N, v, O, y), c < 0 ? (b = v[0], O != y && (b = b * f + (v[1] || 0)), d = b / E | 0, d > 1 ? (d >= f && (d = f - 1), m = e(N, d), h = m.length, y = v.length, c = t(m, v, h, y), c == 1 && (d--, n(m, O < h ? k : N, h))) : (d == 0 && (c = d = 1), m = N.slice()), h = m.length, h < y && m.unshift(0), n(v, m, y), c == -1 && (y = v.length, c = t(N, v, O, y), c < 1 && (d++, n(v, O < y ? k : N, y))), y = v.length) : c === 0 && (d++, v = [0]), _[u++] = d, c && v[0] ? v[y++] = M[w] || 0 : (v = [M[w]], y = 1);
					while ((w++ < T || v[0] !== void 0) && x--);
				}
				return _[0] || _.shift(), g.e = l, D(g, s ? o + S(g) + 1 : o);
			};
		})();
		function x(e, t) {
			var n, r, a, o, c, u, f = 0, p = 0, m = e.constructor, h = m.precision;
			if (S(e) > 16) throw Error(s + S(e));
			if (!e.s) return new m(d);
			for (t == null ? (i = !1, u = h) : u = t, c = new m(.03125); e.abs().gte(.1);) e = e.times(c), p += 5;
			for (r = Math.log(l(2, p)) / Math.LN10 * 2 + 5 | 0, u += r, n = a = o = new m(d), m.precision = u;;) {
				if (a = D(a.times(e), u), n = n.times(++f), c = o.plus(b(a, n, u)), y(c.d).slice(0, u) === y(o.d).slice(0, u)) {
					for (; p--;) o = D(o.times(o), u);
					return m.precision = h, t == null ? (i = !0, D(o, h)) : o;
				}
				o = c;
			}
		}
		function S(e) {
			for (var t = e.e * p, n = e.d[0]; n >= 10; n /= 10) t++;
			return t;
		}
		function C(e, t, n) {
			if (t > e.LN10.sd()) throw i = !0, n && (e.precision = n), Error(a + "LN10 precision limit exceeded");
			return D(new e(e.LN10), t);
		}
		function w(e) {
			for (var t = ""; e--;) t += "0";
			return t;
		}
		function T(e, t) {
			var n, r, o, s, c, l, u, f, p, m = 1, h = 10, g = e, _ = g.d, v = g.constructor, x = v.precision;
			if (g.s < 1) throw Error(a + (g.s ? "NaN" : "-Infinity"));
			if (g.eq(d)) return new v(0);
			if (t == null ? (i = !1, f = x) : f = t, g.eq(10)) return t == null && (i = !0), C(v, f);
			if (f += h, v.precision = f, n = y(_), r = n.charAt(0), s = S(g), Math.abs(s) < 0x5543df729c000) {
				for (; r < 7 && r != 1 || r == 1 && n.charAt(1) > 3;) g = g.times(e), n = y(g.d), r = n.charAt(0), m++;
				s = S(g), r > 1 ? (g = new v("0." + n), s++) : g = new v(r + "." + n.slice(1));
			} else return u = C(v, f + 2, x).times(s + ""), g = T(new v(r + "." + n.slice(1)), f - h).plus(u), v.precision = x, t == null ? (i = !0, D(g, x)) : g;
			for (l = c = g = b(g.minus(d), g.plus(d), f), p = D(g.times(g), f), o = 3;;) {
				if (c = D(c.times(p), f), u = l.plus(b(c, new v(o), f)), y(u.d).slice(0, f) === y(l.d).slice(0, f)) return l = l.times(2), s !== 0 && (l = l.plus(C(v, f + 2, x).times(s + ""))), l = b(l, new v(m), f), v.precision = x, t == null ? (i = !0, D(l, x)) : l;
				l = u, o += 2;
			}
		}
		function E(e, t) {
			var n, r, a;
			for ((n = t.indexOf(".")) > -1 && (t = t.replace(".", "")), (r = t.search(/e/i)) > 0 ? (n < 0 && (n = r), n += +t.slice(r + 1), t = t.substring(0, r)) : n < 0 && (n = t.length), r = 0; t.charCodeAt(r) === 48;) ++r;
			for (a = t.length; t.charCodeAt(a - 1) === 48;) --a;
			if (t = t.slice(r, a), t) {
				if (a -= r, n = n - r - 1, e.e = c(n / p), e.d = [], r = (n + 1) % p, n < 0 && (r += p), r < a) {
					for (r && e.d.push(+t.slice(0, r)), a -= p; r < a;) e.d.push(+t.slice(r, r += p));
					t = t.slice(r), r = p - t.length;
				} else r -= a;
				for (; r--;) t += "0";
				if (e.d.push(+t), i && (e.e > h || e.e < -h)) throw Error(s + n);
			} else e.s = 0, e.e = 0, e.d = [0];
			return e;
		}
		function D(e, t, n) {
			var r, a, o, u, d, m, g, _, v = e.d;
			for (u = 1, o = v[0]; o >= 10; o /= 10) u++;
			if (r = t - u, r < 0) r += p, a = t, g = v[_ = 0];
			else {
				if (_ = Math.ceil((r + 1) / p), o = v.length, _ >= o) return e;
				for (g = o = v[_], u = 1; o >= 10; o /= 10) u++;
				r %= p, a = r - p + u;
			}
			if (n !== void 0 && (o = l(10, u - a - 1), d = g / o % 10 | 0, m = t < 0 || v[_ + 1] !== void 0 || g % o, m = n < 4 ? (d || m) && (n == 0 || n == (e.s < 0 ? 3 : 2)) : d > 5 || d == 5 && (n == 4 || m || n == 6 && (r > 0 ? a > 0 ? g / l(10, u - a) : 0 : v[_ - 1]) % 10 & 1 || n == (e.s < 0 ? 8 : 7))), t < 1 || !v[0]) return m ? (o = S(e), v.length = 1, t = t - o - 1, v[0] = l(10, (p - t % p) % p), e.e = c(-t / p) || 0) : (v.length = 1, v[0] = e.e = e.s = 0), e;
			if (r == 0 ? (v.length = _, o = 1, _--) : (v.length = _ + 1, o = l(10, p - r), v[_] = a > 0 ? (g / l(10, u - a) % l(10, a) | 0) * o : 0), m) for (;;) if (_ == 0) {
				(v[0] += o) == f && (v[0] = 1, ++e.e);
				break;
			} else {
				if (v[_] += o, v[_] != f) break;
				v[_--] = 0, o = 1;
			}
			for (r = v.length; v[--r] === 0;) v.pop();
			if (i && (e.e > h || e.e < -h)) throw Error(s + S(e));
			return e;
		}
		function O(e, t) {
			var n, r, a, o, s, c, l, u, d, m, h = e.constructor, g = h.precision;
			if (!e.s || !t.s) return t.s ? t.s = -t.s : t = new h(e), i ? D(t, g) : t;
			if (l = e.d, m = t.d, r = t.e, u = e.e, l = l.slice(), s = u - r, s) {
				for (d = s < 0, d ? (n = l, s = -s, c = m.length) : (n = m, r = u, c = l.length), a = Math.max(Math.ceil(g / p), c) + 2, s > a && (s = a, n.length = 1), n.reverse(), a = s; a--;) n.push(0);
				n.reverse();
			} else {
				for (a = l.length, c = m.length, d = a < c, d && (c = a), a = 0; a < c; a++) if (l[a] != m[a]) {
					d = l[a] < m[a];
					break;
				}
				s = 0;
			}
			for (d && (n = l, l = m, m = n, t.s = -t.s), c = l.length, a = m.length - c; a > 0; --a) l[c++] = 0;
			for (a = m.length; a > s;) {
				if (l[--a] < m[a]) {
					for (o = a; o && l[--o] === 0;) l[o] = f - 1;
					--l[o], l[a] += f;
				}
				l[a] -= m[a];
			}
			for (; l[--c] === 0;) l.pop();
			for (; l[0] === 0; l.shift()) --r;
			return l[0] ? (t.d = l, t.e = r, i ? D(t, g) : t) : new h(0);
		}
		function k(e, t, n) {
			var r, i = S(e), a = y(e.d), o = a.length;
			return t ? (n && (r = n - o) > 0 ? a = a.charAt(0) + "." + a.slice(1) + w(r) : o > 1 && (a = a.charAt(0) + "." + a.slice(1)), a = a + (i < 0 ? "e" : "e+") + i) : i < 0 ? (a = "0." + w(-i - 1) + a, n && (r = n - o) > 0 && (a += w(r))) : i >= o ? (a += w(i + 1 - o), n && (r = n - i - 1) > 0 && (a = a + "." + w(r))) : ((r = i + 1) < o && (a = a.slice(0, r) + "." + a.slice(r)), n && (r = n - o) > 0 && (i + 1 === o && (a += "."), a += w(r))), e.s < 0 ? "-" + a : a;
		}
		function A(e, t) {
			if (e.length > t) return e.length = t, !0;
		}
		function j(e) {
			var t, n, r;
			function i(e) {
				var t = this;
				if (!(t instanceof i)) return new i(e);
				if (t.constructor = i, e instanceof i) {
					t.s = e.s, t.e = e.e, t.d = (e = e.d) ? e.slice() : e;
					return;
				}
				if (typeof e == "number") {
					if (e * 0 != 0) throw Error(o + e);
					if (e > 0) t.s = 1;
					else if (e < 0) e = -e, t.s = -1;
					else {
						t.s = 0, t.e = 0, t.d = [0];
						return;
					}
					if (e === ~~e && e < 1e7) {
						t.e = 0, t.d = [e];
						return;
					}
					return E(t, e.toString());
				} else if (typeof e != "string") throw Error(o + e);
				if (e.charCodeAt(0) === 45 ? (e = e.slice(1), t.s = -1) : t.s = 1, u.test(e)) E(t, e);
				else throw Error(o + e);
			}
			if (i.prototype = g, i.ROUND_UP = 0, i.ROUND_DOWN = 1, i.ROUND_CEIL = 2, i.ROUND_FLOOR = 3, i.ROUND_HALF_UP = 4, i.ROUND_HALF_DOWN = 5, i.ROUND_HALF_EVEN = 6, i.ROUND_HALF_CEIL = 7, i.ROUND_HALF_FLOOR = 8, i.clone = j, i.config = i.set = M, e === void 0 && (e = {}), e) for (r = [
				"precision",
				"rounding",
				"toExpNeg",
				"toExpPos",
				"LN10"
			], t = 0; t < r.length;) e.hasOwnProperty(n = r[t++]) || (e[n] = this[n]);
			return i.config(e), i;
		}
		function M(e) {
			if (!e || typeof e != "object") throw Error(a + "Object expected");
			var t, r, i, s = [
				"precision",
				1,
				n,
				"rounding",
				0,
				8,
				"toExpNeg",
				-Infinity,
				0,
				"toExpPos",
				0,
				Infinity
			];
			for (t = 0; t < s.length; t += 3) if ((i = e[r = s[t]]) !== void 0) if (c(i) === i && i >= s[t + 1] && i <= s[t + 2]) this[r] = i;
			else throw Error(o + r + ": " + i);
			if ((i = e[r = "LN10"]) !== void 0) if (i == Math.LN10) this[r] = new this(i);
			else throw Error(o + r + ": " + i);
			return this;
		}
		r = j(r), r.default = r.Decimal = r, d = new r(1), typeof define == "function" && define.amd ? define(function() {
			return r;
		}) : t !== void 0 && t.exports ? t.exports = r : (e || (e = typeof self < "u" && self && self.self == self ? self : Function("return this")()), e.Decimal = r);
	})(e);
})))());
function Zf(e) {
	return e === 0 ? 1 : Math.floor(new J.default(e).abs().log(10).toNumber()) + 1;
}
function Qf(e, t, n) {
	for (var r = new J.default(e), i = 0, a = []; r.lt(t) && i < 1e5;) a.push(r.toNumber()), r = r.add(n), i++;
	return a;
}
//#endregion
//#region node_modules/recharts/es6/util/scale/getNiceTickValues.js
function $f(e, t) {
	return ip(e) || rp(e, t) || tp(e, t) || ep();
}
function ep() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function tp(e, t) {
	if (e) {
		if (typeof e == "string") return np(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? np(e, t) : void 0;
	}
}
function np(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function rp(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function ip(e) {
	if (Array.isArray(e)) return e;
}
var ap = (e) => {
	var t = $f(e, 2), n = t[0], r = t[1], i = n, a = r;
	return n > r && (i = r, a = n), [i, a];
}, op = (e, t, n) => {
	if (e.lte(0)) return new J.default(0);
	var r = Zf(e.toNumber()), i = new J.default(10).pow(r), a = e.div(i), o = r === 1 ? .1 : .05, s = new J.default(Math.ceil(a.div(o).toNumber())).add(n).mul(o).mul(i);
	return t ? new J.default(s.toNumber()) : new J.default(Math.ceil(s.toNumber()));
}, sp = (e, t, n) => {
	var r;
	if (e.lte(0)) return new J.default(0);
	var i = [
		1,
		2,
		2.5,
		5
	], a = e.toNumber(), o = Math.floor(new J.default(a).abs().log(10).toNumber()), s = new J.default(10).pow(o), c = e.div(s).toNumber(), l = i.findIndex((e) => e >= c - 1e-10);
	if (l === -1 && (s = s.mul(10), l = 0), l += n, l >= i.length) {
		var u = Math.floor(l / i.length);
		l %= i.length, s = s.mul(new J.default(10).pow(u));
	}
	var d = new J.default((r = i[l]) == null ? 1 : r).mul(s);
	return t ? d : new J.default(Math.ceil(d.toNumber()));
}, cp = (e, t, n) => {
	var r = new J.default(1), i = new J.default(e);
	if (!i.isint() && n) {
		var a = Math.abs(e);
		a < 1 ? (r = new J.default(10).pow(Zf(e) - 1), i = new J.default(Math.floor(i.div(r).toNumber())).mul(r)) : a > 1 && (i = new J.default(Math.floor(e)));
	} else e === 0 ? i = new J.default(Math.floor((t - 1) / 2)) : n || (i = new J.default(Math.floor(e)));
	for (var o = Math.floor((t - 1) / 2), s = [], c = 0; c < t; c++) s.push(i.add(new J.default(c - o).mul(r)).toNumber());
	return s;
}, lp = function(e, t, n, r) {
	var i = arguments.length > 4 && arguments[4] !== void 0 ? arguments[4] : 0, a = arguments.length > 5 && arguments[5] !== void 0 ? arguments[5] : op;
	if (!Number.isFinite((t - e) / (n - 1))) return {
		step: new J.default(0),
		tickMin: new J.default(0),
		tickMax: new J.default(0)
	};
	var o = a(new J.default(t).sub(e).div(n - 1), r, i), s;
	e <= 0 && t >= 0 ? s = new J.default(0) : (s = new J.default(e).add(t).div(2), s = s.sub(new J.default(s).mod(o)));
	var c = Math.ceil(s.sub(e).div(o).toNumber()), l = Math.ceil(new J.default(t).sub(s).div(o).toNumber()), u = c + l + 1;
	return u > n ? lp(e, t, n, r, i + 1, a) : (u < n && (l = t > 0 ? l + (n - u) : l, c = t > 0 ? c : c + (n - u)), {
		step: o,
		tickMin: s.sub(new J.default(c).mul(o)),
		tickMax: s.add(new J.default(l).mul(o))
	});
}, up = function(e) {
	var t = $f(e, 2), n = t[0], r = t[1], i = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : 6, a = arguments.length > 2 && arguments[2] !== void 0 ? arguments[2] : !0, o = arguments.length > 3 && arguments[3] !== void 0 ? arguments[3] : "auto", s = Math.max(i, 2), c = $f(ap([n, r]), 2), l = c[0], u = c[1];
	if (l === -Infinity || u === Infinity) {
		var d = u === Infinity ? [l, ...Array(i - 1).fill(Infinity)] : [...Array(i - 1).fill(-Infinity), u];
		return n > r ? d.reverse() : d;
	}
	if (l === u) return cp(l, i, a);
	var f = lp(l, u, s, a, 0, o === "snap125" ? sp : op), p = f.step, m = f.tickMin, h = f.tickMax, g = Qf(m, h.add(new J.default(.1).mul(p)), p);
	return n > r ? g.reverse() : g;
}, dp = function(e, t) {
	var n = $f(e, 2), r = n[0], i = n[1], a = arguments.length > 2 && arguments[2] !== void 0 ? arguments[2] : !0, o = arguments.length > 3 && arguments[3] !== void 0 ? arguments[3] : "auto", s = $f(ap([r, i]), 2), c = s[0], l = s[1];
	if (c === -Infinity || l === Infinity) return [r, i];
	if (c === l) return [c];
	var u = o === "snap125" ? sp : op, d = Math.max(t, 2), f = u(new J.default(l).sub(c).div(d - 1), a, 0), p = [...Qf(new J.default(c), new J.default(l), f), l];
	if (a === !1) {
		p = p.map((e) => Math.round(e));
		var m = p.length - 1;
		m > 0 && p[m] === p[m - 1] && (p = p.slice(0, m));
	}
	return r > i ? p.reverse() : p;
}, fp = (e) => e.rootProps.maxBarSize, pp = (e) => e.rootProps.barGap, mp = (e) => e.rootProps.barCategoryGap, hp = (e) => e.rootProps.barSize, gp = (e) => e.rootProps.stackOffset, _p = (e) => e.rootProps.reverseStackOrder, vp = (e) => e.options.chartName, yp = (e) => e.rootProps.syncId, bp = (e) => e.rootProps.syncMethod, xp = (e) => e.options.eventEmitter, Sp = {
	grid: -100,
	barBackground: -50,
	area: 100,
	cursorRectangle: 200,
	bar: 300,
	line: 400,
	axis: 500,
	scatter: 600,
	activeBar: 1e3,
	cursorLine: 1100,
	activeDot: 1200,
	label: 2e3
}, Cp = {
	allowDecimals: !1,
	allowDuplicatedCategory: !0,
	allowDataOverflow: !1,
	angle: 0,
	angleAxisId: 0,
	axisLine: !0,
	axisLineType: "polygon",
	cx: 0,
	cy: 0,
	hide: !1,
	includeHidden: !1,
	label: !1,
	niceTicks: "auto",
	orientation: "outer",
	reversed: !1,
	scale: "auto",
	tick: !0,
	tickLine: !0,
	tickSize: 8,
	type: "auto",
	zIndex: Sp.axis
}, wp = {
	allowDataOverflow: !1,
	allowDecimals: !1,
	allowDuplicatedCategory: !0,
	angle: 0,
	axisLine: !0,
	includeHidden: !1,
	hide: !1,
	niceTicks: "auto",
	label: !1,
	orientation: "right",
	radiusAxisId: 0,
	reversed: !1,
	scale: "auto",
	stroke: "#ccc",
	tick: !0,
	tickCount: 5,
	tickLine: !0,
	type: "auto",
	zIndex: Sp.axis
}, Tp = (e, t) => {
	if (!(!e || !t)) return e != null && e.reversed ? [t[1], t[0]] : t;
};
//#endregion
//#region node_modules/recharts/es6/util/getAxisTypeBasedOnLayout.js
function Ep(e, t, n) {
	if (n !== "auto") return n;
	if (e != null) return ws(e, t) ? "category" : "number";
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/polarAxisSelectors.js
function Dp(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Op(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Dp(Object(n), !0).forEach(function(t) {
			kp(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Dp(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function kp(e, t, n) {
	return (t = Ap(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function Ap(e) {
	var t = jp(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function jp(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var Mp = {
	allowDataOverflow: Cp.allowDataOverflow,
	allowDecimals: Cp.allowDecimals,
	allowDuplicatedCategory: !1,
	dataKey: void 0,
	domain: void 0,
	id: Cp.angleAxisId,
	includeHidden: !1,
	name: void 0,
	reversed: Cp.reversed,
	scale: Cp.scale,
	tick: Cp.tick,
	tickCount: void 0,
	ticks: void 0,
	type: Cp.type,
	unit: void 0,
	niceTicks: "auto"
}, Np = {
	allowDataOverflow: wp.allowDataOverflow,
	allowDecimals: wp.allowDecimals,
	allowDuplicatedCategory: wp.allowDuplicatedCategory,
	dataKey: void 0,
	domain: void 0,
	id: wp.radiusAxisId,
	includeHidden: wp.includeHidden,
	name: void 0,
	reversed: wp.reversed,
	scale: wp.scale,
	tick: wp.tick,
	tickCount: wp.tickCount,
	ticks: void 0,
	type: wp.type,
	unit: void 0,
	niceTicks: "auto"
}, Pp = R([(e, t) => {
	if (t != null) return e.polarAxis.angleAxis[t];
}, Xc], (e, t) => {
	var n;
	if (e != null) return e;
	var r = (n = Ep(t, "angleAxis", Mp.type)) == null ? "category" : n;
	return Op(Op({}, Mp), {}, { type: r });
}), Fp = R([(e, t) => e.polarAxis.radiusAxis[t], Xc], (e, t) => {
	var n;
	if (e != null) return e;
	var r = (n = Ep(t, "radiusAxis", Np.type)) == null ? "category" : n;
	return Op(Op({}, Np), {}, { type: r });
}), Ip = (e) => e.polarOptions, Lp = R([
	Vs,
	Hs,
	ic
], lf), Rp = R([Ip, Lp], (e, t) => {
	if (e != null) return Xt(e.innerRadius, t, 0);
}), zp = R([Ip, Lp], (e, t) => {
	if (e != null) return Xt(e.outerRadius, t, t * .8);
}), Bp = R([Ip], (e) => e == null ? [0, 0] : [e.startAngle, e.endAngle]);
R([Pp, Bp], Tp);
var Vp = R([
	Lp,
	Rp,
	zp
], (e, t, n) => {
	if (!(e == null || t == null || n == null)) return [t, n];
});
R([Fp, Vp], Tp);
var Hp = R([
	q,
	Ip,
	Rp,
	zp,
	Vs,
	Hs
], (e, t, n, r, i, a) => {
	if (!(e !== "centric" && e !== "radial" || t == null || n == null || r == null)) {
		var o = t.cx, s = t.cy, c = t.startAngle, l = t.endAngle;
		return {
			cx: Xt(o, i, i / 2),
			cy: Xt(s, a, a / 2),
			innerRadius: n,
			outerRadius: r,
			startAngle: c,
			endAngle: l,
			clockWise: !1
		};
	}
}), Up = (e, t) => t, Wp = (e, t, n) => n;
//#endregion
//#region node_modules/recharts/es6/util/stacks/getStackSeriesIdentifier.js
function Gp(e) {
	return e == null ? void 0 : e.id;
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineDisplayedStackedData.js
function Kp(e, t, n) {
	var r = t.chartData, i = r === void 0 ? [] : r, a = n.allowDuplicatedCategory, o = n.dataKey, s = /* @__PURE__ */ new Map();
	return e.forEach((e) => {
		var t, n = (t = e.data) == null ? i : t;
		if (!(n == null || n.length === 0)) {
			var r = Gp(e);
			n.forEach((t, n) => {
				var i = o == null || a ? n : String(W(t, o, null)), c = W(t, e.dataKey, 0), l = s.has(i) ? s.get(i) : {};
				Object.assign(l, { [r]: c }), s.set(i, l);
			});
		}
	}), Array.from(s.values());
}
//#endregion
//#region node_modules/recharts/es6/state/types/StackedGraphicalItem.js
function qp(e) {
	return "stackId" in e && e.stackId != null && e.dataKey != null;
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/numberDomainEqualityCheck.js
var Jp = (e, t) => e === t ? !0 : e == null || t == null ? !1 : e[0] === t[0] && e[1] === t[1];
//#endregion
//#region node_modules/recharts/es6/state/selectors/arrayEqualityCheck.js
function Yp(e, t) {
	return Array.isArray(e) && Array.isArray(t) && e.length === 0 && t.length === 0 ? !0 : e === t;
}
function Xp(e, t) {
	if (e.length === t.length) {
		for (var n = 0; n < e.length; n++) if (e[n] !== t[n]) return !1;
		return !0;
	}
	return !1;
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/selectTooltipAxisType.js
var Zp = (e) => {
	var t = q(e);
	return t === "horizontal" ? "xAxis" : t === "vertical" ? "yAxis" : t === "centric" ? "angleAxis" : "radiusAxis";
}, Qp = (e) => e.tooltip.settings.axisId;
//#endregion
//#region node_modules/recharts/es6/util/scale/RechartsScale.js
function $p(e) {
	if (e != null) {
		var t = e.ticks, n = e.bandwidth, r = e.range(), i = [Math.min(...r), Math.max(...r)];
		return {
			domain: () => e.domain(),
			range: function(e) {
				function t() {
					return e.apply(this, arguments);
				}
				return t.toString = function() {
					return e.toString();
				}, t;
			}(() => i),
			rangeMin: () => i[0],
			rangeMax: () => i[1],
			isInRange(e) {
				var t = i[0], n = i[1];
				return t <= n ? e >= t && e <= n : e >= n && e <= t;
			},
			bandwidth: n ? () => n.call(e) : void 0,
			ticks: t ? (n) => t.call(e, n) : void 0,
			map: (t, n) => {
				var r = e(t);
				if (r != null) {
					if (e.bandwidth && n != null && n.position) {
						var i = e.bandwidth();
						switch (n.position) {
							case "middle":
								r += i / 2;
								break;
							case "end":
								r += i;
								break;
							default: break;
						}
					}
					return r;
				}
			}
		};
	}
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineCheckedDomain.js
var em = (e, t) => {
	if (t != null) switch (e) {
		case "linear":
			if (!qf(t)) {
				for (var n, r, i = 0; i < t.length; i++) {
					var a = t[i];
					U(a) && ((n === void 0 || a < n) && (n = a), (r === void 0 || a > r) && (r = a));
				}
				return n !== void 0 && r !== void 0 ? [n, r] : void 0;
			}
			return t;
		default: return t;
	}
};
//#endregion
//#region node_modules/d3-array/src/ascending.js
function tm(e, t) {
	return e == null || t == null ? NaN : e < t ? -1 : e > t ? 1 : e >= t ? 0 : NaN;
}
//#endregion
//#region node_modules/d3-array/src/descending.js
function nm(e, t) {
	return e == null || t == null ? NaN : t < e ? -1 : t > e ? 1 : t >= e ? 0 : NaN;
}
//#endregion
//#region node_modules/d3-array/src/bisector.js
function rm(e) {
	let t, n, r;
	e.length === 2 ? (t = e === tm || e === nm ? e : im, n = e, r = e) : (t = tm, n = (t, n) => tm(e(t), n), r = (t, n) => e(t) - n);
	function i(e, r, i = 0, a = e.length) {
		if (i < a) {
			if (t(r, r) !== 0) return a;
			do {
				let t = i + a >>> 1;
				n(e[t], r) < 0 ? i = t + 1 : a = t;
			} while (i < a);
		}
		return i;
	}
	function a(e, r, i = 0, a = e.length) {
		if (i < a) {
			if (t(r, r) !== 0) return a;
			do {
				let t = i + a >>> 1;
				n(e[t], r) <= 0 ? i = t + 1 : a = t;
			} while (i < a);
		}
		return i;
	}
	function o(e, t, n = 0, a = e.length) {
		let o = i(e, t, n, a - 1);
		return o > n && r(e[o - 1], t) > -r(e[o], t) ? o - 1 : o;
	}
	return {
		left: i,
		center: o,
		right: a
	};
}
function im() {
	return 0;
}
//#endregion
//#region node_modules/d3-array/src/number.js
function am(e) {
	return e === null ? NaN : +e;
}
function* om(e, t) {
	if (t === void 0) for (let t of e) t != null && (t = +t) >= t && (yield t);
	else {
		let n = -1;
		for (let r of e) (r = t(r, ++n, e)) != null && (r = +r) >= r && (yield r);
	}
}
//#endregion
//#region node_modules/d3-array/src/bisect.js
var sm = rm(tm), cm = sm.right;
sm.left, rm(am).center;
//#endregion
//#region node_modules/internmap/src/index.js
var lm = class extends Map {
	constructor(e, t = pm) {
		if (super(), Object.defineProperties(this, {
			_intern: { value: /* @__PURE__ */ new Map() },
			_key: { value: t }
		}), e != null) for (let [t, n] of e) this.set(t, n);
	}
	get(e) {
		return super.get(um(this, e));
	}
	has(e) {
		return super.has(um(this, e));
	}
	set(e, t) {
		return super.set(dm(this, e), t);
	}
	delete(e) {
		return super.delete(fm(this, e));
	}
};
function um({ _intern: e, _key: t }, n) {
	let r = t(n);
	return e.has(r) ? e.get(r) : n;
}
function dm({ _intern: e, _key: t }, n) {
	let r = t(n);
	return e.has(r) ? e.get(r) : (e.set(r, n), n);
}
function fm({ _intern: e, _key: t }, n) {
	let r = t(n);
	return e.has(r) && (n = e.get(r), e.delete(r)), n;
}
function pm(e) {
	return typeof e == "object" && e ? e.valueOf() : e;
}
//#endregion
//#region node_modules/d3-array/src/sort.js
function mm(e = tm) {
	if (e === tm) return hm;
	if (typeof e != "function") throw TypeError("compare is not a function");
	return (t, n) => {
		let r = e(t, n);
		return r || r === 0 ? r : (e(n, n) === 0) - (e(t, t) === 0);
	};
}
function hm(e, t) {
	return (e == null || !(e >= e)) - (t == null || !(t >= t)) || (e < t ? -1 : +(e > t));
}
//#endregion
//#region node_modules/d3-array/src/ticks.js
var gm = Math.sqrt(50), _m = Math.sqrt(10), vm = Math.sqrt(2);
function ym(e, t, n) {
	let r = (t - e) / Math.max(0, n), i = Math.floor(Math.log10(r)), a = r / 10 ** i, o = a >= gm ? 10 : a >= _m ? 5 : a >= vm ? 2 : 1, s, c, l;
	return i < 0 ? (l = 10 ** -i / o, s = Math.round(e * l), c = Math.round(t * l), s / l < e && ++s, c / l > t && --c, l = -l) : (l = 10 ** i * o, s = Math.round(e / l), c = Math.round(t / l), s * l < e && ++s, c * l > t && --c), c < s && .5 <= n && n < 2 ? ym(e, t, n * 2) : [
		s,
		c,
		l
	];
}
function bm(e, t, n) {
	if (t = +t, e = +e, n = +n, !(n > 0)) return [];
	if (e === t) return [e];
	let r = t < e, [i, a, o] = r ? ym(t, e, n) : ym(e, t, n);
	if (!(a >= i)) return [];
	let s = a - i + 1, c = Array(s);
	if (r) if (o < 0) for (let e = 0; e < s; ++e) c[e] = (a - e) / -o;
	else for (let e = 0; e < s; ++e) c[e] = (a - e) * o;
	else if (o < 0) for (let e = 0; e < s; ++e) c[e] = (i + e) / -o;
	else for (let e = 0; e < s; ++e) c[e] = (i + e) * o;
	return c;
}
function xm(e, t, n) {
	return t = +t, e = +e, n = +n, ym(e, t, n)[2];
}
function Sm(e, t, n) {
	t = +t, e = +e, n = +n;
	let r = t < e, i = r ? xm(t, e, n) : xm(e, t, n);
	return (r ? -1 : 1) * (i < 0 ? 1 / -i : i);
}
//#endregion
//#region node_modules/d3-array/src/max.js
function Cm(e, t) {
	let n;
	if (t === void 0) for (let t of e) t != null && (n < t || n === void 0 && t >= t) && (n = t);
	else {
		let r = -1;
		for (let i of e) (i = t(i, ++r, e)) != null && (n < i || n === void 0 && i >= i) && (n = i);
	}
	return n;
}
//#endregion
//#region node_modules/d3-array/src/min.js
function wm(e, t) {
	let n;
	if (t === void 0) for (let t of e) t != null && (n > t || n === void 0 && t >= t) && (n = t);
	else {
		let r = -1;
		for (let i of e) (i = t(i, ++r, e)) != null && (n > i || n === void 0 && i >= i) && (n = i);
	}
	return n;
}
//#endregion
//#region node_modules/d3-array/src/quickselect.js
function Tm(e, t, n = 0, r = Infinity, i) {
	if (t = Math.floor(t), n = Math.floor(Math.max(0, n)), r = Math.floor(Math.min(e.length - 1, r)), !(n <= t && t <= r)) return e;
	for (i = i === void 0 ? hm : mm(i); r > n;) {
		if (r - n > 600) {
			let a = r - n + 1, o = t - n + 1, s = Math.log(a), c = .5 * Math.exp(2 * s / 3), l = .5 * Math.sqrt(s * c * (a - c) / a) * (o - a / 2 < 0 ? -1 : 1), u = Math.max(n, Math.floor(t - o * c / a + l)), d = Math.min(r, Math.floor(t + (a - o) * c / a + l));
			Tm(e, t, u, d, i);
		}
		let a = e[t], o = n, s = r;
		for (Em(e, n, t), i(e[r], a) > 0 && Em(e, n, r); o < s;) {
			for (Em(e, o, s), ++o, --s; i(e[o], a) < 0;) ++o;
			for (; i(e[s], a) > 0;) --s;
		}
		i(e[n], a) === 0 ? Em(e, n, s) : (++s, Em(e, s, r)), s <= t && (n = s + 1), t <= s && (r = s - 1);
	}
	return e;
}
function Em(e, t, n) {
	let r = e[t];
	e[t] = e[n], e[n] = r;
}
//#endregion
//#region node_modules/d3-array/src/quantile.js
function Dm(e, t, n) {
	if (e = Float64Array.from(om(e, n)), !(!(r = e.length) || isNaN(t = +t))) {
		if (t <= 0 || r < 2) return wm(e);
		if (t >= 1) return Cm(e);
		var r, i = (r - 1) * t, a = Math.floor(i), o = Cm(Tm(e, a).subarray(0, a + 1));
		return o + (wm(e.subarray(a + 1)) - o) * (i - a);
	}
}
function Om(e, t, n = am) {
	if (!(!(r = e.length) || isNaN(t = +t))) {
		if (t <= 0 || r < 2) return +n(e[0], 0, e);
		if (t >= 1) return +n(e[r - 1], r - 1, e);
		var r, i = (r - 1) * t, a = Math.floor(i), o = +n(e[a], a, e);
		return o + (+n(e[a + 1], a + 1, e) - o) * (i - a);
	}
}
//#endregion
//#region node_modules/d3-array/src/range.js
function km(e, t, n) {
	e = +e, t = +t, n = (i = arguments.length) < 2 ? (t = e, e = 0, 1) : i < 3 ? 1 : +n;
	for (var r = -1, i = Math.max(0, Math.ceil((t - e) / n)) | 0, a = Array(i); ++r < i;) a[r] = e + r * n;
	return a;
}
//#endregion
//#region node_modules/d3-scale/src/init.js
function Am(e, t) {
	switch (arguments.length) {
		case 0: break;
		case 1:
			this.range(e);
			break;
		default:
			this.range(t).domain(e);
			break;
	}
	return this;
}
function jm(e, t) {
	switch (arguments.length) {
		case 0: break;
		case 1:
			typeof e == "function" ? this.interpolator(e) : this.range(e);
			break;
		default:
			this.domain(e), typeof t == "function" ? this.interpolator(t) : this.range(t);
			break;
	}
	return this;
}
//#endregion
//#region node_modules/d3-scale/src/ordinal.js
var Mm = Symbol("implicit");
function Nm() {
	var e = new lm(), t = [], n = [], r = Mm;
	function i(i) {
		let a = e.get(i);
		if (a === void 0) {
			if (r !== Mm) return r;
			e.set(i, a = t.push(i) - 1);
		}
		return n[a % n.length];
	}
	return i.domain = function(n) {
		if (!arguments.length) return t.slice();
		t = [], e = new lm();
		for (let r of n) e.has(r) || e.set(r, t.push(r) - 1);
		return i;
	}, i.range = function(e) {
		return arguments.length ? (n = Array.from(e), i) : n.slice();
	}, i.unknown = function(e) {
		return arguments.length ? (r = e, i) : r;
	}, i.copy = function() {
		return Nm(t, n).unknown(r);
	}, Am.apply(i, arguments), i;
}
//#endregion
//#region node_modules/d3-scale/src/band.js
function Pm() {
	var e = Nm().unknown(void 0), t = e.domain, n = e.range, r = 0, i = 1, a, o, s = !1, c = 0, l = 0, u = .5;
	delete e.unknown;
	function d() {
		var e = t().length, d = i < r, f = d ? i : r, p = d ? r : i;
		a = (p - f) / Math.max(1, e - c + l * 2), s && (a = Math.floor(a)), f += (p - f - a * (e - c)) * u, o = a * (1 - c), s && (f = Math.round(f), o = Math.round(o));
		var m = km(e).map(function(e) {
			return f + a * e;
		});
		return n(d ? m.reverse() : m);
	}
	return e.domain = function(e) {
		return arguments.length ? (t(e), d()) : t();
	}, e.range = function(e) {
		return arguments.length ? ([r, i] = e, r = +r, i = +i, d()) : [r, i];
	}, e.rangeRound = function(e) {
		return [r, i] = e, r = +r, i = +i, s = !0, d();
	}, e.bandwidth = function() {
		return o;
	}, e.step = function() {
		return a;
	}, e.round = function(e) {
		return arguments.length ? (s = !!e, d()) : s;
	}, e.padding = function(e) {
		return arguments.length ? (c = Math.min(1, l = +e), d()) : c;
	}, e.paddingInner = function(e) {
		return arguments.length ? (c = Math.min(1, e), d()) : c;
	}, e.paddingOuter = function(e) {
		return arguments.length ? (l = +e, d()) : l;
	}, e.align = function(e) {
		return arguments.length ? (u = Math.max(0, Math.min(1, e)), d()) : u;
	}, e.copy = function() {
		return Pm(t(), [r, i]).round(s).paddingInner(c).paddingOuter(l).align(u);
	}, Am.apply(d(), arguments);
}
function Fm(e) {
	var t = e.copy;
	return e.padding = e.paddingOuter, delete e.paddingInner, delete e.paddingOuter, e.copy = function() {
		return Fm(t());
	}, e;
}
function Im() {
	return Fm(Pm.apply(null, arguments).paddingInner(1));
}
//#endregion
//#region node_modules/d3-color/src/define.js
function Lm(e, t, n) {
	e.prototype = t.prototype = n, n.constructor = e;
}
function Rm(e, t) {
	var n = Object.create(e.prototype);
	for (var r in t) n[r] = t[r];
	return n;
}
//#endregion
//#region node_modules/d3-color/src/color.js
function zm() {}
var Bm = .7, Vm = 1 / Bm, Hm = "\\s*([+-]?\\d+)\\s*", Um = "\\s*([+-]?(?:\\d*\\.)?\\d+(?:[eE][+-]?\\d+)?)\\s*", Wm = "\\s*([+-]?(?:\\d*\\.)?\\d+(?:[eE][+-]?\\d+)?)%\\s*", Gm = /^#([0-9a-f]{3,8})$/, Km = RegExp(`^rgb\\(${Hm},${Hm},${Hm}\\)$`), qm = RegExp(`^rgb\\(${Wm},${Wm},${Wm}\\)$`), Jm = RegExp(`^rgba\\(${Hm},${Hm},${Hm},${Um}\\)$`), Ym = RegExp(`^rgba\\(${Wm},${Wm},${Wm},${Um}\\)$`), Xm = RegExp(`^hsl\\(${Um},${Wm},${Wm}\\)$`), Zm = RegExp(`^hsla\\(${Um},${Wm},${Wm},${Um}\\)$`), Qm = {
	aliceblue: 15792383,
	antiquewhite: 16444375,
	aqua: 65535,
	aquamarine: 8388564,
	azure: 15794175,
	beige: 16119260,
	bisque: 16770244,
	black: 0,
	blanchedalmond: 16772045,
	blue: 255,
	blueviolet: 9055202,
	brown: 10824234,
	burlywood: 14596231,
	cadetblue: 6266528,
	chartreuse: 8388352,
	chocolate: 13789470,
	coral: 16744272,
	cornflowerblue: 6591981,
	cornsilk: 16775388,
	crimson: 14423100,
	cyan: 65535,
	darkblue: 139,
	darkcyan: 35723,
	darkgoldenrod: 12092939,
	darkgray: 11119017,
	darkgreen: 25600,
	darkgrey: 11119017,
	darkkhaki: 12433259,
	darkmagenta: 9109643,
	darkolivegreen: 5597999,
	darkorange: 16747520,
	darkorchid: 10040012,
	darkred: 9109504,
	darksalmon: 15308410,
	darkseagreen: 9419919,
	darkslateblue: 4734347,
	darkslategray: 3100495,
	darkslategrey: 3100495,
	darkturquoise: 52945,
	darkviolet: 9699539,
	deeppink: 16716947,
	deepskyblue: 49151,
	dimgray: 6908265,
	dimgrey: 6908265,
	dodgerblue: 2003199,
	firebrick: 11674146,
	floralwhite: 16775920,
	forestgreen: 2263842,
	fuchsia: 16711935,
	gainsboro: 14474460,
	ghostwhite: 16316671,
	gold: 16766720,
	goldenrod: 14329120,
	gray: 8421504,
	green: 32768,
	greenyellow: 11403055,
	grey: 8421504,
	honeydew: 15794160,
	hotpink: 16738740,
	indianred: 13458524,
	indigo: 4915330,
	ivory: 16777200,
	khaki: 15787660,
	lavender: 15132410,
	lavenderblush: 16773365,
	lawngreen: 8190976,
	lemonchiffon: 16775885,
	lightblue: 11393254,
	lightcoral: 15761536,
	lightcyan: 14745599,
	lightgoldenrodyellow: 16448210,
	lightgray: 13882323,
	lightgreen: 9498256,
	lightgrey: 13882323,
	lightpink: 16758465,
	lightsalmon: 16752762,
	lightseagreen: 2142890,
	lightskyblue: 8900346,
	lightslategray: 7833753,
	lightslategrey: 7833753,
	lightsteelblue: 11584734,
	lightyellow: 16777184,
	lime: 65280,
	limegreen: 3329330,
	linen: 16445670,
	magenta: 16711935,
	maroon: 8388608,
	mediumaquamarine: 6737322,
	mediumblue: 205,
	mediumorchid: 12211667,
	mediumpurple: 9662683,
	mediumseagreen: 3978097,
	mediumslateblue: 8087790,
	mediumspringgreen: 64154,
	mediumturquoise: 4772300,
	mediumvioletred: 13047173,
	midnightblue: 1644912,
	mintcream: 16121850,
	mistyrose: 16770273,
	moccasin: 16770229,
	navajowhite: 16768685,
	navy: 128,
	oldlace: 16643558,
	olive: 8421376,
	olivedrab: 7048739,
	orange: 16753920,
	orangered: 16729344,
	orchid: 14315734,
	palegoldenrod: 15657130,
	palegreen: 10025880,
	paleturquoise: 11529966,
	palevioletred: 14381203,
	papayawhip: 16773077,
	peachpuff: 16767673,
	peru: 13468991,
	pink: 16761035,
	plum: 14524637,
	powderblue: 11591910,
	purple: 8388736,
	rebeccapurple: 6697881,
	red: 16711680,
	rosybrown: 12357519,
	royalblue: 4286945,
	saddlebrown: 9127187,
	salmon: 16416882,
	sandybrown: 16032864,
	seagreen: 3050327,
	seashell: 16774638,
	sienna: 10506797,
	silver: 12632256,
	skyblue: 8900331,
	slateblue: 6970061,
	slategray: 7372944,
	slategrey: 7372944,
	snow: 16775930,
	springgreen: 65407,
	steelblue: 4620980,
	tan: 13808780,
	teal: 32896,
	thistle: 14204888,
	tomato: 16737095,
	turquoise: 4251856,
	violet: 15631086,
	wheat: 16113331,
	white: 16777215,
	whitesmoke: 16119285,
	yellow: 16776960,
	yellowgreen: 10145074
};
Lm(zm, rh, {
	copy(e) {
		return Object.assign(new this.constructor(), this, e);
	},
	displayable() {
		return this.rgb().displayable();
	},
	hex: $m,
	formatHex: $m,
	formatHex8: eh,
	formatHsl: th,
	formatRgb: nh,
	toString: nh
});
function $m() {
	return this.rgb().formatHex();
}
function eh() {
	return this.rgb().formatHex8();
}
function th() {
	return gh(this).formatHsl();
}
function nh() {
	return this.rgb().formatRgb();
}
function rh(e) {
	var t, n;
	return e = (e + "").trim().toLowerCase(), (t = Gm.exec(e)) ? (n = t[1].length, t = parseInt(t[1], 16), n === 6 ? ih(t) : n === 3 ? new ch(t >> 8 & 15 | t >> 4 & 240, t >> 4 & 15 | t & 240, (t & 15) << 4 | t & 15, 1) : n === 8 ? ah(t >> 24 & 255, t >> 16 & 255, t >> 8 & 255, (t & 255) / 255) : n === 4 ? ah(t >> 12 & 15 | t >> 8 & 240, t >> 8 & 15 | t >> 4 & 240, t >> 4 & 15 | t & 240, ((t & 15) << 4 | t & 15) / 255) : null) : (t = Km.exec(e)) ? new ch(t[1], t[2], t[3], 1) : (t = qm.exec(e)) ? new ch(t[1] * 255 / 100, t[2] * 255 / 100, t[3] * 255 / 100, 1) : (t = Jm.exec(e)) ? ah(t[1], t[2], t[3], t[4]) : (t = Ym.exec(e)) ? ah(t[1] * 255 / 100, t[2] * 255 / 100, t[3] * 255 / 100, t[4]) : (t = Xm.exec(e)) ? hh(t[1], t[2] / 100, t[3] / 100, 1) : (t = Zm.exec(e)) ? hh(t[1], t[2] / 100, t[3] / 100, t[4]) : Qm.hasOwnProperty(e) ? ih(Qm[e]) : e === "transparent" ? new ch(NaN, NaN, NaN, 0) : null;
}
function ih(e) {
	return new ch(e >> 16 & 255, e >> 8 & 255, e & 255, 1);
}
function ah(e, t, n, r) {
	return r <= 0 && (e = t = n = NaN), new ch(e, t, n, r);
}
function oh(e) {
	return e instanceof zm || (e = rh(e)), e ? (e = e.rgb(), new ch(e.r, e.g, e.b, e.opacity)) : new ch();
}
function sh(e, t, n, r) {
	return arguments.length === 1 ? oh(e) : new ch(e, t, n, r == null ? 1 : r);
}
function ch(e, t, n, r) {
	this.r = +e, this.g = +t, this.b = +n, this.opacity = +r;
}
Lm(ch, sh, Rm(zm, {
	brighter(e) {
		return e = e == null ? Vm : Vm ** +e, new ch(this.r * e, this.g * e, this.b * e, this.opacity);
	},
	darker(e) {
		return e = e == null ? Bm : Bm ** +e, new ch(this.r * e, this.g * e, this.b * e, this.opacity);
	},
	rgb() {
		return this;
	},
	clamp() {
		return new ch(ph(this.r), ph(this.g), ph(this.b), fh(this.opacity));
	},
	displayable() {
		return -.5 <= this.r && this.r < 255.5 && -.5 <= this.g && this.g < 255.5 && -.5 <= this.b && this.b < 255.5 && 0 <= this.opacity && this.opacity <= 1;
	},
	hex: lh,
	formatHex: lh,
	formatHex8: uh,
	formatRgb: dh,
	toString: dh
}));
function lh() {
	return `#${mh(this.r)}${mh(this.g)}${mh(this.b)}`;
}
function uh() {
	return `#${mh(this.r)}${mh(this.g)}${mh(this.b)}${mh((isNaN(this.opacity) ? 1 : this.opacity) * 255)}`;
}
function dh() {
	let e = fh(this.opacity);
	return `${e === 1 ? "rgb(" : "rgba("}${ph(this.r)}, ${ph(this.g)}, ${ph(this.b)}${e === 1 ? ")" : `, ${e})`}`;
}
function fh(e) {
	return isNaN(e) ? 1 : Math.max(0, Math.min(1, e));
}
function ph(e) {
	return Math.max(0, Math.min(255, Math.round(e) || 0));
}
function mh(e) {
	return e = ph(e), (e < 16 ? "0" : "") + e.toString(16);
}
function hh(e, t, n, r) {
	return r <= 0 ? e = t = n = NaN : n <= 0 || n >= 1 ? e = t = NaN : t <= 0 && (e = NaN), new vh(e, t, n, r);
}
function gh(e) {
	if (e instanceof vh) return new vh(e.h, e.s, e.l, e.opacity);
	if (e instanceof zm || (e = rh(e)), !e) return new vh();
	if (e instanceof vh) return e;
	e = e.rgb();
	var t = e.r / 255, n = e.g / 255, r = e.b / 255, i = Math.min(t, n, r), a = Math.max(t, n, r), o = NaN, s = a - i, c = (a + i) / 2;
	return s ? (o = t === a ? (n - r) / s + (n < r) * 6 : n === a ? (r - t) / s + 2 : (t - n) / s + 4, s /= c < .5 ? a + i : 2 - a - i, o *= 60) : s = c > 0 && c < 1 ? 0 : o, new vh(o, s, c, e.opacity);
}
function _h(e, t, n, r) {
	return arguments.length === 1 ? gh(e) : new vh(e, t, n, r == null ? 1 : r);
}
function vh(e, t, n, r) {
	this.h = +e, this.s = +t, this.l = +n, this.opacity = +r;
}
Lm(vh, _h, Rm(zm, {
	brighter(e) {
		return e = e == null ? Vm : Vm ** +e, new vh(this.h, this.s, this.l * e, this.opacity);
	},
	darker(e) {
		return e = e == null ? Bm : Bm ** +e, new vh(this.h, this.s, this.l * e, this.opacity);
	},
	rgb() {
		var e = this.h % 360 + (this.h < 0) * 360, t = isNaN(e) || isNaN(this.s) ? 0 : this.s, n = this.l, r = n + (n < .5 ? n : 1 - n) * t, i = 2 * n - r;
		return new ch(xh(e >= 240 ? e - 240 : e + 120, i, r), xh(e, i, r), xh(e < 120 ? e + 240 : e - 120, i, r), this.opacity);
	},
	clamp() {
		return new vh(yh(this.h), bh(this.s), bh(this.l), fh(this.opacity));
	},
	displayable() {
		return (0 <= this.s && this.s <= 1 || isNaN(this.s)) && 0 <= this.l && this.l <= 1 && 0 <= this.opacity && this.opacity <= 1;
	},
	formatHsl() {
		let e = fh(this.opacity);
		return `${e === 1 ? "hsl(" : "hsla("}${yh(this.h)}, ${bh(this.s) * 100}%, ${bh(this.l) * 100}%${e === 1 ? ")" : `, ${e})`}`;
	}
}));
function yh(e) {
	return e = (e || 0) % 360, e < 0 ? e + 360 : e;
}
function bh(e) {
	return Math.max(0, Math.min(1, e || 0));
}
function xh(e, t, n) {
	return (e < 60 ? t + (n - t) * e / 60 : e < 180 ? n : e < 240 ? t + (n - t) * (240 - e) / 60 : t) * 255;
}
//#endregion
//#region node_modules/d3-interpolate/src/constant.js
var Sh = (e) => () => e;
//#endregion
//#region node_modules/d3-interpolate/src/color.js
function Ch(e, t) {
	return function(n) {
		return e + n * t;
	};
}
function wh(e, t, n) {
	return e **= +n, t = t ** +n - e, n = 1 / n, function(r) {
		return (e + r * t) ** +n;
	};
}
function Th(e) {
	return (e = +e) == 1 ? Eh : function(t, n) {
		return n - t ? wh(t, n, e) : Sh(isNaN(t) ? n : t);
	};
}
function Eh(e, t) {
	var n = t - e;
	return n ? Ch(e, n) : Sh(isNaN(e) ? t : e);
}
//#endregion
//#region node_modules/d3-interpolate/src/rgb.js
var Dh = (function e(t) {
	var n = Th(t);
	function r(e, t) {
		var r = n((e = sh(e)).r, (t = sh(t)).r), i = n(e.g, t.g), a = n(e.b, t.b), o = Eh(e.opacity, t.opacity);
		return function(t) {
			return e.r = r(t), e.g = i(t), e.b = a(t), e.opacity = o(t), e + "";
		};
	}
	return r.gamma = e, r;
})(1);
//#endregion
//#region node_modules/d3-interpolate/src/numberArray.js
function Oh(e, t) {
	t || (t = []);
	var n = e ? Math.min(t.length, e.length) : 0, r = t.slice(), i;
	return function(a) {
		for (i = 0; i < n; ++i) r[i] = e[i] * (1 - a) + t[i] * a;
		return r;
	};
}
function kh(e) {
	return ArrayBuffer.isView(e) && !(e instanceof DataView);
}
//#endregion
//#region node_modules/d3-interpolate/src/array.js
function Ah(e, t) {
	var n = t ? t.length : 0, r = e ? Math.min(n, e.length) : 0, i = Array(r), a = Array(n), o;
	for (o = 0; o < r; ++o) i[o] = zh(e[o], t[o]);
	for (; o < n; ++o) a[o] = t[o];
	return function(e) {
		for (o = 0; o < r; ++o) a[o] = i[o](e);
		return a;
	};
}
//#endregion
//#region node_modules/d3-interpolate/src/date.js
function jh(e, t) {
	var n = /* @__PURE__ */ new Date();
	return e = +e, t = +t, function(r) {
		return n.setTime(e * (1 - r) + t * r), n;
	};
}
//#endregion
//#region node_modules/d3-interpolate/src/number.js
function Mh(e, t) {
	return e = +e, t = +t, function(n) {
		return e * (1 - n) + t * n;
	};
}
//#endregion
//#region node_modules/d3-interpolate/src/object.js
function Nh(e, t) {
	var n = {}, r = {}, i;
	for (i in (typeof e != "object" || !e) && (e = {}), (typeof t != "object" || !t) && (t = {}), t) i in e ? n[i] = zh(e[i], t[i]) : r[i] = t[i];
	return function(e) {
		for (i in n) r[i] = n[i](e);
		return r;
	};
}
//#endregion
//#region node_modules/d3-interpolate/src/string.js
var Ph = /[-+]?(?:\d+\.?\d*|\.?\d+)(?:[eE][-+]?\d+)?/g, Fh = new RegExp(Ph.source, "g");
function Ih(e) {
	return function() {
		return e;
	};
}
function Lh(e) {
	return function(t) {
		return e(t) + "";
	};
}
function Rh(e, t) {
	var n = Ph.lastIndex = Fh.lastIndex = 0, r, i, a, o = -1, s = [], c = [];
	for (e += "", t += ""; (r = Ph.exec(e)) && (i = Fh.exec(t));) (a = i.index) > n && (a = t.slice(n, a), s[o] ? s[o] += a : s[++o] = a), (r = r[0]) === (i = i[0]) ? s[o] ? s[o] += i : s[++o] = i : (s[++o] = null, c.push({
		i: o,
		x: Mh(r, i)
	})), n = Fh.lastIndex;
	return n < t.length && (a = t.slice(n), s[o] ? s[o] += a : s[++o] = a), s.length < 2 ? c[0] ? Lh(c[0].x) : Ih(t) : (t = c.length, function(e) {
		for (var n = 0, r; n < t; ++n) s[(r = c[n]).i] = r.x(e);
		return s.join("");
	});
}
//#endregion
//#region node_modules/d3-interpolate/src/value.js
function zh(e, t) {
	var n = typeof t, r;
	return t == null || n === "boolean" ? Sh(t) : (n === "number" ? Mh : n === "string" ? (r = rh(t)) ? (t = r, Dh) : Rh : t instanceof rh ? Dh : t instanceof Date ? jh : kh(t) ? Oh : Array.isArray(t) ? Ah : typeof t.valueOf != "function" && typeof t.toString != "function" || isNaN(t) ? Nh : Mh)(e, t);
}
//#endregion
//#region node_modules/d3-interpolate/src/round.js
function Bh(e, t) {
	return e = +e, t = +t, function(n) {
		return Math.round(e * (1 - n) + t * n);
	};
}
//#endregion
//#region node_modules/d3-interpolate/src/piecewise.js
function Vh(e, t) {
	t === void 0 && (t = e, e = zh);
	for (var n = 0, r = t.length - 1, i = t[0], a = Array(r < 0 ? 0 : r); n < r;) a[n] = e(i, i = t[++n]);
	return function(e) {
		var t = Math.max(0, Math.min(r - 1, Math.floor(e *= r)));
		return a[t](e - t);
	};
}
//#endregion
//#region node_modules/d3-scale/src/constant.js
function Hh(e) {
	return function() {
		return e;
	};
}
//#endregion
//#region node_modules/d3-scale/src/number.js
function Uh(e) {
	return +e;
}
//#endregion
//#region node_modules/d3-scale/src/continuous.js
var Wh = [0, 1];
function Gh(e) {
	return e;
}
function Kh(e, t) {
	return (t -= e = +e) ? function(n) {
		return (n - e) / t;
	} : Hh(isNaN(t) ? NaN : .5);
}
function qh(e, t) {
	var n;
	return e > t && (n = e, e = t, t = n), function(n) {
		return Math.max(e, Math.min(t, n));
	};
}
function Jh(e, t, n) {
	var r = e[0], i = e[1], a = t[0], o = t[1];
	return i < r ? (r = Kh(i, r), a = n(o, a)) : (r = Kh(r, i), a = n(a, o)), function(e) {
		return a(r(e));
	};
}
function Yh(e, t, n) {
	var r = Math.min(e.length, t.length) - 1, i = Array(r), a = Array(r), o = -1;
	for (e[r] < e[0] && (e = e.slice().reverse(), t = t.slice().reverse()); ++o < r;) i[o] = Kh(e[o], e[o + 1]), a[o] = n(t[o], t[o + 1]);
	return function(t) {
		var n = cm(e, t, 1, r) - 1;
		return a[n](i[n](t));
	};
}
function Xh(e, t) {
	return t.domain(e.domain()).range(e.range()).interpolate(e.interpolate()).clamp(e.clamp()).unknown(e.unknown());
}
function Zh() {
	var e = Wh, t = Wh, n = zh, r, i, a, o = Gh, s, c, l;
	function u() {
		var n = Math.min(e.length, t.length);
		return o !== Gh && (o = qh(e[0], e[n - 1])), s = n > 2 ? Yh : Jh, c = l = null, d;
	}
	function d(i) {
		return i == null || isNaN(i = +i) ? a : (c || (c = s(e.map(r), t, n)))(r(o(i)));
	}
	return d.invert = function(n) {
		return o(i((l || (l = s(t, e.map(r), Mh)))(n)));
	}, d.domain = function(t) {
		return arguments.length ? (e = Array.from(t, Uh), u()) : e.slice();
	}, d.range = function(e) {
		return arguments.length ? (t = Array.from(e), u()) : t.slice();
	}, d.rangeRound = function(e) {
		return t = Array.from(e), n = Bh, u();
	}, d.clamp = function(e) {
		return arguments.length ? (o = e ? !0 : Gh, u()) : o !== Gh;
	}, d.interpolate = function(e) {
		return arguments.length ? (n = e, u()) : n;
	}, d.unknown = function(e) {
		return arguments.length ? (a = e, d) : a;
	}, function(e, t) {
		return r = e, i = t, u();
	};
}
function Qh() {
	return Zh()(Gh, Gh);
}
//#endregion
//#region node_modules/d3-format/src/formatDecimal.js
function $h(e) {
	return Math.abs(e = Math.round(e)) >= 1e21 ? e.toLocaleString("en").replace(/,/g, "") : e.toString(10);
}
function eg(e, t) {
	if (!isFinite(e) || e === 0) return null;
	var n = (e = t ? e.toExponential(t - 1) : e.toExponential()).indexOf("e"), r = e.slice(0, n);
	return [r.length > 1 ? r[0] + r.slice(2) : r, +e.slice(n + 1)];
}
//#endregion
//#region node_modules/d3-format/src/exponent.js
function tg(e) {
	return e = eg(Math.abs(e)), e ? e[1] : NaN;
}
//#endregion
//#region node_modules/d3-format/src/formatGroup.js
function ng(e, t) {
	return function(n, r) {
		for (var i = n.length, a = [], o = 0, s = e[0], c = 0; i > 0 && s > 0 && (c + s + 1 > r && (s = Math.max(1, r - c)), a.push(n.substring(i -= s, i + s)), !((c += s + 1) > r));) s = e[o = (o + 1) % e.length];
		return a.reverse().join(t);
	};
}
//#endregion
//#region node_modules/d3-format/src/formatNumerals.js
function rg(e) {
	return function(t) {
		return t.replace(/[0-9]/g, function(t) {
			return e[+t];
		});
	};
}
//#endregion
//#region node_modules/d3-format/src/formatSpecifier.js
var ig = /^(?:(.)?([<>=^]))?([+\-( ])?([$#])?(0)?(\d+)?(,)?(\.\d+)?(~)?([a-z%])?$/i;
function ag(e) {
	if (!(t = ig.exec(e))) throw Error("invalid format: " + e);
	var t;
	return new og({
		fill: t[1],
		align: t[2],
		sign: t[3],
		symbol: t[4],
		zero: t[5],
		width: t[6],
		comma: t[7],
		precision: t[8] && t[8].slice(1),
		trim: t[9],
		type: t[10]
	});
}
ag.prototype = og.prototype;
function og(e) {
	this.fill = e.fill === void 0 ? " " : e.fill + "", this.align = e.align === void 0 ? ">" : e.align + "", this.sign = e.sign === void 0 ? "-" : e.sign + "", this.symbol = e.symbol === void 0 ? "" : e.symbol + "", this.zero = !!e.zero, this.width = e.width === void 0 ? void 0 : +e.width, this.comma = !!e.comma, this.precision = e.precision === void 0 ? void 0 : +e.precision, this.trim = !!e.trim, this.type = e.type === void 0 ? "" : e.type + "";
}
og.prototype.toString = function() {
	return this.fill + this.align + this.sign + this.symbol + (this.zero ? "0" : "") + (this.width === void 0 ? "" : Math.max(1, this.width | 0)) + (this.comma ? "," : "") + (this.precision === void 0 ? "" : "." + Math.max(0, this.precision | 0)) + (this.trim ? "~" : "") + this.type;
};
//#endregion
//#region node_modules/d3-format/src/formatTrim.js
function sg(e) {
	out: for (var t = e.length, n = 1, r = -1, i; n < t; ++n) switch (e[n]) {
		case ".":
			r = i = n;
			break;
		case "0":
			r === 0 && (r = n), i = n;
			break;
		default:
			if (!+e[n]) break out;
			r > 0 && (r = 0);
			break;
	}
	return r > 0 ? e.slice(0, r) + e.slice(i + 1) : e;
}
//#endregion
//#region node_modules/d3-format/src/formatPrefixAuto.js
var cg;
function lg(e, t) {
	var n = eg(e, t);
	if (!n) return cg = void 0, e.toPrecision(t);
	var r = n[0], i = n[1], a = i - (cg = Math.max(-8, Math.min(8, Math.floor(i / 3))) * 3) + 1, o = r.length;
	return a === o ? r : a > o ? r + Array(a - o + 1).join("0") : a > 0 ? r.slice(0, a) + "." + r.slice(a) : "0." + Array(1 - a).join("0") + eg(e, Math.max(0, t + a - 1))[0];
}
//#endregion
//#region node_modules/d3-format/src/formatRounded.js
function ug(e, t) {
	var n = eg(e, t);
	if (!n) return e + "";
	var r = n[0], i = n[1];
	return i < 0 ? "0." + Array(-i).join("0") + r : r.length > i + 1 ? r.slice(0, i + 1) + "." + r.slice(i + 1) : r + Array(i - r.length + 2).join("0");
}
//#endregion
//#region node_modules/d3-format/src/formatTypes.js
var dg = {
	"%": (e, t) => (e * 100).toFixed(t),
	b: (e) => Math.round(e).toString(2),
	c: (e) => e + "",
	d: $h,
	e: (e, t) => e.toExponential(t),
	f: (e, t) => e.toFixed(t),
	g: (e, t) => e.toPrecision(t),
	o: (e) => Math.round(e).toString(8),
	p: (e, t) => ug(e * 100, t),
	r: ug,
	s: lg,
	X: (e) => Math.round(e).toString(16).toUpperCase(),
	x: (e) => Math.round(e).toString(16)
};
//#endregion
//#region node_modules/d3-format/src/identity.js
function fg(e) {
	return e;
}
//#endregion
//#region node_modules/d3-format/src/locale.js
var pg = Array.prototype.map, mg = [
	"y",
	"z",
	"a",
	"f",
	"p",
	"n",
	"µ",
	"m",
	"",
	"k",
	"M",
	"G",
	"T",
	"P",
	"E",
	"Z",
	"Y"
];
function hg(e) {
	var t = e.grouping === void 0 || e.thousands === void 0 ? fg : ng(pg.call(e.grouping, Number), e.thousands + ""), n = e.currency === void 0 ? "" : e.currency[0] + "", r = e.currency === void 0 ? "" : e.currency[1] + "", i = e.decimal === void 0 ? "." : e.decimal + "", a = e.numerals === void 0 ? fg : rg(pg.call(e.numerals, String)), o = e.percent === void 0 ? "%" : e.percent + "", s = e.minus === void 0 ? "−" : e.minus + "", c = e.nan === void 0 ? "NaN" : e.nan + "";
	function l(e, l) {
		e = ag(e);
		var u = e.fill, d = e.align, f = e.sign, p = e.symbol, m = e.zero, h = e.width, g = e.comma, _ = e.precision, v = e.trim, y = e.type;
		y === "n" ? (g = !0, y = "g") : dg[y] || (_ === void 0 && (_ = 12), v = !0, y = "g"), (m || u === "0" && d === "=") && (m = !0, u = "0", d = "=");
		var b = (l && l.prefix !== void 0 ? l.prefix : "") + (p === "$" ? n : p === "#" && /[boxX]/.test(y) ? "0" + y.toLowerCase() : ""), x = (p === "$" ? r : /[%p]/.test(y) ? o : "") + (l && l.suffix !== void 0 ? l.suffix : ""), S = dg[y], C = /[defgprs%]/.test(y);
		_ = _ === void 0 ? 6 : /[gprs]/.test(y) ? Math.max(1, Math.min(21, _)) : Math.max(0, Math.min(20, _));
		function w(e) {
			var n = b, r = x, o, l, p;
			if (y === "c") r = S(e) + r, e = "";
			else {
				e = +e;
				var w = e < 0 || 1 / e < 0;
				if (e = isNaN(e) ? c : S(Math.abs(e), _), v && (e = sg(e)), w && +e == 0 && f !== "+" && (w = !1), n = (w ? f === "(" ? f : s : f === "-" || f === "(" ? "" : f) + n, r = (y === "s" && !isNaN(e) && cg !== void 0 ? mg[8 + cg / 3] : "") + r + (w && f === "(" ? ")" : ""), C) {
					for (o = -1, l = e.length; ++o < l;) if (p = e.charCodeAt(o), 48 > p || p > 57) {
						r = (p === 46 ? i + e.slice(o + 1) : e.slice(o)) + r, e = e.slice(0, o);
						break;
					}
				}
			}
			g && !m && (e = t(e, Infinity));
			var T = n.length + e.length + r.length, E = T < h ? Array(h - T + 1).join(u) : "";
			switch (g && m && (e = t(E + e, E.length ? h - r.length : Infinity), E = ""), d) {
				case "<":
					e = n + e + r + E;
					break;
				case "=":
					e = n + E + e + r;
					break;
				case "^":
					e = E.slice(0, T = E.length >> 1) + n + e + r + E.slice(T);
					break;
				default:
					e = E + n + e + r;
					break;
			}
			return a(e);
		}
		return w.toString = function() {
			return e + "";
		}, w;
	}
	function u(e, t) {
		var n = Math.max(-8, Math.min(8, Math.floor(tg(t) / 3))) * 3, r = 10 ** -n, i = l((e = ag(e), e.type = "f", e), { suffix: mg[8 + n / 3] });
		return function(e) {
			return i(r * e);
		};
	}
	return {
		format: l,
		formatPrefix: u
	};
}
//#endregion
//#region node_modules/d3-format/src/defaultLocale.js
var gg, _g, vg;
yg({
	thousands: ",",
	grouping: [3],
	currency: ["$", ""]
});
function yg(e) {
	return gg = hg(e), _g = gg.format, vg = gg.formatPrefix, gg;
}
//#endregion
//#region node_modules/d3-format/src/precisionFixed.js
function bg(e) {
	return Math.max(0, -tg(Math.abs(e)));
}
//#endregion
//#region node_modules/d3-format/src/precisionPrefix.js
function xg(e, t) {
	return Math.max(0, Math.max(-8, Math.min(8, Math.floor(tg(t) / 3))) * 3 - tg(Math.abs(e)));
}
//#endregion
//#region node_modules/d3-format/src/precisionRound.js
function Sg(e, t) {
	return e = Math.abs(e), t = Math.abs(t) - e, Math.max(0, tg(t) - tg(e)) + 1;
}
//#endregion
//#region node_modules/d3-scale/src/tickFormat.js
function Cg(e, t, n, r) {
	var i = Sm(e, t, n), a;
	switch (r = ag(r == null ? ",f" : r), r.type) {
		case "s":
			var o = Math.max(Math.abs(e), Math.abs(t));
			return r.precision == null && !isNaN(a = xg(i, o)) && (r.precision = a), vg(r, o);
		case "":
		case "e":
		case "g":
		case "p":
		case "r":
			r.precision == null && !isNaN(a = Sg(i, Math.max(Math.abs(e), Math.abs(t)))) && (r.precision = a - (r.type === "e"));
			break;
		case "f":
		case "%":
			r.precision == null && !isNaN(a = bg(i)) && (r.precision = a - (r.type === "%") * 2);
			break;
	}
	return _g(r);
}
//#endregion
//#region node_modules/d3-scale/src/linear.js
function wg(e) {
	var t = e.domain;
	return e.ticks = function(e) {
		var n = t();
		return bm(n[0], n[n.length - 1], e == null ? 10 : e);
	}, e.tickFormat = function(e, n) {
		var r = t();
		return Cg(r[0], r[r.length - 1], e == null ? 10 : e, n);
	}, e.nice = function(n) {
		n == null && (n = 10);
		var r = t(), i = 0, a = r.length - 1, o = r[i], s = r[a], c, l, u = 10;
		for (s < o && (l = o, o = s, s = l, l = i, i = a, a = l); u-- > 0;) {
			if (l = xm(o, s, n), l === c) return r[i] = o, r[a] = s, t(r);
			if (l > 0) o = Math.floor(o / l) * l, s = Math.ceil(s / l) * l;
			else if (l < 0) o = Math.ceil(o * l) / l, s = Math.floor(s * l) / l;
			else break;
			c = l;
		}
		return e;
	}, e;
}
function Tg() {
	var e = Qh();
	return e.copy = function() {
		return Xh(e, Tg());
	}, Am.apply(e, arguments), wg(e);
}
//#endregion
//#region node_modules/d3-scale/src/identity.js
function Eg(e) {
	var t;
	function n(e) {
		return e == null || isNaN(e = +e) ? t : e;
	}
	return n.invert = n, n.domain = n.range = function(t) {
		return arguments.length ? (e = Array.from(t, Uh), n) : e.slice();
	}, n.unknown = function(e) {
		return arguments.length ? (t = e, n) : t;
	}, n.copy = function() {
		return Eg(e).unknown(t);
	}, e = arguments.length ? Array.from(e, Uh) : [0, 1], wg(n);
}
//#endregion
//#region node_modules/d3-scale/src/nice.js
function Dg(e, t) {
	e = e.slice();
	var n = 0, r = e.length - 1, i = e[n], a = e[r], o;
	return a < i && (o = n, n = r, r = o, o = i, i = a, a = o), e[n] = t.floor(i), e[r] = t.ceil(a), e;
}
//#endregion
//#region node_modules/d3-scale/src/log.js
function Og(e) {
	return Math.log(e);
}
function kg(e) {
	return Math.exp(e);
}
function Ag(e) {
	return -Math.log(-e);
}
function jg(e) {
	return -Math.exp(-e);
}
function Mg(e) {
	return isFinite(e) ? +("1e" + e) : e < 0 ? 0 : e;
}
function Ng(e) {
	return e === 10 ? Mg : e === Math.E ? Math.exp : (t) => e ** +t;
}
function Pg(e) {
	return e === Math.E ? Math.log : e === 10 && Math.log10 || e === 2 && Math.log2 || (e = Math.log(e), (t) => Math.log(t) / e);
}
function Fg(e) {
	return (t, n) => -e(-t, n);
}
function Ig(e) {
	let t = e(Og, kg), n = t.domain, r = 10, i, a;
	function o() {
		return i = Pg(r), a = Ng(r), n()[0] < 0 ? (i = Fg(i), a = Fg(a), e(Ag, jg)) : e(Og, kg), t;
	}
	return t.base = function(e) {
		return arguments.length ? (r = +e, o()) : r;
	}, t.domain = function(e) {
		return arguments.length ? (n(e), o()) : n();
	}, t.ticks = (e) => {
		let t = n(), o = t[0], s = t[t.length - 1], c = s < o;
		c && ([o, s] = [s, o]);
		let l = i(o), u = i(s), d, f, p = e == null ? 10 : +e, m = [];
		if (!(r % 1) && u - l < p) {
			if (l = Math.floor(l), u = Math.ceil(u), o > 0) {
				for (; l <= u; ++l) for (d = 1; d < r; ++d) if (f = l < 0 ? d / a(-l) : d * a(l), !(f < o)) {
					if (f > s) break;
					m.push(f);
				}
			} else for (; l <= u; ++l) for (d = r - 1; d >= 1; --d) if (f = l > 0 ? d / a(-l) : d * a(l), !(f < o)) {
				if (f > s) break;
				m.push(f);
			}
			m.length * 2 < p && (m = bm(o, s, p));
		} else m = bm(l, u, Math.min(u - l, p)).map(a);
		return c ? m.reverse() : m;
	}, t.tickFormat = (e, n) => {
		if (e == null && (e = 10), n == null && (n = r === 10 ? "s" : ","), typeof n != "function" && (!(r % 1) && (n = ag(n)).precision == null && (n.trim = !0), n = _g(n)), e === Infinity) return n;
		let o = Math.max(1, r * e / t.ticks().length);
		return (e) => {
			let t = e / a(Math.round(i(e)));
			return t * r < r - .5 && (t *= r), t <= o ? n(e) : "";
		};
	}, t.nice = () => n(Dg(n(), {
		floor: (e) => a(Math.floor(i(e))),
		ceil: (e) => a(Math.ceil(i(e)))
	})), t;
}
function Lg() {
	let e = Ig(Zh()).domain([1, 10]);
	return e.copy = () => Xh(e, Lg()).base(e.base()), Am.apply(e, arguments), e;
}
//#endregion
//#region node_modules/d3-scale/src/symlog.js
function Rg(e) {
	return function(t) {
		return Math.sign(t) * Math.log1p(Math.abs(t / e));
	};
}
function zg(e) {
	return function(t) {
		return Math.sign(t) * Math.expm1(Math.abs(t)) * e;
	};
}
function Bg(e) {
	var t = 1, n = e(Rg(t), zg(t));
	return n.constant = function(n) {
		return arguments.length ? e(Rg(t = +n), zg(t)) : t;
	}, wg(n);
}
function Vg() {
	var e = Bg(Zh());
	return e.copy = function() {
		return Xh(e, Vg()).constant(e.constant());
	}, Am.apply(e, arguments);
}
//#endregion
//#region node_modules/d3-scale/src/pow.js
function Hg(e) {
	return function(t) {
		return t < 0 ? -((-t) ** +e) : t ** +e;
	};
}
function Ug(e) {
	return e < 0 ? -Math.sqrt(-e) : Math.sqrt(e);
}
function Wg(e) {
	return e < 0 ? -e * e : e * e;
}
function Gg(e) {
	var t = e(Gh, Gh), n = 1;
	function r() {
		return n === 1 ? e(Gh, Gh) : n === .5 ? e(Ug, Wg) : e(Hg(n), Hg(1 / n));
	}
	return t.exponent = function(e) {
		return arguments.length ? (n = +e, r()) : n;
	}, wg(t);
}
function Kg() {
	var e = Gg(Zh());
	return e.copy = function() {
		return Xh(e, Kg()).exponent(e.exponent());
	}, Am.apply(e, arguments), e;
}
function qg() {
	return Kg.apply(null, arguments).exponent(.5);
}
//#endregion
//#region node_modules/d3-scale/src/radial.js
function Jg(e) {
	return Math.sign(e) * e * e;
}
function Yg(e) {
	return Math.sign(e) * Math.sqrt(Math.abs(e));
}
function Xg() {
	var e = Qh(), t = [0, 1], n = !1, r;
	function i(t) {
		var i = Yg(e(t));
		return isNaN(i) ? r : n ? Math.round(i) : i;
	}
	return i.invert = function(t) {
		return e.invert(Jg(t));
	}, i.domain = function(t) {
		return arguments.length ? (e.domain(t), i) : e.domain();
	}, i.range = function(n) {
		return arguments.length ? (e.range((t = Array.from(n, Uh)).map(Jg)), i) : t.slice();
	}, i.rangeRound = function(e) {
		return i.range(e).round(!0);
	}, i.round = function(e) {
		return arguments.length ? (n = !!e, i) : n;
	}, i.clamp = function(t) {
		return arguments.length ? (e.clamp(t), i) : e.clamp();
	}, i.unknown = function(e) {
		return arguments.length ? (r = e, i) : r;
	}, i.copy = function() {
		return Xg(e.domain(), t).round(n).clamp(e.clamp()).unknown(r);
	}, Am.apply(i, arguments), wg(i);
}
//#endregion
//#region node_modules/d3-scale/src/quantile.js
function Zg() {
	var e = [], t = [], n = [], r;
	function i() {
		var r = 0, i = Math.max(1, t.length);
		for (n = Array(i - 1); ++r < i;) n[r - 1] = Om(e, r / i);
		return a;
	}
	function a(e) {
		return e == null || isNaN(e = +e) ? r : t[cm(n, e)];
	}
	return a.invertExtent = function(r) {
		var i = t.indexOf(r);
		return i < 0 ? [NaN, NaN] : [i > 0 ? n[i - 1] : e[0], i < n.length ? n[i] : e[e.length - 1]];
	}, a.domain = function(t) {
		if (!arguments.length) return e.slice();
		e = [];
		for (let n of t) n != null && !isNaN(n = +n) && e.push(n);
		return e.sort(tm), i();
	}, a.range = function(e) {
		return arguments.length ? (t = Array.from(e), i()) : t.slice();
	}, a.unknown = function(e) {
		return arguments.length ? (r = e, a) : r;
	}, a.quantiles = function() {
		return n.slice();
	}, a.copy = function() {
		return Zg().domain(e).range(t).unknown(r);
	}, Am.apply(a, arguments);
}
//#endregion
//#region node_modules/d3-scale/src/quantize.js
function Qg() {
	var e = 0, t = 1, n = 1, r = [.5], i = [0, 1], a;
	function o(e) {
		return e != null && e <= e ? i[cm(r, e, 0, n)] : a;
	}
	function s() {
		var i = -1;
		for (r = Array(n); ++i < n;) r[i] = ((i + 1) * t - (i - n) * e) / (n + 1);
		return o;
	}
	return o.domain = function(n) {
		return arguments.length ? ([e, t] = n, e = +e, t = +t, s()) : [e, t];
	}, o.range = function(e) {
		return arguments.length ? (n = (i = Array.from(e)).length - 1, s()) : i.slice();
	}, o.invertExtent = function(a) {
		var o = i.indexOf(a);
		return o < 0 ? [NaN, NaN] : o < 1 ? [e, r[0]] : o >= n ? [r[n - 1], t] : [r[o - 1], r[o]];
	}, o.unknown = function(e) {
		return arguments.length && (a = e), o;
	}, o.thresholds = function() {
		return r.slice();
	}, o.copy = function() {
		return Qg().domain([e, t]).range(i).unknown(a);
	}, Am.apply(wg(o), arguments);
}
//#endregion
//#region node_modules/d3-scale/src/threshold.js
function $g() {
	var e = [.5], t = [0, 1], n, r = 1;
	function i(i) {
		return i != null && i <= i ? t[cm(e, i, 0, r)] : n;
	}
	return i.domain = function(n) {
		return arguments.length ? (e = Array.from(n), r = Math.min(e.length, t.length - 1), i) : e.slice();
	}, i.range = function(n) {
		return arguments.length ? (t = Array.from(n), r = Math.min(e.length, t.length - 1), i) : t.slice();
	}, i.invertExtent = function(n) {
		var r = t.indexOf(n);
		return [e[r - 1], e[r]];
	}, i.unknown = function(e) {
		return arguments.length ? (n = e, i) : n;
	}, i.copy = function() {
		return $g().domain(e).range(t).unknown(n);
	}, Am.apply(i, arguments);
}
//#endregion
//#region node_modules/d3-time/src/interval.js
var e_ = /* @__PURE__ */ new Date(), t_ = /* @__PURE__ */ new Date();
function n_(e, t, n, r) {
	function i(t) {
		return e(t = arguments.length === 0 ? /* @__PURE__ */ new Date() : /* @__PURE__ */ new Date(+t)), t;
	}
	return i.floor = (t) => (e(t = /* @__PURE__ */ new Date(+t)), t), i.ceil = (n) => (e(n = /* @__PURE__ */ new Date(n - 1)), t(n, 1), e(n), n), i.round = (e) => {
		let t = i(e), n = i.ceil(e);
		return e - t < n - e ? t : n;
	}, i.offset = (e, n) => (t(e = /* @__PURE__ */ new Date(+e), n == null ? 1 : Math.floor(n)), e), i.range = (n, r, a) => {
		let o = [];
		if (n = i.ceil(n), a = a == null ? 1 : Math.floor(a), !(n < r) || !(a > 0)) return o;
		let s;
		do
			o.push(s = /* @__PURE__ */ new Date(+n)), t(n, a), e(n);
		while (s < n && n < r);
		return o;
	}, i.filter = (n) => n_((t) => {
		if (t >= t) for (; e(t), !n(t);) t.setTime(t - 1);
	}, (e, r) => {
		if (e >= e) if (r < 0) for (; ++r <= 0;) for (; t(e, -1), !n(e););
		else for (; --r >= 0;) for (; t(e, 1), !n(e););
	}), n && (i.count = (t, r) => (e_.setTime(+t), t_.setTime(+r), e(e_), e(t_), Math.floor(n(e_, t_))), i.every = (e) => (e = Math.floor(e), !isFinite(e) || !(e > 0) ? null : e > 1 ? i.filter(r ? (t) => r(t) % e === 0 : (t) => i.count(0, t) % e === 0) : i)), i;
}
//#endregion
//#region node_modules/d3-time/src/millisecond.js
var r_ = n_(() => {}, (e, t) => {
	e.setTime(+e + t);
}, (e, t) => t - e);
r_.every = (e) => (e = Math.floor(e), !isFinite(e) || !(e > 0) ? null : e > 1 ? n_((t) => {
	t.setTime(Math.floor(t / e) * e);
}, (t, n) => {
	t.setTime(+t + n * e);
}, (t, n) => (n - t) / e) : r_), r_.range;
//#endregion
//#region node_modules/d3-time/src/duration.js
var i_ = 1e3, a_ = i_ * 60, o_ = a_ * 60, s_ = o_ * 24, c_ = s_ * 7, l_ = s_ * 30, u_ = s_ * 365, d_ = n_((e) => {
	e.setTime(e - e.getMilliseconds());
}, (e, t) => {
	e.setTime(+e + t * i_);
}, (e, t) => (t - e) / i_, (e) => e.getUTCSeconds());
d_.range;
//#endregion
//#region node_modules/d3-time/src/minute.js
var f_ = n_((e) => {
	e.setTime(e - e.getMilliseconds() - e.getSeconds() * i_);
}, (e, t) => {
	e.setTime(+e + t * a_);
}, (e, t) => (t - e) / a_, (e) => e.getMinutes());
f_.range;
var p_ = n_((e) => {
	e.setUTCSeconds(0, 0);
}, (e, t) => {
	e.setTime(+e + t * a_);
}, (e, t) => (t - e) / a_, (e) => e.getUTCMinutes());
p_.range;
//#endregion
//#region node_modules/d3-time/src/hour.js
var m_ = n_((e) => {
	e.setTime(e - e.getMilliseconds() - e.getSeconds() * i_ - e.getMinutes() * a_);
}, (e, t) => {
	e.setTime(+e + t * o_);
}, (e, t) => (t - e) / o_, (e) => e.getHours());
m_.range;
var h_ = n_((e) => {
	e.setUTCMinutes(0, 0, 0);
}, (e, t) => {
	e.setTime(+e + t * o_);
}, (e, t) => (t - e) / o_, (e) => e.getUTCHours());
h_.range;
//#endregion
//#region node_modules/d3-time/src/day.js
var g_ = n_((e) => e.setHours(0, 0, 0, 0), (e, t) => e.setDate(e.getDate() + t), (e, t) => (t - e - (t.getTimezoneOffset() - e.getTimezoneOffset()) * a_) / s_, (e) => e.getDate() - 1);
g_.range;
var __ = n_((e) => {
	e.setUTCHours(0, 0, 0, 0);
}, (e, t) => {
	e.setUTCDate(e.getUTCDate() + t);
}, (e, t) => (t - e) / s_, (e) => e.getUTCDate() - 1);
__.range;
var v_ = n_((e) => {
	e.setUTCHours(0, 0, 0, 0);
}, (e, t) => {
	e.setUTCDate(e.getUTCDate() + t);
}, (e, t) => (t - e) / s_, (e) => Math.floor(e / s_));
v_.range;
//#endregion
//#region node_modules/d3-time/src/week.js
function y_(e) {
	return n_((t) => {
		t.setDate(t.getDate() - (t.getDay() + 7 - e) % 7), t.setHours(0, 0, 0, 0);
	}, (e, t) => {
		e.setDate(e.getDate() + t * 7);
	}, (e, t) => (t - e - (t.getTimezoneOffset() - e.getTimezoneOffset()) * a_) / c_);
}
var b_ = y_(0), x_ = y_(1), S_ = y_(2), C_ = y_(3), w_ = y_(4), T_ = y_(5), E_ = y_(6);
b_.range, x_.range, S_.range, C_.range, w_.range, T_.range, E_.range;
function D_(e) {
	return n_((t) => {
		t.setUTCDate(t.getUTCDate() - (t.getUTCDay() + 7 - e) % 7), t.setUTCHours(0, 0, 0, 0);
	}, (e, t) => {
		e.setUTCDate(e.getUTCDate() + t * 7);
	}, (e, t) => (t - e) / c_);
}
var O_ = D_(0), k_ = D_(1), A_ = D_(2), j_ = D_(3), M_ = D_(4), N_ = D_(5), P_ = D_(6);
O_.range, k_.range, A_.range, j_.range, M_.range, N_.range, P_.range;
//#endregion
//#region node_modules/d3-time/src/month.js
var F_ = n_((e) => {
	e.setDate(1), e.setHours(0, 0, 0, 0);
}, (e, t) => {
	e.setMonth(e.getMonth() + t);
}, (e, t) => t.getMonth() - e.getMonth() + (t.getFullYear() - e.getFullYear()) * 12, (e) => e.getMonth());
F_.range;
var I_ = n_((e) => {
	e.setUTCDate(1), e.setUTCHours(0, 0, 0, 0);
}, (e, t) => {
	e.setUTCMonth(e.getUTCMonth() + t);
}, (e, t) => t.getUTCMonth() - e.getUTCMonth() + (t.getUTCFullYear() - e.getUTCFullYear()) * 12, (e) => e.getUTCMonth());
I_.range;
//#endregion
//#region node_modules/d3-time/src/year.js
var L_ = n_((e) => {
	e.setMonth(0, 1), e.setHours(0, 0, 0, 0);
}, (e, t) => {
	e.setFullYear(e.getFullYear() + t);
}, (e, t) => t.getFullYear() - e.getFullYear(), (e) => e.getFullYear());
L_.every = (e) => !isFinite(e = Math.floor(e)) || !(e > 0) ? null : n_((t) => {
	t.setFullYear(Math.floor(t.getFullYear() / e) * e), t.setMonth(0, 1), t.setHours(0, 0, 0, 0);
}, (t, n) => {
	t.setFullYear(t.getFullYear() + n * e);
}), L_.range;
var R_ = n_((e) => {
	e.setUTCMonth(0, 1), e.setUTCHours(0, 0, 0, 0);
}, (e, t) => {
	e.setUTCFullYear(e.getUTCFullYear() + t);
}, (e, t) => t.getUTCFullYear() - e.getUTCFullYear(), (e) => e.getUTCFullYear());
R_.every = (e) => !isFinite(e = Math.floor(e)) || !(e > 0) ? null : n_((t) => {
	t.setUTCFullYear(Math.floor(t.getUTCFullYear() / e) * e), t.setUTCMonth(0, 1), t.setUTCHours(0, 0, 0, 0);
}, (t, n) => {
	t.setUTCFullYear(t.getUTCFullYear() + n * e);
}), R_.range;
//#endregion
//#region node_modules/d3-time/src/ticks.js
function z_(e, t, n, r, i, a) {
	let o = [
		[
			d_,
			1,
			i_
		],
		[
			d_,
			5,
			5 * i_
		],
		[
			d_,
			15,
			15 * i_
		],
		[
			d_,
			30,
			30 * i_
		],
		[
			a,
			1,
			a_
		],
		[
			a,
			5,
			5 * a_
		],
		[
			a,
			15,
			15 * a_
		],
		[
			a,
			30,
			30 * a_
		],
		[
			i,
			1,
			o_
		],
		[
			i,
			3,
			3 * o_
		],
		[
			i,
			6,
			6 * o_
		],
		[
			i,
			12,
			12 * o_
		],
		[
			r,
			1,
			s_
		],
		[
			r,
			2,
			2 * s_
		],
		[
			n,
			1,
			c_
		],
		[
			t,
			1,
			l_
		],
		[
			t,
			3,
			3 * l_
		],
		[
			e,
			1,
			u_
		]
	];
	function s(e, t, n) {
		let r = t < e;
		r && ([e, t] = [t, e]);
		let i = n && typeof n.range == "function" ? n : c(e, t, n), a = i ? i.range(e, +t + 1) : [];
		return r ? a.reverse() : a;
	}
	function c(t, n, r) {
		let i = Math.abs(n - t) / r, a = rm(([, , e]) => e).right(o, i);
		if (a === o.length) return e.every(Sm(t / u_, n / u_, r));
		if (a === 0) return r_.every(Math.max(Sm(t, n, r), 1));
		let [s, c] = o[i / o[a - 1][2] < o[a][2] / i ? a - 1 : a];
		return s.every(c);
	}
	return [s, c];
}
var [B_, V_] = z_(R_, I_, O_, v_, h_, p_), [H_, U_] = z_(L_, F_, b_, g_, m_, f_);
//#endregion
//#region node_modules/d3-time-format/src/locale.js
function W_(e) {
	if (0 <= e.y && e.y < 100) {
		var t = new Date(-1, e.m, e.d, e.H, e.M, e.S, e.L);
		return t.setFullYear(e.y), t;
	}
	return new Date(e.y, e.m, e.d, e.H, e.M, e.S, e.L);
}
function G_(e) {
	if (0 <= e.y && e.y < 100) {
		var t = new Date(Date.UTC(-1, e.m, e.d, e.H, e.M, e.S, e.L));
		return t.setUTCFullYear(e.y), t;
	}
	return new Date(Date.UTC(e.y, e.m, e.d, e.H, e.M, e.S, e.L));
}
function K_(e, t, n) {
	return {
		y: e,
		m: t,
		d: n,
		H: 0,
		M: 0,
		S: 0,
		L: 0
	};
}
function q_(e) {
	var t = e.dateTime, n = e.date, r = e.time, i = e.periods, a = e.days, o = e.shortDays, s = e.months, c = e.shortMonths, l = $_(i), u = ev(i), d = $_(a), f = ev(a), p = $_(o), m = ev(o), h = $_(s), g = ev(s), _ = $_(c), v = ev(c), y = {
		a: N,
		A: P,
		b: ee,
		B: te,
		c: null,
		d: xv,
		e: xv,
		f: Ev,
		g: Lv,
		G: zv,
		H: Sv,
		I: Cv,
		j: wv,
		L: Tv,
		m: Dv,
		M: Ov,
		p: ne,
		q: re,
		Q: cy,
		s: ly,
		S: kv,
		u: Av,
		U: jv,
		V: Nv,
		w: Pv,
		W: Fv,
		x: null,
		X: null,
		y: Iv,
		Y: Rv,
		Z: Bv,
		"%": sy
	}, b = {
		a: ie,
		A: ae,
		b: oe,
		B: se,
		c: null,
		d: Vv,
		e: Vv,
		f: Kv,
		g: ry,
		G: ay,
		H: Hv,
		I: Uv,
		j: Wv,
		L: Gv,
		m: qv,
		M: Jv,
		p: ce,
		q: le,
		Q: cy,
		s: ly,
		S: Yv,
		u: Xv,
		U: Zv,
		V: $v,
		w: ey,
		W: ty,
		x: null,
		X: null,
		y: ny,
		Y: iy,
		Z: oy,
		"%": sy
	}, x = {
		a: E,
		A: D,
		b: O,
		B: k,
		c: A,
		d: dv,
		e: dv,
		f: _v,
		g: sv,
		G: ov,
		H: pv,
		I: pv,
		j: fv,
		L: gv,
		m: uv,
		M: mv,
		p: T,
		q: lv,
		Q: yv,
		s: bv,
		S: hv,
		u: nv,
		U: rv,
		V: iv,
		w: tv,
		W: av,
		x: j,
		X: M,
		y: sv,
		Y: ov,
		Z: cv,
		"%": vv
	};
	y.x = S(n, y), y.X = S(r, y), y.c = S(t, y), b.x = S(n, b), b.X = S(r, b), b.c = S(t, b);
	function S(e, t) {
		return function(n) {
			var r = [], i = -1, a = 0, o = e.length, s, c, l;
			for (n instanceof Date || (n = /* @__PURE__ */ new Date(+n)); ++i < o;) e.charCodeAt(i) === 37 && (r.push(e.slice(a, i)), (c = J_[s = e.charAt(++i)]) == null ? c = s === "e" ? " " : "0" : s = e.charAt(++i), (l = t[s]) && (s = l(n, c)), r.push(s), a = i + 1);
			return r.push(e.slice(a, i)), r.join("");
		};
	}
	function C(e, t) {
		return function(n) {
			var r = K_(1900, void 0, 1), i = w(r, e, n += "", 0), a, o;
			if (i != n.length) return null;
			if ("Q" in r) return new Date(r.Q);
			if ("s" in r) return new Date(r.s * 1e3 + ("L" in r ? r.L : 0));
			if (t && !("Z" in r) && (r.Z = 0), "p" in r && (r.H = r.H % 12 + r.p * 12), r.m === void 0 && (r.m = "q" in r ? r.q : 0), "V" in r) {
				if (r.V < 1 || r.V > 53) return null;
				"w" in r || (r.w = 1), "Z" in r ? (a = G_(K_(r.y, 0, 1)), o = a.getUTCDay(), a = o > 4 || o === 0 ? k_.ceil(a) : k_(a), a = __.offset(a, (r.V - 1) * 7), r.y = a.getUTCFullYear(), r.m = a.getUTCMonth(), r.d = a.getUTCDate() + (r.w + 6) % 7) : (a = W_(K_(r.y, 0, 1)), o = a.getDay(), a = o > 4 || o === 0 ? x_.ceil(a) : x_(a), a = g_.offset(a, (r.V - 1) * 7), r.y = a.getFullYear(), r.m = a.getMonth(), r.d = a.getDate() + (r.w + 6) % 7);
			} else ("W" in r || "U" in r) && ("w" in r || (r.w = "u" in r ? r.u % 7 : +("W" in r)), o = "Z" in r ? G_(K_(r.y, 0, 1)).getUTCDay() : W_(K_(r.y, 0, 1)).getDay(), r.m = 0, r.d = "W" in r ? (r.w + 6) % 7 + r.W * 7 - (o + 5) % 7 : r.w + r.U * 7 - (o + 6) % 7);
			return "Z" in r ? (r.H += r.Z / 100 | 0, r.M += r.Z % 100, G_(r)) : W_(r);
		};
	}
	function w(e, t, n, r) {
		for (var i = 0, a = t.length, o = n.length, s, c; i < a;) {
			if (r >= o) return -1;
			if (s = t.charCodeAt(i++), s === 37) {
				if (s = t.charAt(i++), c = x[s in J_ ? t.charAt(i++) : s], !c || (r = c(e, n, r)) < 0) return -1;
			} else if (s != n.charCodeAt(r++)) return -1;
		}
		return r;
	}
	function T(e, t, n) {
		var r = l.exec(t.slice(n));
		return r ? (e.p = u.get(r[0].toLowerCase()), n + r[0].length) : -1;
	}
	function E(e, t, n) {
		var r = p.exec(t.slice(n));
		return r ? (e.w = m.get(r[0].toLowerCase()), n + r[0].length) : -1;
	}
	function D(e, t, n) {
		var r = d.exec(t.slice(n));
		return r ? (e.w = f.get(r[0].toLowerCase()), n + r[0].length) : -1;
	}
	function O(e, t, n) {
		var r = _.exec(t.slice(n));
		return r ? (e.m = v.get(r[0].toLowerCase()), n + r[0].length) : -1;
	}
	function k(e, t, n) {
		var r = h.exec(t.slice(n));
		return r ? (e.m = g.get(r[0].toLowerCase()), n + r[0].length) : -1;
	}
	function A(e, n, r) {
		return w(e, t, n, r);
	}
	function j(e, t, r) {
		return w(e, n, t, r);
	}
	function M(e, t, n) {
		return w(e, r, t, n);
	}
	function N(e) {
		return o[e.getDay()];
	}
	function P(e) {
		return a[e.getDay()];
	}
	function ee(e) {
		return c[e.getMonth()];
	}
	function te(e) {
		return s[e.getMonth()];
	}
	function ne(e) {
		return i[+(e.getHours() >= 12)];
	}
	function re(e) {
		return 1 + ~~(e.getMonth() / 3);
	}
	function ie(e) {
		return o[e.getUTCDay()];
	}
	function ae(e) {
		return a[e.getUTCDay()];
	}
	function oe(e) {
		return c[e.getUTCMonth()];
	}
	function se(e) {
		return s[e.getUTCMonth()];
	}
	function ce(e) {
		return i[+(e.getUTCHours() >= 12)];
	}
	function le(e) {
		return 1 + ~~(e.getUTCMonth() / 3);
	}
	return {
		format: function(e) {
			var t = S(e += "", y);
			return t.toString = function() {
				return e;
			}, t;
		},
		parse: function(e) {
			var t = C(e += "", !1);
			return t.toString = function() {
				return e;
			}, t;
		},
		utcFormat: function(e) {
			var t = S(e += "", b);
			return t.toString = function() {
				return e;
			}, t;
		},
		utcParse: function(e) {
			var t = C(e += "", !0);
			return t.toString = function() {
				return e;
			}, t;
		}
	};
}
var J_ = {
	"-": "",
	_: " ",
	0: "0"
}, Y_ = /^\s*\d+/, X_ = /^%/, Z_ = /[\\^$*+?|[\]().{}]/g;
function Y(e, t, n) {
	var r = e < 0 ? "-" : "", i = (r ? -e : e) + "", a = i.length;
	return r + (a < n ? Array(n - a + 1).join(t) + i : i);
}
function Q_(e) {
	return e.replace(Z_, "\\$&");
}
function $_(e) {
	return RegExp("^(?:" + e.map(Q_).join("|") + ")", "i");
}
function ev(e) {
	return new Map(e.map((e, t) => [e.toLowerCase(), t]));
}
function tv(e, t, n) {
	var r = Y_.exec(t.slice(n, n + 1));
	return r ? (e.w = +r[0], n + r[0].length) : -1;
}
function nv(e, t, n) {
	var r = Y_.exec(t.slice(n, n + 1));
	return r ? (e.u = +r[0], n + r[0].length) : -1;
}
function rv(e, t, n) {
	var r = Y_.exec(t.slice(n, n + 2));
	return r ? (e.U = +r[0], n + r[0].length) : -1;
}
function iv(e, t, n) {
	var r = Y_.exec(t.slice(n, n + 2));
	return r ? (e.V = +r[0], n + r[0].length) : -1;
}
function av(e, t, n) {
	var r = Y_.exec(t.slice(n, n + 2));
	return r ? (e.W = +r[0], n + r[0].length) : -1;
}
function ov(e, t, n) {
	var r = Y_.exec(t.slice(n, n + 4));
	return r ? (e.y = +r[0], n + r[0].length) : -1;
}
function sv(e, t, n) {
	var r = Y_.exec(t.slice(n, n + 2));
	return r ? (e.y = +r[0] + (+r[0] > 68 ? 1900 : 2e3), n + r[0].length) : -1;
}
function cv(e, t, n) {
	var r = /^(Z)|([+-]\d\d)(?::?(\d\d))?/.exec(t.slice(n, n + 6));
	return r ? (e.Z = r[1] ? 0 : -(r[2] + (r[3] || "00")), n + r[0].length) : -1;
}
function lv(e, t, n) {
	var r = Y_.exec(t.slice(n, n + 1));
	return r ? (e.q = r[0] * 3 - 3, n + r[0].length) : -1;
}
function uv(e, t, n) {
	var r = Y_.exec(t.slice(n, n + 2));
	return r ? (e.m = r[0] - 1, n + r[0].length) : -1;
}
function dv(e, t, n) {
	var r = Y_.exec(t.slice(n, n + 2));
	return r ? (e.d = +r[0], n + r[0].length) : -1;
}
function fv(e, t, n) {
	var r = Y_.exec(t.slice(n, n + 3));
	return r ? (e.m = 0, e.d = +r[0], n + r[0].length) : -1;
}
function pv(e, t, n) {
	var r = Y_.exec(t.slice(n, n + 2));
	return r ? (e.H = +r[0], n + r[0].length) : -1;
}
function mv(e, t, n) {
	var r = Y_.exec(t.slice(n, n + 2));
	return r ? (e.M = +r[0], n + r[0].length) : -1;
}
function hv(e, t, n) {
	var r = Y_.exec(t.slice(n, n + 2));
	return r ? (e.S = +r[0], n + r[0].length) : -1;
}
function gv(e, t, n) {
	var r = Y_.exec(t.slice(n, n + 3));
	return r ? (e.L = +r[0], n + r[0].length) : -1;
}
function _v(e, t, n) {
	var r = Y_.exec(t.slice(n, n + 6));
	return r ? (e.L = Math.floor(r[0] / 1e3), n + r[0].length) : -1;
}
function vv(e, t, n) {
	var r = X_.exec(t.slice(n, n + 1));
	return r ? n + r[0].length : -1;
}
function yv(e, t, n) {
	var r = Y_.exec(t.slice(n));
	return r ? (e.Q = +r[0], n + r[0].length) : -1;
}
function bv(e, t, n) {
	var r = Y_.exec(t.slice(n));
	return r ? (e.s = +r[0], n + r[0].length) : -1;
}
function xv(e, t) {
	return Y(e.getDate(), t, 2);
}
function Sv(e, t) {
	return Y(e.getHours(), t, 2);
}
function Cv(e, t) {
	return Y(e.getHours() % 12 || 12, t, 2);
}
function wv(e, t) {
	return Y(1 + g_.count(L_(e), e), t, 3);
}
function Tv(e, t) {
	return Y(e.getMilliseconds(), t, 3);
}
function Ev(e, t) {
	return Tv(e, t) + "000";
}
function Dv(e, t) {
	return Y(e.getMonth() + 1, t, 2);
}
function Ov(e, t) {
	return Y(e.getMinutes(), t, 2);
}
function kv(e, t) {
	return Y(e.getSeconds(), t, 2);
}
function Av(e) {
	var t = e.getDay();
	return t === 0 ? 7 : t;
}
function jv(e, t) {
	return Y(b_.count(L_(e) - 1, e), t, 2);
}
function Mv(e) {
	var t = e.getDay();
	return t >= 4 || t === 0 ? w_(e) : w_.ceil(e);
}
function Nv(e, t) {
	return e = Mv(e), Y(w_.count(L_(e), e) + (L_(e).getDay() === 4), t, 2);
}
function Pv(e) {
	return e.getDay();
}
function Fv(e, t) {
	return Y(x_.count(L_(e) - 1, e), t, 2);
}
function Iv(e, t) {
	return Y(e.getFullYear() % 100, t, 2);
}
function Lv(e, t) {
	return e = Mv(e), Y(e.getFullYear() % 100, t, 2);
}
function Rv(e, t) {
	return Y(e.getFullYear() % 1e4, t, 4);
}
function zv(e, t) {
	var n = e.getDay();
	return e = n >= 4 || n === 0 ? w_(e) : w_.ceil(e), Y(e.getFullYear() % 1e4, t, 4);
}
function Bv(e) {
	var t = e.getTimezoneOffset();
	return (t > 0 ? "-" : (t *= -1, "+")) + Y(t / 60 | 0, "0", 2) + Y(t % 60, "0", 2);
}
function Vv(e, t) {
	return Y(e.getUTCDate(), t, 2);
}
function Hv(e, t) {
	return Y(e.getUTCHours(), t, 2);
}
function Uv(e, t) {
	return Y(e.getUTCHours() % 12 || 12, t, 2);
}
function Wv(e, t) {
	return Y(1 + __.count(R_(e), e), t, 3);
}
function Gv(e, t) {
	return Y(e.getUTCMilliseconds(), t, 3);
}
function Kv(e, t) {
	return Gv(e, t) + "000";
}
function qv(e, t) {
	return Y(e.getUTCMonth() + 1, t, 2);
}
function Jv(e, t) {
	return Y(e.getUTCMinutes(), t, 2);
}
function Yv(e, t) {
	return Y(e.getUTCSeconds(), t, 2);
}
function Xv(e) {
	var t = e.getUTCDay();
	return t === 0 ? 7 : t;
}
function Zv(e, t) {
	return Y(O_.count(R_(e) - 1, e), t, 2);
}
function Qv(e) {
	var t = e.getUTCDay();
	return t >= 4 || t === 0 ? M_(e) : M_.ceil(e);
}
function $v(e, t) {
	return e = Qv(e), Y(M_.count(R_(e), e) + (R_(e).getUTCDay() === 4), t, 2);
}
function ey(e) {
	return e.getUTCDay();
}
function ty(e, t) {
	return Y(k_.count(R_(e) - 1, e), t, 2);
}
function ny(e, t) {
	return Y(e.getUTCFullYear() % 100, t, 2);
}
function ry(e, t) {
	return e = Qv(e), Y(e.getUTCFullYear() % 100, t, 2);
}
function iy(e, t) {
	return Y(e.getUTCFullYear() % 1e4, t, 4);
}
function ay(e, t) {
	var n = e.getUTCDay();
	return e = n >= 4 || n === 0 ? M_(e) : M_.ceil(e), Y(e.getUTCFullYear() % 1e4, t, 4);
}
function oy() {
	return "+0000";
}
function sy() {
	return "%";
}
function cy(e) {
	return +e;
}
function ly(e) {
	return Math.floor(e / 1e3);
}
//#endregion
//#region node_modules/d3-time-format/src/defaultLocale.js
var uy, dy, fy;
py({
	dateTime: "%x, %X",
	date: "%-m/%-d/%Y",
	time: "%-I:%M:%S %p",
	periods: ["AM", "PM"],
	days: [
		"Sunday",
		"Monday",
		"Tuesday",
		"Wednesday",
		"Thursday",
		"Friday",
		"Saturday"
	],
	shortDays: [
		"Sun",
		"Mon",
		"Tue",
		"Wed",
		"Thu",
		"Fri",
		"Sat"
	],
	months: [
		"January",
		"February",
		"March",
		"April",
		"May",
		"June",
		"July",
		"August",
		"September",
		"October",
		"November",
		"December"
	],
	shortMonths: [
		"Jan",
		"Feb",
		"Mar",
		"Apr",
		"May",
		"Jun",
		"Jul",
		"Aug",
		"Sep",
		"Oct",
		"Nov",
		"Dec"
	]
});
function py(e) {
	return uy = q_(e), dy = uy.format, uy.parse, fy = uy.utcFormat, uy.utcParse, uy;
}
//#endregion
//#region node_modules/d3-scale/src/time.js
function my(e) {
	return new Date(e);
}
function hy(e) {
	return e instanceof Date ? +e : +/* @__PURE__ */ new Date(+e);
}
function gy(e, t, n, r, i, a, o, s, c, l) {
	var u = Qh(), d = u.invert, f = u.domain, p = l(".%L"), m = l(":%S"), h = l("%I:%M"), g = l("%I %p"), _ = l("%a %d"), v = l("%b %d"), y = l("%B"), b = l("%Y");
	function x(e) {
		return (c(e) < e ? p : s(e) < e ? m : o(e) < e ? h : a(e) < e ? g : r(e) < e ? i(e) < e ? _ : v : n(e) < e ? y : b)(e);
	}
	return u.invert = function(e) {
		return new Date(d(e));
	}, u.domain = function(e) {
		return arguments.length ? f(Array.from(e, hy)) : f().map(my);
	}, u.ticks = function(t) {
		var n = f();
		return e(n[0], n[n.length - 1], t == null ? 10 : t);
	}, u.tickFormat = function(e, t) {
		return t == null ? x : l(t);
	}, u.nice = function(e) {
		var n = f();
		return (!e || typeof e.range != "function") && (e = t(n[0], n[n.length - 1], e == null ? 10 : e)), e ? f(Dg(n, e)) : u;
	}, u.copy = function() {
		return Xh(u, gy(e, t, n, r, i, a, o, s, c, l));
	}, u;
}
function _y() {
	return Am.apply(gy(H_, U_, L_, F_, b_, g_, m_, f_, d_, dy).domain([new Date(2e3, 0, 1), new Date(2e3, 0, 2)]), arguments);
}
//#endregion
//#region node_modules/d3-scale/src/utcTime.js
function vy() {
	return Am.apply(gy(B_, V_, R_, I_, O_, __, h_, p_, d_, fy).domain([Date.UTC(2e3, 0, 1), Date.UTC(2e3, 0, 2)]), arguments);
}
//#endregion
//#region node_modules/d3-scale/src/sequential.js
function yy() {
	var e = 0, t = 1, n, r, i, a, o = Gh, s = !1, c;
	function l(e) {
		return e == null || isNaN(e = +e) ? c : o(i === 0 ? .5 : (e = (a(e) - n) * i, s ? Math.max(0, Math.min(1, e)) : e));
	}
	l.domain = function(o) {
		return arguments.length ? ([e, t] = o, n = a(e = +e), r = a(t = +t), i = n === r ? 0 : 1 / (r - n), l) : [e, t];
	}, l.clamp = function(e) {
		return arguments.length ? (s = !!e, l) : s;
	}, l.interpolator = function(e) {
		return arguments.length ? (o = e, l) : o;
	};
	function u(e) {
		return function(t) {
			var n, r;
			return arguments.length ? ([n, r] = t, o = e(n, r), l) : [o(0), o(1)];
		};
	}
	return l.range = u(zh), l.rangeRound = u(Bh), l.unknown = function(e) {
		return arguments.length ? (c = e, l) : c;
	}, function(o) {
		return a = o, n = o(e), r = o(t), i = n === r ? 0 : 1 / (r - n), l;
	};
}
function by(e, t) {
	return t.domain(e.domain()).interpolator(e.interpolator()).clamp(e.clamp()).unknown(e.unknown());
}
function xy() {
	var e = wg(yy()(Gh));
	return e.copy = function() {
		return by(e, xy());
	}, jm.apply(e, arguments);
}
function Sy() {
	var e = Ig(yy()).domain([1, 10]);
	return e.copy = function() {
		return by(e, Sy()).base(e.base());
	}, jm.apply(e, arguments);
}
function Cy() {
	var e = Bg(yy());
	return e.copy = function() {
		return by(e, Cy()).constant(e.constant());
	}, jm.apply(e, arguments);
}
function wy() {
	var e = Gg(yy());
	return e.copy = function() {
		return by(e, wy()).exponent(e.exponent());
	}, jm.apply(e, arguments);
}
function Ty() {
	return wy.apply(null, arguments).exponent(.5);
}
//#endregion
//#region node_modules/d3-scale/src/sequentialQuantile.js
function Ey() {
	var e = [], t = Gh;
	function n(n) {
		if (n != null && !isNaN(n = +n)) return t((cm(e, n, 1) - 1) / (e.length - 1));
	}
	return n.domain = function(t) {
		if (!arguments.length) return e.slice();
		e = [];
		for (let n of t) n != null && !isNaN(n = +n) && e.push(n);
		return e.sort(tm), n;
	}, n.interpolator = function(e) {
		return arguments.length ? (t = e, n) : t;
	}, n.range = function() {
		return e.map((n, r) => t(r / (e.length - 1)));
	}, n.quantiles = function(t) {
		return Array.from({ length: t + 1 }, (n, r) => Dm(e, r / t));
	}, n.copy = function() {
		return Ey(t).domain(e);
	}, jm.apply(n, arguments);
}
//#endregion
//#region node_modules/d3-scale/src/diverging.js
function Dy() {
	var e = 0, t = .5, n = 1, r = 1, i, a, o, s, c, l = Gh, u, d = !1, f;
	function p(e) {
		return isNaN(e = +e) ? f : (e = .5 + ((e = +u(e)) - a) * (r * e < r * a ? s : c), l(d ? Math.max(0, Math.min(1, e)) : e));
	}
	p.domain = function(l) {
		return arguments.length ? ([e, t, n] = l, i = u(e = +e), a = u(t = +t), o = u(n = +n), s = i === a ? 0 : .5 / (a - i), c = a === o ? 0 : .5 / (o - a), r = a < i ? -1 : 1, p) : [
			e,
			t,
			n
		];
	}, p.clamp = function(e) {
		return arguments.length ? (d = !!e, p) : d;
	}, p.interpolator = function(e) {
		return arguments.length ? (l = e, p) : l;
	};
	function m(e) {
		return function(t) {
			var n, r, i;
			return arguments.length ? ([n, r, i] = t, l = Vh(e, [
				n,
				r,
				i
			]), p) : [
				l(0),
				l(.5),
				l(1)
			];
		};
	}
	return p.range = m(zh), p.rangeRound = m(Bh), p.unknown = function(e) {
		return arguments.length ? (f = e, p) : f;
	}, function(l) {
		return u = l, i = l(e), a = l(t), o = l(n), s = i === a ? 0 : .5 / (a - i), c = a === o ? 0 : .5 / (o - a), r = a < i ? -1 : 1, p;
	};
}
function Oy() {
	var e = wg(Dy()(Gh));
	return e.copy = function() {
		return by(e, Oy());
	}, jm.apply(e, arguments);
}
function ky() {
	var e = Ig(Dy()).domain([
		.1,
		1,
		10
	]);
	return e.copy = function() {
		return by(e, ky()).base(e.base());
	}, jm.apply(e, arguments);
}
function Ay() {
	var e = Bg(Dy());
	return e.copy = function() {
		return by(e, Ay()).constant(e.constant());
	}, jm.apply(e, arguments);
}
function jy() {
	var e = Gg(Dy());
	return e.copy = function() {
		return by(e, jy()).exponent(e.exponent());
	}, jm.apply(e, arguments);
}
function My() {
	return jy.apply(null, arguments).exponent(.5);
}
//#endregion
//#region node_modules/victory-vendor/es/d3-scale.js
var Ny = /* @__PURE__ */ s({
	scaleBand: () => Pm,
	scaleDiverging: () => Oy,
	scaleDivergingLog: () => ky,
	scaleDivergingPow: () => jy,
	scaleDivergingSqrt: () => My,
	scaleDivergingSymlog: () => Ay,
	scaleIdentity: () => Eg,
	scaleImplicit: () => Mm,
	scaleLinear: () => Tg,
	scaleLog: () => Lg,
	scaleOrdinal: () => Nm,
	scalePoint: () => Im,
	scalePow: () => Kg,
	scaleQuantile: () => Zg,
	scaleQuantize: () => Qg,
	scaleRadial: () => Xg,
	scaleSequential: () => xy,
	scaleSequentialLog: () => Sy,
	scaleSequentialPow: () => wy,
	scaleSequentialQuantile: () => Ey,
	scaleSequentialSqrt: () => Ty,
	scaleSequentialSymlog: () => Cy,
	scaleSqrt: () => qg,
	scaleSymlog: () => Vg,
	scaleThreshold: () => $g,
	scaleTime: () => _y,
	scaleUtc: () => vy,
	tickFormat: () => Cg
});
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineConfiguredScale.js
function Py(e) {
	var t = Ny;
	if (e in t && typeof t[e] == "function") return t[e]();
	var n = `scale${tn(e)}`;
	if (n in t && typeof t[n] == "function") return t[n]();
}
function Fy(e, t, n) {
	if (typeof e == "function") return e.copy().domain(t).range(n);
	if (e != null) {
		var r = Py(e);
		if (r != null) return r.domain(t).range(n), r;
	}
}
function Iy(e, t, n, r) {
	if (!(n == null || r == null)) return typeof e.scale == "function" ? Fy(e.scale, n, r) : Fy(t, n, r);
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineRealScaleType.js
function Ly(e) {
	return `scale${tn(e)}`;
}
function Ry(e) {
	return Ly(e) in Ny;
}
var zy = (e, t, n) => {
	if (e != null) {
		var r = e.scale, i = e.type;
		if (r === "auto") return i === "category" && n && (n.indexOf("LineChart") >= 0 || n.indexOf("AreaChart") >= 0 || n.indexOf("ComposedChart") >= 0 && !t) ? "point" : i === "category" ? "band" : "linear";
		if (typeof r == "string") return Ry(r) ? r : "point";
	}
};
//#endregion
//#region node_modules/recharts/es6/util/scale/createCategoricalInverse.js
function By(e, t) {
	for (var n = 0, r = e.length, i = e[0] < e[e.length - 1]; n < r;) {
		var a = Math.floor((n + r) / 2);
		(i ? e[a] < t : e[a] > t) ? n = a + 1 : r = a;
	}
	return n;
}
function Vy(e, t) {
	if (e) {
		var n = t == null ? e.domain() : t, r = n.map((t) => {
			var n;
			return (n = e(t)) == null ? 0 : n;
		}), i = e.range();
		if (!(n.length === 0 || i.length < 2)) return (e) => {
			var t, i, a = By(r, e);
			if (a <= 0) return n[0];
			if (a >= n.length) return n[n.length - 1];
			var o = (t = r[a - 1]) == null ? 0 : t, s = (i = r[a]) == null ? 0 : i;
			return Math.abs(e - o) <= Math.abs(e - s) ? n[a - 1] : n[a];
		};
	}
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineInverseScaleFunction.js
function Hy(e) {
	if (e != null) return "invert" in e && typeof e.invert == "function" ? e.invert.bind(e) : Vy(e, void 0);
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/axisSelectors.js
function Uy(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Wy(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Uy(Object(n), !0).forEach(function(t) {
			Gy(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Uy(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Gy(e, t, n) {
	return (t = Ky(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function Ky(e) {
	var t = qy(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function qy(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function Jy(e, t) {
	return $y(e) || Qy(e, t) || Xy(e, t) || Yy();
}
function Yy() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function Xy(e, t) {
	if (e) {
		if (typeof e == "string") return Zy(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? Zy(e, t) : void 0;
	}
}
function Zy(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function Qy(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function $y(e) {
	if (Array.isArray(e)) return e;
}
var eb = [0, "auto"], tb = {
	allowDataOverflow: !1,
	allowDecimals: !0,
	allowDuplicatedCategory: !0,
	angle: 0,
	dataKey: void 0,
	domain: void 0,
	height: 30,
	hide: !0,
	id: 0,
	includeHidden: !1,
	interval: "preserveEnd",
	minTickGap: 5,
	mirror: !1,
	name: void 0,
	orientation: "bottom",
	padding: {
		left: 0,
		right: 0
	},
	reversed: !1,
	scale: "auto",
	tick: !0,
	tickCount: 5,
	tickFormatter: void 0,
	ticks: void 0,
	type: "category",
	unit: void 0,
	niceTicks: "auto"
}, nb = (e, t) => e.cartesianAxis.xAxis[t], rb = (e, t) => {
	var n = nb(e, t);
	return n == null ? tb : n;
}, ib = {
	allowDataOverflow: !1,
	allowDecimals: !0,
	allowDuplicatedCategory: !0,
	angle: 0,
	dataKey: void 0,
	domain: eb,
	hide: !0,
	id: 0,
	includeHidden: !1,
	interval: "preserveEnd",
	minTickGap: 5,
	mirror: !1,
	name: void 0,
	orientation: "left",
	padding: {
		top: 0,
		bottom: 0
	},
	reversed: !1,
	scale: "auto",
	tick: !0,
	tickCount: 5,
	tickFormatter: void 0,
	ticks: void 0,
	type: "number",
	unit: void 0,
	niceTicks: "auto",
	width: 60
}, ab = (e, t) => e.cartesianAxis.yAxis[t], ob = (e, t) => {
	var n = ab(e, t);
	return n == null ? ib : n;
}, sb = {
	domain: [0, "auto"],
	includeHidden: !1,
	reversed: !1,
	allowDataOverflow: !1,
	allowDuplicatedCategory: !1,
	dataKey: void 0,
	id: 0,
	name: "",
	range: [64, 64],
	scale: "auto",
	type: "number",
	unit: ""
}, cb = (e, t) => {
	var n = e.cartesianAxis.zAxis[t];
	return n == null ? sb : n;
}, lb = (e, t, n) => {
	switch (t) {
		case "xAxis": return rb(e, n);
		case "yAxis": return ob(e, n);
		case "zAxis": return cb(e, n);
		case "angleAxis": return Pp(e, n);
		case "radiusAxis": return Fp(e, n);
		default: throw Error(`Unexpected axis type: ${t}`);
	}
}, ub = (e, t, n) => {
	switch (t) {
		case "xAxis": return rb(e, n);
		case "yAxis": return ob(e, n);
		default: throw Error(`Unexpected axis type: ${t}`);
	}
}, db = (e, t, n) => {
	switch (t) {
		case "xAxis": return rb(e, n);
		case "yAxis": return ob(e, n);
		case "angleAxis": return Pp(e, n);
		case "radiusAxis": return Fp(e, n);
		default: throw Error(`Unexpected axis type: ${t}`);
	}
}, fb = (e) => e.graphicalItems.cartesianItems.some((e) => e.type === "bar") || e.graphicalItems.polarItems.some((e) => e.type === "radialBar");
function pb(e, t) {
	return (n) => {
		switch (e) {
			case "xAxis": return "xAxisId" in n && n.xAxisId === t;
			case "yAxis": return "yAxisId" in n && n.yAxisId === t;
			case "zAxis": return "zAxisId" in n && n.zAxisId === t;
			case "angleAxis": return "angleAxisId" in n && n.angleAxisId === t;
			case "radiusAxis": return "radiusAxisId" in n && n.radiusAxisId === t;
			default: return !1;
		}
	};
}
var mb = (e) => e.graphicalItems.cartesianItems, hb = R([Up, Wp], pb), gb = (e, t, n) => e.filter(n).filter((e) => (t == null ? void 0 : t.includeHidden) === !0 || !e.hide), _b = R([
	mb,
	lb,
	hb
], gb, { memoizeOptions: { resultEqualityCheck: Yp } }), vb = R([_b], (e) => e.filter((e) => e.type === "area" || e.type === "bar").filter(qp)), yb = (e) => e.filter((e) => !("stackId" in e) || e.stackId === void 0), bb = R([_b], yb), xb = (e) => e.map((e) => e.data).filter(Boolean).flat(1), Sb = R([_b], (e) => e.some((e) => !e.data)), Cb = R([_b], xb, { memoizeOptions: { resultEqualityCheck: Yp } }), wb = (e, t) => {
	var n = t.chartData, r = n === void 0 ? [] : n, i = t.dataStartIndex, a = t.dataEndIndex;
	return e.length > 0 ? e : r.slice(i, a + 1);
}, Tb = R([Cb, Lf], wb), Eb = (e, t, n) => (t == null ? void 0 : t.dataKey) == null ? n.length > 0 ? n.map((e) => e.dataKey).flatMap((t) => e.map((e) => ({ value: W(e, t) }))) : e.map((e) => ({ value: e })) : e.map((e) => ({ value: W(e, t.dataKey) })), Db = (e, t, n, r, i, a) => {
	var o = r.chartData, s = o === void 0 ? [] : o, c = r.dataStartIndex, l = r.dataEndIndex, u = Eb(e, t, n);
	return i && (t == null ? void 0 : t.dataKey) != null && a.length > 0 ? [...s.slice(c, l + 1).map((e) => ({ value: W(e, t.dataKey) })).filter((e) => e.value != null), ...u] : u;
}, Ob = R([
	Tb,
	lb,
	_b,
	Lf,
	Sb,
	Cb
], Db);
function kb(e) {
	if (qt(e) || e instanceof Date) {
		var t = Number(e);
		if (U(t)) return t;
	}
}
function Ab(e) {
	if (Array.isArray(e)) {
		var t = [kb(e[0]), kb(e[1])];
		return qf(t) ? t : void 0;
	}
	var n = kb(e);
	if (n != null) return [n, n];
}
function jb(e) {
	return e.map(kb).filter(nn);
}
function Mb(e, t) {
	var n = kb(e), r = kb(t);
	return n == null && r == null ? 0 : n == null ? -1 : r == null ? 1 : n - r;
}
var Nb = R([Ob], (e) => e == null ? void 0 : e.map((e) => e.value).sort(Mb));
function Pb(e, t) {
	switch (e) {
		case "xAxis": return t.direction === "x";
		case "yAxis": return t.direction === "y";
		default: return !1;
	}
}
function Fb(e, t, n) {
	if (!n || !n.length) return [];
	var r;
	if (typeof t == "number" && !Kt(t)) r = t;
	else if (Array.isArray(t)) {
		var i = jb(t);
		i.length > 0 && (r = Math.max(...i));
	}
	return r == null ? [] : jb(n.flatMap((t) => {
		var n = W(e, t.dataKey), i, a;
		if (Array.isArray(n)) {
			var o = Jy(n, 2);
			i = o[0], a = o[1];
		} else i = a = n;
		if (!(!U(i) || !U(a))) return [r - i, r + a];
	}));
}
var Ib = (e) => db(e, Zp(e), Qp(e)), Lb = R([Ib], (e) => e == null ? void 0 : e.dataKey), Rb = R([
	vb,
	Lf,
	Ib
], Kp), zb = (e, t, n, r) => {
	var i = t.reduce((e, t) => {
		if (t.stackId == null) return e;
		var n = e[t.stackId];
		return n == null && (n = []), n.push(t), e[t.stackId] = n, e;
	}, {});
	return Object.fromEntries(Object.entries(i).map((t) => {
		var i = Jy(t, 2), a = i[0], o = i[1], s = r ? [...o].reverse() : o;
		return [a, {
			stackedData: Ds(e, s.map(Gp), n),
			graphicalItems: s
		}];
	}));
}, Bb = R([
	Rb,
	vb,
	gp,
	_p
], zb), Vb = (e, t, n, r) => {
	var i = t.dataStartIndex, a = t.dataEndIndex;
	if (r == null && n !== "zAxis") return Ns(e, i, a);
}, Hb = R([lb], (e) => e.allowDataOverflow), Ub = (e) => {
	var t;
	if (e == null || !("domain" in e)) return eb;
	if (e.domain != null) return e.domain;
	if ("ticks" in e && e.ticks != null) {
		if (e.type === "number") {
			var n = jb(e.ticks);
			return [Math.min(...n), Math.max(...n)];
		}
		if (e.type === "category") return e.ticks.map(String);
	}
	return (t = e == null ? void 0 : e.domain) == null ? eb : t;
}, Wb = R([lb], Ub), Gb = R([Wb, Hb], Yf), Kb = R([
	Bb,
	Ff,
	Up,
	Gb
], Vb, { memoizeOptions: { resultEqualityCheck: Jp } }), qb = (e) => e.errorBars, Jb = (e, t, n) => e.flatMap((e) => t[e.id]).filter(Boolean).filter((e) => Pb(n, e)), Yb = function() {
	var e = [...arguments].filter(Boolean);
	if (e.length !== 0) {
		var t = e.flat();
		return [Math.min(...t), Math.max(...t)];
	}
}, Xb = function(e, t, n, r, i) {
	var a = arguments.length > 5 && arguments[5] !== void 0 ? arguments[5] : [], o, s;
	if (n.length > 0 && n.forEach((e) => {
		var n, c = e.data == null ? a : [...e.data], l = (n = r[e.id]) == null ? void 0 : n.filter((e) => Pb(i, e));
		c.forEach((n) => {
			var r, i = W(n, (r = t.dataKey) == null ? e.dataKey : r), a = Fb(n, i, l);
			if (a.length >= 2) {
				var c = Math.min(...a), u = Math.max(...a);
				(o == null || c < o) && (o = c), (s == null || u > s) && (s = u);
			}
			var d = Ab(i);
			d != null && (o = o == null ? d[0] : Math.min(o, d[0]), s = s == null ? d[1] : Math.max(s, d[1]));
		});
	}), (t == null ? void 0 : t.dataKey) != null && n.length === 0 && e.forEach((e) => {
		var n = Ab(W(e, t.dataKey));
		n != null && (o = o == null ? n[0] : Math.min(o, n[0]), s = s == null ? n[1] : Math.max(s, n[1]));
	}), U(o) && U(s)) return [o, s];
}, Zb = R([
	Tb,
	lb,
	bb,
	qb,
	Up,
	zf
], Xb, { memoizeOptions: { resultEqualityCheck: Jp } });
function Qb(e) {
	var t = e.value;
	if (qt(t) || t instanceof Date) return t;
}
var $b = (e, t, n) => {
	var r = e.map(Qb).filter((e) => e != null);
	return n && (t.dataKey == null || t.allowDuplicatedCategory && Zt(r)) ? Pf(0, e.length) : t.allowDuplicatedCategory ? r : Array.from(new Set(r));
}, ex = (e) => e.referenceElements.dots, tx = (e, t, n) => e.filter((e) => e.ifOverflow === "extendDomain").filter((e) => t === "xAxis" ? e.xAxisId === n : e.yAxisId === n), nx = R([
	ex,
	Up,
	Wp
], tx), rx = (e) => e.referenceElements.areas, ix = R([
	rx,
	Up,
	Wp
], tx), ax = (e) => e.referenceElements.lines, ox = R([
	ax,
	Up,
	Wp
], tx), sx = (e, t) => {
	if (e != null) {
		var n = jb(e.map((e) => t === "xAxis" ? e.x : e.y));
		if (n.length !== 0) return [Math.min(...n), Math.max(...n)];
	}
}, cx = R(nx, Up, sx), lx = (e, t) => {
	if (e != null) {
		var n = jb(e.flatMap((e) => [t === "xAxis" ? e.x1 : e.y1, t === "xAxis" ? e.x2 : e.y2]));
		if (n.length !== 0) return [Math.min(...n), Math.max(...n)];
	}
}, ux = R([ix, Up], lx);
function dx(e) {
	var t;
	if (e.x != null) return jb([e.x]);
	var n = (t = e.segment) == null ? void 0 : t.map((e) => e.x);
	return n == null || n.length === 0 ? [] : jb(n);
}
function fx(e) {
	var t;
	if (e.y != null) return jb([e.y]);
	var n = (t = e.segment) == null ? void 0 : t.map((e) => e.y);
	return n == null || n.length === 0 ? [] : jb(n);
}
var px = (e, t) => {
	if (e != null) {
		var n = e.flatMap((e) => t === "xAxis" ? dx(e) : fx(e));
		if (n.length !== 0) return [Math.min(...n), Math.max(...n)];
	}
}, mx = R(cx, R([ox, Up], px), ux, (e, t, n) => Yb(e, n, t)), hx = (e, t, n, r, i, a, o, s, c) => {
	if (n != null) return n;
	var l = o === "vertical" && s === "xAxis" || o === "horizontal" && s === "yAxis" ? Yb(r, a, i) : Yb(a, i), u = Xf(t, l, e.allowDataOverflow);
	return u == null && e.allowDataOverflow && l == null && c != null ? c : u;
}, gx = R([
	lb,
	Wb,
	Gb,
	Kb,
	Zb,
	mx,
	q,
	Up,
	R([lb], (e) => {
		if (!(e == null || e.type !== "number" || !("ticks" in e) || e.ticks == null)) {
			var t = jb(e.ticks);
			if (t.length !== 0) return [Math.min(...t), Math.max(...t)];
		}
	}, { memoizeOptions: { resultEqualityCheck: Jp } })
], hx, { memoizeOptions: { resultEqualityCheck: Jp } }), _x = [0, 1], vx = (e, t, n, r, i, a, o) => {
	if (!((e == null || n == null || n.length === 0) && o === void 0)) {
		var s = e.dataKey, c = e.type, l = ws(t, a);
		if (l && s == null) {
			var u;
			return Pf(0, (u = n == null ? void 0 : n.length) == null ? 0 : u);
		}
		return c === "category" ? $b(r, e, l) : i === "expand" && !l ? _x : o;
	}
}, yx = R([
	lb,
	q,
	Tb,
	Ob,
	gp,
	Up,
	gx
], vx), bx = R([
	lb,
	fb,
	vp
], zy), xx = (e, t, n) => {
	var r = t.niceTicks;
	if (r !== "none") {
		var i = Ub(t), a = Array.isArray(i) && (i[0] === "auto" || i[1] === "auto");
		if ((r === "snap125" || r === "adaptive") && t != null && t.tickCount && qf(e)) {
			if (a) return up(e, t.tickCount, t.allowDecimals, r);
			if (t.type === "number") return dp(e, t.tickCount, t.allowDecimals, r);
		}
		if (r === "auto" && n === "linear" && t != null && t.tickCount) {
			if (a && qf(e)) return up(e, t.tickCount, t.allowDecimals, "adaptive");
			if (t.type === "number" && qf(e)) return dp(e, t.tickCount, t.allowDecimals, "adaptive");
		}
	}
}, Sx = R([
	yx,
	db,
	bx
], xx), Cx = (e, t, n, r) => {
	if (r !== "angleAxis" && (e == null ? void 0 : e.type) === "number" && qf(t) && Array.isArray(n) && n.length > 0) {
		var i, a, o = t[0], s = (i = n[0]) == null ? 0 : i, c = t[1], l = (a = n[n.length - 1]) == null ? 0 : a;
		return [Math.min(o, s), Math.max(c, l)];
	}
	return t;
}, wx = R([
	lb,
	yx,
	Sx,
	Up
], Cx), Tx = R(R(Ob, lb, (e, t) => {
	if (!(!t || t.type !== "number")) {
		var n = Infinity, r = Array.from(jb(e.map((e) => e.value))).sort((e, t) => e - t), i = r[0], a = r[r.length - 1];
		if (i == null || a == null) return Infinity;
		var o = a - i;
		if (o === 0) return Infinity;
		for (var s = 0; s < r.length - 1; s++) {
			var c = r[s], l = r[s + 1];
			if (!(c == null || l == null)) {
				var u = l - c;
				n = Math.min(n, u);
			}
		}
		return n / o;
	}
}), q, mp, ic, (e, t, n, r, i) => i, (e, t, n, r, i) => {
	if (!U(e)) return 0;
	var a = t === "vertical" ? r.height : r.width;
	if (i === "gap") return e * a / 2;
	if (i === "no-gap") {
		var o = Xt(n, e * a), s = e * a / 2;
		return s - o - (s - o) / a * o;
	}
	return 0;
}), Ex = (e, t, n) => {
	var r = rb(e, t);
	return r == null || typeof r.padding != "string" ? 0 : Tx(e, "xAxis", t, n, r.padding);
}, Dx = (e, t, n) => {
	var r = ob(e, t);
	return r == null || typeof r.padding != "string" ? 0 : Tx(e, "yAxis", t, n, r.padding);
}, Ox = R(rb, Ex, (e, t) => {
	var n, r;
	if (e == null) return {
		left: 0,
		right: 0
	};
	var i = e.padding;
	return typeof i == "string" ? {
		left: t,
		right: t
	} : {
		left: ((n = i.left) == null ? 0 : n) + t,
		right: ((r = i.right) == null ? 0 : r) + t
	};
}), kx = R(ob, Dx, (e, t) => {
	var n, r;
	if (e == null) return {
		top: 0,
		bottom: 0
	};
	var i = e.padding;
	return typeof i == "string" ? {
		top: t,
		bottom: t
	} : {
		top: ((n = i.top) == null ? 0 : n) + t,
		bottom: ((r = i.bottom) == null ? 0 : r) + t
	};
}), Ax = R([
	ic,
	Ox,
	uc,
	lc,
	(e, t, n) => n
], (e, t, n, r, i) => {
	var a = r.padding;
	return i ? [a.left, n.width - a.right] : [e.left + t.left, e.left + e.width - t.right];
}), jx = R([
	ic,
	q,
	kx,
	uc,
	lc,
	(e, t, n) => n
], (e, t, n, r, i, a) => {
	var o = i.padding;
	return a ? [r.height - o.bottom, o.top] : t === "horizontal" ? [e.top + e.height - n.bottom, e.top + n.top] : [e.top + n.top, e.top + e.height - n.bottom];
}), Mx = (e, t, n, r) => {
	var i;
	switch (t) {
		case "xAxis": return Ax(e, n, r);
		case "yAxis": return jx(e, n, r);
		case "zAxis": return (i = cb(e, n)) == null ? void 0 : i.range;
		case "angleAxis": return Bp(e);
		case "radiusAxis": return Vp(e, n);
		default: return;
	}
}, Nx = R([lb, Mx], Tp), Px = R([
	lb,
	bx,
	R([bx, wx], em),
	Nx
], Iy), Fx = (e, t, n, r) => {
	if (!(n == null || n.dataKey == null)) {
		var i = n.type, a = n.scale;
		if (ws(e, r) && (i === "number" || a !== "auto")) return t.map((e) => e.value);
	}
}, Ix = R([
	q,
	Ob,
	db,
	Up
], Fx), Lx = R([Px], $p);
R([Px], Hy), R([Px, Nb], Vy), R([
	_b,
	qb,
	Up
], Jb);
function Rx(e, t) {
	return e.id < t.id ? -1 : +(e.id > t.id);
}
var zx = (e, t) => t, Bx = (e, t, n) => n, Vx = R(Gs, zx, Bx, (e, t, n) => e.filter((e) => e.orientation === t).filter((e) => e.mirror === n).sort(Rx)), Hx = R(Ks, zx, Bx, (e, t, n) => e.filter((e) => e.orientation === t).filter((e) => e.mirror === n).sort(Rx)), Ux = (e, t) => ({
	width: e.width,
	height: t.height
}), Wx = (e, t) => ({
	width: typeof t.width == "number" ? t.width : 60,
	height: e.height
}), Gx = R(ic, rb, Ux), Kx = (e, t, n) => {
	switch (t) {
		case "top": return e.top;
		case "bottom": return n - e.bottom;
		default: return 0;
	}
}, qx = (e, t, n) => {
	switch (t) {
		case "left": return e.left;
		case "right": return n - e.right;
		default: return 0;
	}
}, Jx = R(Hs, ic, Vx, zx, Bx, (e, t, n, r, i) => {
	var a = {}, o;
	return n.forEach((n) => {
		var s = Ux(t, n);
		o == null && (o = Kx(t, r, e));
		var c = r === "top" && !i || r === "bottom" && i;
		a[n.id] = o - Number(c) * s.height, o += (c ? -1 : 1) * s.height;
	}), a;
}), Yx = R(Vs, ic, Hx, zx, Bx, (e, t, n, r, i) => {
	var a = {}, o;
	return n.forEach((n) => {
		var s = Wx(t, n);
		o == null && (o = qx(t, r, e));
		var c = r === "left" && !i || r === "right" && i;
		a[n.id] = o - Number(c) * s.width, o += (c ? -1 : 1) * s.width;
	}), a;
}), Xx = R([
	ic,
	rb,
	(e, t) => {
		var n = rb(e, t);
		if (n != null) return Jx(e, n.orientation, n.mirror);
	},
	(e, t) => t
], (e, t, n, r) => {
	if (t != null) {
		var i = n == null ? void 0 : n[r];
		return i == null ? {
			x: e.left,
			y: 0
		} : {
			x: e.left,
			y: i
		};
	}
}), Zx = R([
	ic,
	ob,
	(e, t) => {
		var n = ob(e, t);
		if (n != null) return Yx(e, n.orientation, n.mirror);
	},
	(e, t) => t
], (e, t, n, r) => {
	if (t != null) {
		var i = n == null ? void 0 : n[r];
		return i == null ? {
			x: 0,
			y: e.top
		} : {
			x: i,
			y: e.top
		};
	}
}), Qx = R(ic, ob, (e, t) => ({
	width: typeof t.width == "number" ? t.width : 60,
	height: e.height
})), $x = (e, t, n) => {
	switch (t) {
		case "xAxis": return Gx(e, n).width;
		case "yAxis": return Qx(e, n).height;
		default: return;
	}
}, eS = (e, t, n, r) => {
	if (n != null) {
		var i = n.allowDuplicatedCategory, a = n.type, o = n.dataKey, s = ws(e, r), c = t.map((e) => e.value), l = c.filter((e) => e != null);
		if (o && s && a === "category" && i && Zt(l)) return c;
	}
}, tS = R([
	q,
	Ob,
	lb,
	Up
], eS);
R([
	q,
	ub,
	bx,
	Lx,
	tS,
	Ix,
	Mx,
	Sx,
	Up
], (e, t, n, r, i, a, o, s, c) => {
	if (t != null) {
		var l = ws(e, c);
		return {
			angle: t.angle,
			interval: t.interval,
			minTickGap: t.minTickGap,
			orientation: t.orientation,
			tick: t.tick,
			tickCount: t.tickCount,
			tickFormatter: t.tickFormatter,
			ticks: t.ticks,
			type: t.type,
			unit: t.unit,
			axisType: c,
			categoricalDomain: a,
			duplicateDomain: i,
			isCategorical: l,
			niceTicks: s,
			range: o,
			realScaleType: n,
			scale: r
		};
	}
});
var nS = R([
	q,
	db,
	bx,
	Lx,
	Sx,
	Mx,
	tS,
	Ix,
	Up
], (e, t, n, r, i, a, o, s, c) => {
	if (!(t == null || r == null)) {
		var l = ws(e, c), u = t.type, d = t.ticks, f = t.tickCount, p = n === "scaleBand" && typeof r.bandwidth == "function" ? r.bandwidth() / 2 : 2, m = u === "category" && r.bandwidth ? r.bandwidth() / p : 0;
		m = c === "angleAxis" && a != null && a.length >= 2 ? Gt(a[0] - a[1]) * 2 * m : m;
		var h = d || i;
		return h ? h.map((e, t) => {
			var n = o ? o.indexOf(e) : e, i = r.map(n);
			return U(i) ? {
				index: t,
				coordinate: i + m,
				value: e,
				offset: m
			} : null;
		}).filter(nn) : l && s ? s.map((e, t) => {
			var n = r.map(e);
			return U(n) ? {
				coordinate: n + m,
				value: e,
				index: t,
				offset: m
			} : null;
		}).filter(nn) : r.ticks ? r.ticks(f).map((e, t) => {
			var n = r.map(e);
			return U(n) ? {
				coordinate: n + m,
				value: e,
				index: t,
				offset: m
			} : null;
		}).filter(nn) : r.domain().map((e, t) => {
			var n = r.map(e);
			return U(n) ? {
				coordinate: n + m,
				value: o ? o[e] : e,
				index: t,
				offset: m
			} : null;
		}).filter(nn);
	}
}), rS = R([
	q,
	db,
	Lx,
	Mx,
	tS,
	Ix,
	Up
], (e, t, n, r, i, a, o) => {
	if (!(t == null || n == null || r == null || r[0] === r[1])) {
		var s = ws(e, o), c = t.tickCount, l = 0;
		return l = o === "angleAxis" && (r == null ? void 0 : r.length) >= 2 ? Gt(r[0] - r[1]) * 2 * l : l, s && a ? a.map((e, t) => {
			var r = n.map(e);
			return U(r) ? {
				coordinate: r + l,
				value: e,
				index: t,
				offset: l
			} : null;
		}).filter(nn) : n.ticks ? n.ticks(c).map((e, t) => {
			var r = n.map(e);
			return U(r) ? {
				coordinate: r + l,
				value: e,
				index: t,
				offset: l
			} : null;
		}).filter(nn) : n.domain().map((e, t) => {
			var r = n.map(e);
			return U(r) ? {
				coordinate: r + l,
				value: i ? i[e] : e,
				index: t,
				offset: l
			} : null;
		}).filter(nn);
	}
}), iS = R(lb, Lx, (e, t) => {
	if (!(e == null || t == null)) return Wy(Wy({}, e), {}, { scale: t });
});
R((e, t, n) => cb(e, n), R([R([
	lb,
	bx,
	yx,
	Nx
], Iy)], $p), (e, t) => {
	if (!(e == null || t == null)) return Wy(Wy({}, e), {}, { scale: t });
});
var aS = R([
	q,
	Gs,
	Ks
], (e, t, n) => {
	switch (e) {
		case "horizontal": return t.some((e) => e.reversed) ? "right-to-left" : "left-to-right";
		case "vertical": return n.some((e) => e.reversed) ? "bottom-to-top" : "top-to-bottom";
		case "centric":
		case "radial": return "left-to-right";
		default: return;
	}
});
R([(e, t, n) => {
	var r;
	return (r = e.renderedTicks[t]) == null ? void 0 : r[n];
}], (e) => {
	if (!(!e || e.length === 0)) return (t) => {
		var n, r = Infinity, i = e[0];
		for (var a of e) {
			var o = Math.abs(a.coordinate - t);
			o < r && (r = o, i = a);
		}
		return (n = i) == null ? void 0 : n.value;
	};
});
//#endregion
//#region node_modules/recharts/es6/state/selectors/selectTooltipEventType.js
var oS = (e) => e.options.defaultTooltipEventType, sS = (e) => e.options.validateTooltipEventTypes;
function cS(e, t, n) {
	if (e == null) return t;
	var r = e ? "axis" : "item";
	return n == null ? t : n.includes(r) ? r : t;
}
function lS(e, t) {
	return cS(t, oS(e), sS(e));
}
function uS(e) {
	return L((t) => lS(t, e));
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineActiveLabel.js
var dS = (e, t) => {
	var n, r = Number(t);
	if (!(Kt(r) || t == null)) return r >= 0 ? e == null || (n = e[r]) == null ? void 0 : n.value : void 0;
}, fS = (e) => e.tooltip.settings, pS = {
	active: !1,
	index: null,
	dataKey: void 0,
	graphicalItemId: void 0,
	coordinate: void 0
}, mS = xo({
	name: "tooltip",
	initialState: {
		itemInteraction: {
			click: pS,
			hover: pS
		},
		axisInteraction: {
			click: pS,
			hover: pS
		},
		keyboardInteraction: pS,
		syncInteraction: {
			active: !1,
			index: null,
			dataKey: void 0,
			label: void 0,
			coordinate: void 0,
			sourceViewBox: void 0,
			graphicalItemId: void 0
		},
		tooltipItemPayloads: [],
		settings: {
			shared: void 0,
			trigger: "hover",
			axisId: 0,
			active: !1,
			defaultIndex: void 0
		}
	},
	reducers: {
		addTooltipEntrySettings: {
			reducer(e, t) {
				e.tooltipItemPayloads.push(H(t.payload));
			},
			prepare: ao()
		},
		replaceTooltipEntrySettings: {
			reducer(e, t) {
				var n = t.payload, r = n.prev, i = n.next, a = Ga(e).tooltipItemPayloads.indexOf(H(r));
				a > -1 && (e.tooltipItemPayloads[a] = H(i));
			},
			prepare: ao()
		},
		removeTooltipEntrySettings: {
			reducer(e, t) {
				var n = Ga(e).tooltipItemPayloads.indexOf(H(t.payload));
				n > -1 && e.tooltipItemPayloads.splice(n, 1);
			},
			prepare: ao()
		},
		setTooltipSettingsState(e, t) {
			e.settings = t.payload;
		},
		setActiveMouseOverItemIndex(e, t) {
			e.syncInteraction.active = !1, e.syncInteraction.sourceViewBox = void 0, e.keyboardInteraction.active = !1, e.itemInteraction.hover.active = !0, e.itemInteraction.hover.index = t.payload.activeIndex, e.itemInteraction.hover.dataKey = t.payload.activeDataKey, e.itemInteraction.hover.graphicalItemId = t.payload.activeGraphicalItemId, e.itemInteraction.hover.coordinate = t.payload.activeCoordinate;
		},
		mouseLeaveChart(e) {
			e.itemInteraction.hover.active = !1, e.axisInteraction.hover.active = !1;
		},
		mouseLeaveItem(e) {
			e.itemInteraction.hover.active = !1;
		},
		setActiveClickItemIndex(e, t) {
			e.syncInteraction.active = !1, e.syncInteraction.sourceViewBox = void 0, e.itemInteraction.click.active = !0, e.keyboardInteraction.active = !1, e.itemInteraction.click.index = t.payload.activeIndex, e.itemInteraction.click.dataKey = t.payload.activeDataKey, e.itemInteraction.click.graphicalItemId = t.payload.activeGraphicalItemId, e.itemInteraction.click.coordinate = t.payload.activeCoordinate;
		},
		setMouseOverAxisIndex(e, t) {
			e.syncInteraction.active = !1, e.syncInteraction.sourceViewBox = void 0, e.axisInteraction.hover.active = !0, e.keyboardInteraction.active = !1, e.axisInteraction.hover.index = t.payload.activeIndex, e.axisInteraction.hover.dataKey = t.payload.activeDataKey, e.axisInteraction.hover.coordinate = t.payload.activeCoordinate;
		},
		setMouseClickAxisIndex(e, t) {
			e.syncInteraction.active = !1, e.syncInteraction.sourceViewBox = void 0, e.keyboardInteraction.active = !1, e.axisInteraction.click.active = !0, e.axisInteraction.click.index = t.payload.activeIndex, e.axisInteraction.click.dataKey = t.payload.activeDataKey, e.axisInteraction.click.coordinate = t.payload.activeCoordinate;
		},
		setSyncInteraction(e, t) {
			e.syncInteraction = t.payload;
		},
		setKeyboardInteraction(e, t) {
			e.keyboardInteraction.active = t.payload.active, e.keyboardInteraction.index = t.payload.activeIndex, e.keyboardInteraction.coordinate = t.payload.activeCoordinate;
		}
	}
}), hS = mS.actions, gS = hS.addTooltipEntrySettings, _S = hS.replaceTooltipEntrySettings, vS = hS.removeTooltipEntrySettings, yS = hS.setTooltipSettingsState, bS = hS.setActiveMouseOverItemIndex, xS = hS.mouseLeaveItem, SS = hS.mouseLeaveChart, CS = hS.setActiveClickItemIndex, wS = hS.setMouseOverAxisIndex, TS = hS.setMouseClickAxisIndex, ES = hS.setSyncInteraction, DS = hS.setKeyboardInteraction, OS = mS.reducer;
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineTooltipInteractionState.js
function kS(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function AS(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? kS(Object(n), !0).forEach(function(t) {
			jS(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : kS(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function jS(e, t, n) {
	return (t = MS(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function MS(e) {
	var t = NS(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function NS(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function PS(e, t, n) {
	return t === "axis" ? n === "click" ? e.axisInteraction.click : e.axisInteraction.hover : n === "click" ? e.itemInteraction.click : e.itemInteraction.hover;
}
function FS(e) {
	return e.index != null;
}
var IS = (e, t, n, r) => {
	if (t == null) return pS;
	var i = PS(e, t, n);
	if (i == null) return pS;
	if (i.active) return i;
	if (e.keyboardInteraction.active) return e.keyboardInteraction;
	if (e.syncInteraction.active && e.syncInteraction.index != null) return e.syncInteraction;
	var a = e.settings.active === !0;
	if (FS(i)) {
		if (a) return AS(AS({}, i), {}, { active: !0 });
	} else if (r != null) return {
		active: !0,
		coordinate: void 0,
		dataKey: void 0,
		index: r,
		graphicalItemId: void 0
	};
	return AS(AS({}, pS), {}, { coordinate: i.coordinate });
};
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineActiveTooltipIndex.js
function LS(e) {
	if (typeof e == "number") return Number.isFinite(e) ? e : void 0;
	if (e instanceof Date) {
		var t = e.valueOf();
		return Number.isFinite(t) ? t : void 0;
	}
	var n = Number(e);
	return Number.isFinite(n) ? n : void 0;
}
function RS(e, t) {
	var n = LS(e), r = t[0], i = t[1];
	return n !== void 0 && n >= Math.min(r, i) && n <= Math.max(r, i);
}
function zS(e, t, n) {
	if (n == null || t == null) return !0;
	var r = W(e, t);
	return r == null || !qf(n) || RS(r, n);
}
var BS = (e, t, n, r) => {
	var i = e == null ? void 0 : e.index;
	if (i == null) return null;
	var a = Number(i);
	if (!U(a)) return i;
	var o = 0, s = Infinity;
	t.length > 0 && (s = t.length - 1);
	var c = Math.max(o, Math.min(a, s)), l = t[c];
	return l == null || zS(l, n, r) ? String(c) : null;
}, VS = (e, t, n, r, i, a, o) => {
	if (a != null) {
		var s = o[0], c = s == null ? void 0 : s.getPosition(a);
		if (c != null) return c;
		var l = i == null ? void 0 : i[Number(a)];
		if (l) switch (n) {
			case "horizontal": return {
				x: l.coordinate,
				y: (r.top + t) / 2
			};
			default: return {
				x: (r.left + e) / 2,
				y: l.coordinate
			};
		}
	}
}, HS = (e, t, n, r) => {
	if (t === "axis") return e.tooltipItemPayloads;
	if (e.tooltipItemPayloads.length === 0) return [];
	var i = n === "hover" ? e.itemInteraction.hover.graphicalItemId : e.itemInteraction.click.graphicalItemId;
	if (e.syncInteraction.active && i == null) return e.tooltipItemPayloads;
	if (i == null && (r != null || e.keyboardInteraction.active)) {
		var a = e.tooltipItemPayloads[0];
		return a == null ? [] : [a];
	}
	return e.tooltipItemPayloads.filter((e) => {
		var t;
		return ((t = e.settings) == null ? void 0 : t.graphicalItemId) === i;
	});
}, US = (e) => e.options.tooltipPayloadSearcher, WS = (e) => e.tooltip;
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineTooltipPayload.js
function GS(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function KS(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? GS(Object(n), !0).forEach(function(t) {
			qS(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : GS(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function qS(e, t, n) {
	return (t = JS(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function JS(e) {
	var t = YS(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function YS(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function XS(e) {
	if (typeof e == "string" || typeof e == "number") return e;
}
function ZS(e) {
	if (typeof e == "string" || typeof e == "number" || typeof e == "boolean") return e;
}
function QS(e) {
	if (typeof e == "string" || typeof e == "number") return e;
	if (typeof e == "function") return (t) => e(t);
}
function $S(e) {
	if (typeof e == "string") return e;
}
function eC(e) {
	if (!(typeof e != "object" || !e)) return {
		name: "name" in e ? XS(e.name) : void 0,
		unit: "unit" in e ? ZS(e.unit) : void 0,
		dataKey: "dataKey" in e ? QS(e.dataKey) : void 0,
		payload: "payload" in e ? e.payload : void 0,
		color: "color" in e ? $S(e.color) : void 0,
		fill: "fill" in e ? $S(e.fill) : void 0
	};
}
function tC(e, t) {
	return e == null ? t : e;
}
var nC = (e, t, n, r, i, a, o) => {
	if (!(t == null || a == null)) {
		var s = n.chartData, c = n.computedData, l = n.dataStartIndex, u = n.dataEndIndex;
		return e.reduce((e, n) => {
			var d, f = n.dataDefinedOnItem, p = n.settings, m = tC(f, s), h = Array.isArray(m) ? gs(m, l, u) : m, g = (d = p == null ? void 0 : p.dataKey) == null ? r : d, _ = p == null ? void 0 : p.nameKey, v = r && Array.isArray(h) && !Array.isArray(h[0]) && o === "axis" ? $t(h, r, i) : a(h, t, c, _);
			if (Array.isArray(v)) v.forEach((t) => {
				var n, r, i = eC(t), a = i == null ? void 0 : i.name, o = i == null ? void 0 : i.dataKey, s = i == null ? void 0 : i.payload, c = KS(KS({}, p), {}, {
					name: a,
					unit: i == null ? void 0 : i.unit,
					color: (n = i == null ? void 0 : i.color) == null ? p == null ? void 0 : p.color : n,
					fill: (r = i == null ? void 0 : i.fill) == null ? p == null ? void 0 : p.fill : r
				});
				e.push(Ls({
					tooltipEntrySettings: c,
					dataKey: o,
					payload: s,
					value: W(s, o),
					name: a == null ? void 0 : String(a)
				}));
			});
			else {
				var y;
				e.push(Ls({
					tooltipEntrySettings: p,
					dataKey: g,
					payload: v,
					value: W(v, g),
					name: (y = W(v, _)) == null ? p == null ? void 0 : p.name : y
				}));
			}
			return e;
		}, []);
	}
}, rC = R([
	Ib,
	fb,
	vp
], zy), iC = R([
	R([(e) => e.graphicalItems.cartesianItems, (e) => e.graphicalItems.polarItems], (e, t) => [...e, ...t]),
	Ib,
	R([Zp, Qp], pb)
], gb, { memoizeOptions: { resultEqualityCheck: Yp } }), aC = R([iC], (e) => e.filter(qp)), oC = R([iC], xb, { memoizeOptions: { resultEqualityCheck: Yp } }), sC = R([iC], (e) => e.some((e) => !e.data)), cC = R([oC, Ff], wb), lC = R([
	aC,
	Ff,
	Ib
], Kp), uC = R([
	cC,
	Ib,
	iC,
	Ff,
	sC,
	oC
], Db), dC = R([Ib], Ub), fC = R([dC, R([Ib], (e) => e.allowDataOverflow)], Yf), pC = R([
	R([
		lC,
		R([iC], (e) => e.filter(qp)),
		gp,
		_p
	], zb),
	Ff,
	Zp,
	fC
], Vb), mC = R([
	cC,
	Ib,
	R([iC], yb),
	qb,
	Zp,
	Bf
], Xb, { memoizeOptions: { resultEqualityCheck: Jp } }), hC = R([R([
	ex,
	Zp,
	Qp
], tx), Zp], sx), gC = R([R([
	rx,
	Zp,
	Qp
], tx), Zp], lx), _C = R([
	Ib,
	q,
	cC,
	uC,
	gp,
	Zp,
	R([
		Ib,
		dC,
		fC,
		pC,
		mC,
		R([
			hC,
			R([R([
				ax,
				Zp,
				Qp
			], tx), Zp], px),
			gC
		], Yb),
		q,
		Zp
	], hx)
], vx), vC = R([
	Ib,
	_C,
	R([
		_C,
		Ib,
		rC
	], xx),
	Zp
], Cx), yC = (e) => Mx(e, Zp(e), Qp(e), !1), bC = R([Ib, yC], Tp), xC = R([R([
	Ib,
	rC,
	vC,
	bC
], Iy)], $p), SC = R([
	q,
	Ib,
	rC,
	xC,
	yC,
	R([
		q,
		uC,
		Ib,
		Zp
	], eS),
	R([
		q,
		uC,
		Ib,
		Zp
	], Fx),
	Zp
], (e, t, n, r, i, a, o, s) => {
	if (t) {
		var c = t.type, l = ws(e, s);
		if (r) {
			var u = n === "scaleBand" && r.bandwidth ? r.bandwidth() / 2 : 2, d = c === "category" && r.bandwidth ? r.bandwidth() / u : 0;
			return d = s === "angleAxis" && i != null && (i == null ? void 0 : i.length) >= 2 ? Gt(i[0] - i[1]) * 2 * d : d, l && o ? o.map((e, t) => {
				var n = r.map(e);
				return U(n) ? {
					coordinate: n + d,
					value: e,
					index: t,
					offset: d
				} : null;
			}).filter(nn) : r.domain().map((e, t) => {
				var n = r.map(e);
				return U(n) ? {
					coordinate: n + d,
					value: a ? a[e] : e,
					index: t,
					offset: d
				} : null;
			}).filter(nn);
		}
	}
}), CC = R([
	oS,
	sS,
	fS
], (e, t, n) => cS(n.shared, e, t)), wC = (e) => e.tooltip.settings.trigger, TC = (e) => e.tooltip.settings.defaultIndex, EC = R([
	WS,
	CC,
	wC,
	TC
], IS), DC = R([
	EC,
	cC,
	Lb,
	_C
], BS), OC = R([SC, DC], dS), kC = R([EC], (e) => {
	if (e) return e.dataKey;
}), AC = R([EC], (e) => {
	if (e) return e.graphicalItemId;
}), jC = R([
	WS,
	CC,
	wC,
	TC
], HS), MC = R([EC, R([
	Vs,
	Hs,
	q,
	ic,
	SC,
	TC,
	jC
], VS)], (e, t) => e != null && e.coordinate ? e.coordinate : t), NC = R([EC], (e) => {
	var t;
	return (t = e == null ? void 0 : e.active) != null && t;
});
R([R([
	jC,
	DC,
	Ff,
	Lb,
	OC,
	US,
	CC
], nC)], (e) => {
	if (e != null) {
		var t = e.map((e) => e.payload).filter((e) => e != null);
		return Array.from(new Set(t));
	}
});
//#endregion
//#region node_modules/recharts/es6/context/useTooltipAxis.js
function PC(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function FC(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? PC(Object(n), !0).forEach(function(t) {
			IC(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : PC(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function IC(e, t, n) {
	return (t = LC(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function LC(e) {
	var t = RC(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function RC(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var zC = () => L(Ib), BC = () => {
	var e = zC(), t = L(SC), n = L(xC);
	return Is(!e || !n ? void 0 : FC(FC({}, e), {}, { scale: n }), t);
};
//#endregion
//#region node_modules/recharts/es6/util/getActiveCoordinate.js
function VC(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function HC(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? VC(Object(n), !0).forEach(function(t) {
			UC(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : VC(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function UC(e, t, n) {
	return (t = WC(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function WC(e) {
	var t = GC(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function GC(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var KC = (e, t, n, r) => {
	var i = t.find((e) => e && e.index === n);
	if (i) {
		if (e === "horizontal") return {
			x: i.coordinate,
			y: r.relativeY
		};
		if (e === "vertical") return {
			x: r.relativeX,
			y: i.coordinate
		};
	}
	return {
		x: 0,
		y: 0
	};
}, qC = (e, t, n, r) => {
	var i = t.find((e) => e && e.index === n);
	if (i) {
		if (e === "centric") {
			var a = i.coordinate, o = r.radius;
			return HC(HC(HC({}, r), cf(r.cx, r.cy, o, a)), {}, {
				angle: a,
				radius: o
			});
		}
		var s = i.coordinate, c = r.angle;
		return HC(HC(HC({}, r), cf(r.cx, r.cy, s, c)), {}, {
			angle: c,
			radius: s
		});
	}
	return {
		angle: 0,
		clockWise: !1,
		cx: 0,
		cy: 0,
		endAngle: 0,
		innerRadius: 0,
		outerRadius: 0,
		radius: 0,
		startAngle: 0,
		x: 0,
		y: 0
	};
};
function JC(e, t) {
	var n = e.relativeX, r = e.relativeY;
	return n >= t.left && n <= t.left + t.width && r >= t.top && r <= t.top + t.height;
}
var YC = (e, t, n, r, i) => {
	var a, o = (a = t == null ? void 0 : t.length) == null ? 0 : a;
	if (o <= 1 || e == null) return 0;
	if (r === "angleAxis" && i != null && Math.abs(Math.abs(i[1] - i[0]) - 360) <= 1e-6) for (var s = 0; s < o; s++) {
		var c, l, u, d, f, p = s > 0 ? (c = n[s - 1]) == null ? void 0 : c.coordinate : (l = n[o - 1]) == null ? void 0 : l.coordinate, m = (u = n[s]) == null ? void 0 : u.coordinate, h = s >= o - 1 ? (d = n[0]) == null ? void 0 : d.coordinate : (f = n[s + 1]) == null ? void 0 : f.coordinate, g = void 0;
		if (!(p == null || m == null || h == null)) if (Gt(m - p) !== Gt(h - m)) {
			var _ = [];
			if (Gt(h - m) === Gt(i[1] - i[0])) {
				g = h;
				var v = m + i[1] - i[0];
				_[0] = Math.min(v, (v + p) / 2), _[1] = Math.max(v, (v + p) / 2);
			} else {
				g = p;
				var y = h + i[1] - i[0];
				_[0] = Math.min(m, (y + m) / 2), _[1] = Math.max(m, (y + m) / 2);
			}
			var b = [Math.min(m, (g + m) / 2), Math.max(m, (g + m) / 2)];
			if (e > b[0] && e <= b[1] || e >= _[0] && e <= _[1]) {
				var x;
				return (x = n[s]) == null ? void 0 : x.index;
			}
		} else {
			var S = Math.min(p, h), C = Math.max(p, h);
			if (e > (S + m) / 2 && e <= (C + m) / 2) {
				var w;
				return (w = n[s]) == null ? void 0 : w.index;
			}
		}
	}
	else if (t) for (var T = 0; T < o; T++) {
		var E = t[T];
		if (E != null) {
			var D = t[T + 1], O = t[T - 1];
			if (T === 0 && D != null && e <= (E.coordinate + D.coordinate) / 2 || T === o - 1 && O != null && e > (E.coordinate + O.coordinate) / 2 || T > 0 && T < o - 1 && O != null && D != null && e > (E.coordinate + O.coordinate) / 2 && e <= (E.coordinate + D.coordinate) / 2) return E.index;
		}
	}
	return -1;
}, XC = () => L(vp), ZC = (e, t) => t, QC = (e, t, n) => n, $C = (e, t, n, r) => r, ew = R(SC, (e) => ai(e, (e) => e.coordinate)), tw = R([
	WS,
	ZC,
	QC,
	$C
], IS), nw = R([
	tw,
	cC,
	Lb,
	_C
], BS), rw = (e, t, n) => {
	if (t != null) {
		var r = WS(e);
		return t === "axis" ? n === "hover" ? r.axisInteraction.hover.dataKey : r.axisInteraction.click.dataKey : n === "hover" ? r.itemInteraction.hover.dataKey : r.itemInteraction.click.dataKey;
	}
}, iw = R([
	WS,
	ZC,
	QC,
	$C
], HS), aw = R([
	Vs,
	Hs,
	q,
	ic,
	SC,
	$C,
	iw
], VS), ow = R([tw, aw], (e, t) => {
	var n;
	return (n = e.coordinate) == null ? t : n;
}), sw = R([SC, nw], dS), cw = R([
	iw,
	nw,
	Ff,
	Lb,
	sw,
	US,
	ZC
], nC), lw = R([tw, nw], (e, t) => ({
	isActive: e.active && t != null,
	activeIndex: t
})), uw = (e, t, n, r, i, a, o) => {
	if (!(!e || !n || !r || !i) && JC(e, o)) {
		var s = YC(zs(e, t), a, i, n, r), c = KC(t, i, s, e);
		return {
			activeIndex: String(s),
			activeCoordinate: c
		};
	}
}, dw = (e, t, n, r, i, a, o) => {
	if (!(!e || !r || !i || !a || !n)) {
		var s = mf(e, n);
		if (s) {
			var c = YC(Bs(s, t), o, a, r, i), l = qC(t, a, c, s);
			return {
				activeIndex: String(c),
				activeCoordinate: l
			};
		}
	}
}, fw = (e, t, n, r, i, a, o, s) => {
	if (!(!e || !t || !r || !i || !a)) return t === "horizontal" || t === "vertical" ? uw(e, t, r, i, a, o, s) : dw(e, t, n, r, i, a, o);
}, pw = R((e) => e.zIndex.zIndexMap, (e, t) => t, (e, t, n) => n, (e, t, n) => {
	if (t != null) {
		var r = e[t];
		if (r != null) return n ? r.panoramaElement : r.element;
	}
}), mw = R((e) => e.zIndex.zIndexMap, (e) => {
	var t = Object.keys(e).map((e) => parseInt(e, 10)).concat(Object.values(Sp));
	return Array.from(new Set(t)).sort((e, t) => e - t);
}, { memoizeOptions: { resultEqualityCheck: Xp } });
//#endregion
//#region node_modules/recharts/es6/state/zIndexSlice.js
function hw(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function gw(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? hw(Object(n), !0).forEach(function(t) {
			_w(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : hw(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function _w(e, t, n) {
	return (t = vw(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function vw(e) {
	var t = yw(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function yw(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var bw = { zIndexMap: Object.values(Sp).reduce((e, t) => gw(gw({}, e), {}, { [t]: {
	element: void 0,
	panoramaElement: void 0,
	consumers: 0
} }), {}) }, xw = new Set(Object.values(Sp));
function Sw(e) {
	return xw.has(e);
}
var Cw = xo({
	name: "zIndex",
	initialState: bw,
	reducers: {
		registerZIndexPortal: {
			reducer: (e, t) => {
				var n = t.payload.zIndex;
				e.zIndexMap[n] ? e.zIndexMap[n].consumers += 1 : e.zIndexMap[n] = {
					consumers: 1,
					element: void 0,
					panoramaElement: void 0
				};
			},
			prepare: ao()
		},
		unregisterZIndexPortal: {
			reducer: (e, t) => {
				var n = t.payload.zIndex;
				e.zIndexMap[n] && (--e.zIndexMap[n].consumers, e.zIndexMap[n].consumers <= 0 && !Sw(n) && delete e.zIndexMap[n]);
			},
			prepare: ao()
		},
		registerZIndexPortalElement: {
			reducer: (e, t) => {
				var n = t.payload, r = n.zIndex, i = n.element, a = n.isPanorama;
				e.zIndexMap[r] ? a ? e.zIndexMap[r].panoramaElement = H(i) : e.zIndexMap[r].element = H(i) : e.zIndexMap[r] = {
					consumers: 0,
					element: a ? void 0 : H(i),
					panoramaElement: a ? H(i) : void 0
				};
			},
			prepare: ao()
		},
		unregisterZIndexPortalElement: {
			reducer: (e, t) => {
				var n = t.payload.zIndex;
				e.zIndexMap[n] && (t.payload.isPanorama ? e.zIndexMap[n].panoramaElement = void 0 : e.zIndexMap[n].element = void 0);
			},
			prepare: ao()
		}
	}
}), ww = Cw.actions, Tw = ww.registerZIndexPortal, Ew = ww.unregisterZIndexPortal, Dw = ww.registerZIndexPortalElement, Ow = ww.unregisterZIndexPortalElement, kw = Cw.reducer, Aw = h();
function jw(e) {
	var t = e.zIndex, n = e.children, r = Zc() && t !== void 0 && t !== 0, i = cc(), a = (0, C.useRef)(void 0), o = (0, C.useRef)(/* @__PURE__ */ new Set()), s = kr(), c = L((e) => pw(e, t, i));
	if ((0, C.useLayoutEffect)(() => {
		if (!r) {
			var e = o.current;
			e.forEach((e) => {
				s(Ew({ zIndex: e }));
			}), e.clear(), a.current = void 0;
			return;
		}
		if (o.current.has(t) || (s(Tw({ zIndex: t })), o.current.add(t)), c) {
			a.current = c;
			var n = o.current;
			n.forEach((e) => {
				e !== t && (s(Ew({ zIndex: e })), n.delete(e));
			});
		}
	}, [
		s,
		t,
		r,
		c
	]), (0, C.useLayoutEffect)(() => {
		var e = o.current;
		return () => {
			e.forEach((e) => {
				s(Ew({ zIndex: e }));
			}), e.clear();
		};
	}, [s]), !r) return n;
	var l = c == null ? a.current : c;
	return l ? /*#__PURE__*/ (0, Aw.createPortal)(n, l) : null;
}
//#endregion
//#region node_modules/recharts/es6/component/Cursor.js
function Mw() {
	return Mw = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, Mw.apply(null, arguments);
}
function Nw(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Pw(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Nw(Object(n), !0).forEach(function(t) {
			Fw(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Nw(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Fw(e, t, n) {
	return (t = Iw(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function Iw(e) {
	var t = Lw(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Lw(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function Rw(e) {
	var t = e.cursor, n = e.cursorComp, r = e.cursorProps;
	return /*#__PURE__*/ (0, C.isValidElement)(t) ? /*#__PURE__*/ (0, C.cloneElement)(t, r) : /*#__PURE__*/ (0, C.createElement)(n, r);
}
function zw(e) {
	var t, n = e.coordinate, r = e.payload, i = e.index, a = e.offset, o = e.tooltipAxisBandSize, s = e.layout, c = e.cursor, l = e.tooltipEventType, u = e.chartName, d = n, f = r, p = i;
	if (!c || !d || u !== "ScatterChart" && l !== "axis") return null;
	var m, h, g;
	if (u === "ScatterChart") m = d, h = Bu, g = Sp.cursorLine;
	else if (u === "BarChart") m = Vu(s, d, a, o), h = $d, g = Sp.cursorRectangle;
	else if (s === "radial" && an(d)) {
		var _ = hf(d), v = _.cx, y = _.cy, b = _.radius;
		m = {
			cx: v,
			cy: y,
			startAngle: _.startAngle,
			endAngle: _.endAngle,
			innerRadius: b,
			outerRadius: b
		}, h = Af, g = Sp.cursorLine;
	} else m = { points: jf(s, d, a) }, h = ku, g = Sp.cursorLine;
	var x = typeof c == "object" && "className" in c ? c.className : void 0, S = Pw(Pw(Pw(Pw({
		stroke: "#ccc",
		pointerEvents: "none"
	}, a), m), Se(c)), {}, {
		payload: f,
		payloadIndex: p,
		className: he("recharts-tooltip-cursor", x)
	});
	return /*#__PURE__*/ C.createElement(jw, { zIndex: (t = e.zIndex) == null ? g : t }, /*#__PURE__*/ C.createElement(Rw, {
		cursor: c,
		cursorComp: h,
		cursorProps: S
	}));
}
function Bw(e) {
	var t = BC(), n = Kc(), r = Jc(), i = XC();
	return t == null || n == null || r == null || i == null ? null : /*#__PURE__*/ C.createElement(zw, Mw({}, e, {
		offset: n,
		layout: r,
		tooltipAxisBandSize: t,
		chartName: i
	}));
}
//#endregion
//#region node_modules/recharts/es6/context/tooltipPortalContext.js
var Vw = /*#__PURE__*/ (0, C.createContext)(null), Hw = () => (0, C.useContext)(Vw), Uw = (/* @__PURE__ */ l((/* @__PURE__ */ o(((e, t) => {
	var n = Object.prototype.hasOwnProperty, r = "~";
	function i() {}
	Object.create && (i.prototype = Object.create(null), new i().__proto__ || (r = !1));
	function a(e, t, n) {
		this.fn = e, this.context = t, this.once = n || !1;
	}
	function o(e, t, n, i, o) {
		if (typeof n != "function") throw TypeError("The listener must be a function");
		var s = new a(n, i || e, o), c = r ? r + t : t;
		return e._events[c] ? e._events[c].fn ? e._events[c] = [e._events[c], s] : e._events[c].push(s) : (e._events[c] = s, e._eventsCount++), e;
	}
	function s(e, t) {
		--e._eventsCount === 0 ? e._events = new i() : delete e._events[t];
	}
	function c() {
		this._events = new i(), this._eventsCount = 0;
	}
	c.prototype.eventNames = function() {
		var e = [], t, i;
		if (this._eventsCount === 0) return e;
		for (i in t = this._events) n.call(t, i) && e.push(r ? i.slice(1) : i);
		return Object.getOwnPropertySymbols ? e.concat(Object.getOwnPropertySymbols(t)) : e;
	}, c.prototype.listeners = function(e) {
		var t = r ? r + e : e, n = this._events[t];
		if (!n) return [];
		if (n.fn) return [n.fn];
		for (var i = 0, a = n.length, o = Array(a); i < a; i++) o[i] = n[i].fn;
		return o;
	}, c.prototype.listenerCount = function(e) {
		var t = r ? r + e : e, n = this._events[t];
		return n ? n.fn ? 1 : n.length : 0;
	}, c.prototype.emit = function(e, t, n, i, a, o) {
		var s = r ? r + e : e;
		if (!this._events[s]) return !1;
		var c = this._events[s], l = arguments.length, u, d;
		if (c.fn) {
			switch (c.once && this.removeListener(e, c.fn, void 0, !0), l) {
				case 1: return c.fn.call(c.context), !0;
				case 2: return c.fn.call(c.context, t), !0;
				case 3: return c.fn.call(c.context, t, n), !0;
				case 4: return c.fn.call(c.context, t, n, i), !0;
				case 5: return c.fn.call(c.context, t, n, i, a), !0;
				case 6: return c.fn.call(c.context, t, n, i, a, o), !0;
			}
			for (d = 1, u = Array(l - 1); d < l; d++) u[d - 1] = arguments[d];
			c.fn.apply(c.context, u);
		} else {
			var f = c.length, p;
			for (d = 0; d < f; d++) switch (c[d].once && this.removeListener(e, c[d].fn, void 0, !0), l) {
				case 1:
					c[d].fn.call(c[d].context);
					break;
				case 2:
					c[d].fn.call(c[d].context, t);
					break;
				case 3:
					c[d].fn.call(c[d].context, t, n);
					break;
				case 4:
					c[d].fn.call(c[d].context, t, n, i);
					break;
				default:
					if (!u) for (p = 1, u = Array(l - 1); p < l; p++) u[p - 1] = arguments[p];
					c[d].fn.apply(c[d].context, u);
			}
		}
		return !0;
	}, c.prototype.on = function(e, t, n) {
		return o(this, e, t, n, !1);
	}, c.prototype.once = function(e, t, n) {
		return o(this, e, t, n, !0);
	}, c.prototype.removeListener = function(e, t, n, i) {
		var a = r ? r + e : e;
		if (!this._events[a]) return this;
		if (!t) return s(this, a), this;
		var o = this._events[a];
		if (o.fn) o.fn === t && (!i || o.once) && (!n || o.context === n) && s(this, a);
		else {
			for (var c = 0, l = [], u = o.length; c < u; c++) (o[c].fn !== t || i && !o[c].once || n && o[c].context !== n) && l.push(o[c]);
			l.length ? this._events[a] = l.length === 1 ? l[0] : l : s(this, a);
		}
		return this;
	}, c.prototype.removeAllListeners = function(e) {
		var t;
		return e ? (t = r ? r + e : e, this._events[t] && s(this, t)) : (this._events = new i(), this._eventsCount = 0), this;
	}, c.prototype.off = c.prototype.removeListener, c.prototype.addListener = c.prototype.on, c.prefixed = r, c.EventEmitter = c, t !== void 0 && (t.exports = c);
})))(), 1)).default, Ww = new Uw(), Gw = "recharts.syncEvent.tooltip", Kw = "recharts.syncEvent.brush", qw = (e, t) => {
	if (t && Array.isArray(e)) {
		var n = Number.parseInt(t, 10);
		if (!Kt(n)) return e[n];
	}
}, Jw = xo({
	name: "options",
	initialState: {
		chartName: "",
		tooltipPayloadSearcher: () => void 0,
		eventEmitter: void 0,
		defaultTooltipEventType: "axis"
	},
	reducers: { createEventEmitter: (e) => {
		e.eventEmitter == null && (e.eventEmitter = Symbol("rechartsEventEmitter"));
	} }
}), Yw = Jw.reducer, Xw = Jw.actions.createEventEmitter;
//#endregion
//#region node_modules/recharts/es6/synchronisation/syncSelectors.js
function Zw(e) {
	return e.tooltip.syncInteraction;
}
var Qw = xo({
	name: "chartData",
	initialState: {
		chartData: void 0,
		computedData: void 0,
		dataStartIndex: 0,
		dataEndIndex: 0
	},
	reducers: {
		setChartData(e, t) {
			if (e.chartData = H(t.payload), t.payload == null) {
				e.dataStartIndex = 0, e.dataEndIndex = 0;
				return;
			}
			t.payload.length > 0 && e.dataEndIndex !== t.payload.length - 1 && (e.dataEndIndex = t.payload.length - 1);
		},
		setComputedData(e, t) {
			e.computedData = t.payload;
		},
		setDataStartEndIndexes(e, t) {
			var n = t.payload, r = n.startIndex, i = n.endIndex;
			r != null && (e.dataStartIndex = r), i != null && (e.dataEndIndex = i);
		}
	}
}), $w = Qw.actions, eT = $w.setChartData, tT = $w.setDataStartEndIndexes;
$w.setComputedData;
var nT = Qw.reducer, rT = ["x", "y"];
function iT(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function aT(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? iT(Object(n), !0).forEach(function(t) {
			oT(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : iT(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function oT(e, t, n) {
	return (t = sT(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function sT(e) {
	var t = cT(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function cT(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function lT(e, t) {
	if (e == null) return {};
	var n, r, i = uT(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function uT(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function dT() {
	var e = L(yp), t = L(xp), n = kr(), r = L(bp), i = L(SC), a = Jc(), o = Wc();
	(0, C.useEffect)(() => {
		if (e == null) return rn;
		var s = (s, c, l) => {
			if (t !== l && e === s) {
				if (c.payload.active === !1) {
					n(ES({
						active: !1,
						coordinate: void 0,
						dataKey: void 0,
						index: null,
						label: void 0,
						sourceViewBox: void 0,
						graphicalItemId: void 0
					}));
					return;
				}
				if (r === "index") {
					var u;
					if (o && c != null && (u = c.payload) != null && u.coordinate && c.payload.sourceViewBox) {
						var d = c.payload.coordinate, f = d.x, p = d.y, m = lT(d, rT), h = c.payload.sourceViewBox, g = h.x, _ = h.y, v = h.width, y = h.height, b = aT(aT({}, m), {}, {
							x: o.x + (v ? (f - g) / v : 0) * o.width,
							y: o.y + (y ? (p - _) / y : 0) * o.height
						});
						n(aT(aT({}, c), {}, { payload: aT(aT({}, c.payload), {}, { coordinate: b }) }));
					} else n(c);
					return;
				}
				if (i != null) {
					var x;
					typeof r == "function" ? x = i[r(i, {
						activeTooltipIndex: c.payload.index == null ? void 0 : Number(c.payload.index),
						isTooltipActive: c.payload.active,
						activeIndex: c.payload.index == null ? void 0 : Number(c.payload.index),
						activeLabel: c.payload.label,
						activeDataKey: c.payload.dataKey,
						activeCoordinate: c.payload.coordinate
					})] : r === "value" && (x = i.find((e) => String(e.value) === c.payload.label));
					var S = c.payload.coordinate;
					if (S == null || o == null) {
						n(ES({
							active: !1,
							coordinate: void 0,
							dataKey: void 0,
							index: null,
							label: void 0,
							sourceViewBox: void 0,
							graphicalItemId: void 0
						}));
						return;
					}
					if (x == null) {
						n(ES({
							active: !1,
							coordinate: void 0,
							dataKey: void 0,
							index: null,
							label: void 0,
							sourceViewBox: c.payload.sourceViewBox,
							graphicalItemId: void 0
						}));
						return;
					}
					var C = S.x, w = S.y, T = Math.min(C, o.x + o.width), E = Math.min(w, o.y + o.height), D = {
						x: a === "horizontal" ? x.coordinate : T,
						y: a === "horizontal" ? E : x.coordinate
					};
					n(ES({
						active: c.payload.active,
						coordinate: D,
						dataKey: c.payload.dataKey,
						index: String(x.index),
						label: c.payload.label,
						sourceViewBox: c.payload.sourceViewBox,
						graphicalItemId: c.payload.graphicalItemId
					}));
				}
			}
		};
		return Ww.on(Gw, s), () => {
			Ww.off(Gw, s);
		};
	}, [
		L((e) => e.rootProps.className),
		n,
		t,
		e,
		r,
		i,
		a,
		o
	]);
}
function fT() {
	var e = L(yp), t = L(xp), n = kr();
	(0, C.useEffect)(() => {
		if (e == null) return rn;
		var r = (r, i, a) => {
			t !== a && e === r && n(tT(i));
		};
		return Ww.on(Kw, r), () => {
			Ww.off(Kw, r);
		};
	}, [
		n,
		t,
		e
	]);
}
function pT() {
	var e = kr();
	(0, C.useEffect)(() => {
		e(Xw());
	}, [e]), dT(), fT();
}
function mT(e, t, n, r, i, a) {
	var o = L((n) => rw(n, e, t)), s = L(AC), c = L(xp), l = L(yp), u = L(bp), d = L(Zw), f = (d == null ? void 0 : d.sourceViewBox) != null, p = Wc();
	(0, C.useEffect)(() => {
		if (!f && l != null && c != null) {
			var e = ES({
				active: a,
				coordinate: n,
				dataKey: o,
				index: i,
				label: typeof r == "number" ? String(r) : r,
				sourceViewBox: p,
				graphicalItemId: s
			});
			Ww.emit(Gw, l, e, c);
		}
	}, [
		f,
		n,
		o,
		s,
		i,
		r,
		c,
		l,
		u,
		a,
		p
	]);
}
//#endregion
//#region node_modules/recharts/es6/component/Tooltip.js
function hT(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function gT(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? hT(Object(n), !0).forEach(function(t) {
			_T(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : hT(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function _T(e, t, n) {
	return (t = vT(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function vT(e) {
	var t = yT(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function yT(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function bT(e, t) {
	return TT(e) || wT(e, t) || ST(e, t) || xT();
}
function xT() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function ST(e, t) {
	if (e) {
		if (typeof e == "string") return CT(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? CT(e, t) : void 0;
	}
}
function CT(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function wT(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function TT(e) {
	if (Array.isArray(e)) return e;
}
function ET(e) {
	return e.dataKey;
}
function DT(e, t) {
	return /*#__PURE__*/ C.isValidElement(e) ? /*#__PURE__*/ C.cloneElement(e, t) : typeof e == "function" ? /*#__PURE__*/ C.createElement(e, t) : /*#__PURE__*/ C.createElement(zl, t);
}
var OT = [], kT = {
	allowEscapeViewBox: {
		x: !1,
		y: !1
	},
	animationDuration: 400,
	animationEasing: "ease",
	axisId: 0,
	contentStyle: {},
	cursor: !0,
	filterNull: !0,
	includeHidden: !1,
	isAnimationActive: "auto",
	itemSorter: "name",
	itemStyle: {},
	labelStyle: {},
	offset: 10,
	reverseDirection: {
		x: !1,
		y: !1
	},
	separator: " : ",
	trigger: "hover",
	useTranslate3d: !1,
	wrapperStyle: {}
};
function AT(e) {
	var t, n, r = mn(e, kT), i = r.active, a = r.allowEscapeViewBox, o = r.animationDuration, s = r.animationEasing, c = r.content, l = r.filterNull, u = r.isAnimationActive, d = r.offset, f = r.payloadUniqBy, p = r.position, m = r.reverseDirection, h = r.useTranslate3d, g = r.wrapperStyle, _ = r.cursor, v = r.shared, y = r.trigger, b = r.defaultIndex, x = r.portal, S = r.axisId, w = kr(), T = typeof b == "number" ? String(b) : b;
	(0, C.useEffect)(() => {
		w(yS({
			shared: v,
			trigger: y,
			axisId: S,
			active: i,
			defaultIndex: T
		}));
	}, [
		w,
		v,
		y,
		S,
		i,
		T
	]);
	var E = Wc(), D = mu(), O = uS(v), k = (t = L((e) => lw(e, O, y, T))) == null ? {} : t, A = k.activeIndex, j = k.isActive, M = L((e) => cw(e, O, y, T)), N = L((e) => sw(e, O, y, T)), P = L((e) => ow(e, O, y, T)), ee = M, te = Hw(), ne = (n = i == null ? j : i) != null && n, re = bT(_i([ee, ne]), 2), ie = re[0], ae = re[1], oe = O === "axis" ? N : void 0;
	mT(O, y, P, oe, A, ne);
	var se = x == null ? te : x;
	if (se == null || E == null || O == null) return null;
	var ce = ee == null ? OT : ee;
	ne || (ce = OT), l && ce.length && (ce = xr(ce.filter((e) => e.value != null && (e.hide !== !0 || r.includeHidden)), f, ET));
	var le = ce.length > 0, ue = gT(gT({}, r), {}, {
		payload: ce,
		label: oe,
		active: ne,
		activeIndex: A,
		coordinate: P,
		accessibilityLayer: D
	}), de = /*#__PURE__*/ C.createElement(pu, {
		allowEscapeViewBox: a,
		animationDuration: o,
		animationEasing: s,
		isAnimationActive: u,
		active: ne,
		coordinate: P,
		hasPayload: le,
		offset: d,
		position: p,
		reverseDirection: m,
		useTranslate3d: h,
		viewBox: E,
		wrapperStyle: g,
		lastBoundingBox: ie,
		innerRef: ae,
		hasPortalFromProps: !!x
	}, DT(c, ue));
	return /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ (0, Aw.createPortal)(de, se), ne && /*#__PURE__*/ C.createElement(Bw, {
		cursor: _,
		tooltipEventType: O,
		coordinate: P,
		payload: ce,
		index: A
	}));
}
//#endregion
//#region node_modules/recharts/es6/component/Cell.js
var jT = (e) => null;
jT.displayName = "Cell";
//#endregion
//#region node_modules/recharts/es6/util/LRUCache.js
function MT(e, t, n) {
	return (t = NT(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function NT(e) {
	var t = PT(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function PT(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var FT = class {
	constructor(e) {
		MT(this, "cache", /* @__PURE__ */ new Map()), this.maxSize = e;
	}
	get(e) {
		var t = this.cache.get(e);
		return t !== void 0 && (this.cache.delete(e), this.cache.set(e, t)), t;
	}
	set(e, t) {
		if (this.cache.has(e)) this.cache.delete(e);
		else if (this.cache.size >= this.maxSize) {
			var n = this.cache.keys().next().value;
			n != null && this.cache.delete(n);
		}
		this.cache.set(e, t);
	}
	clear() {
		this.cache.clear();
	}
	size() {
		return this.cache.size;
	}
};
//#endregion
//#region node_modules/recharts/es6/util/DOMUtils.js
function IT(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function LT(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? IT(Object(n), !0).forEach(function(t) {
			RT(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : IT(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function RT(e, t, n) {
	return (t = zT(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function zT(e) {
	var t = BT(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function BT(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var VT = LT({}, {
	cacheSize: 2e3,
	enableCache: !0
}), HT = new FT(VT.cacheSize), UT = {
	position: "absolute",
	top: "-20000px",
	left: 0,
	padding: 0,
	margin: 0,
	border: "none",
	whiteSpace: "pre"
}, WT = "recharts_measurement_span";
function GT(e, t) {
	return `${e}|${t.fontSize || ""}|${t.fontFamily || ""}|${t.fontWeight || ""}|${t.fontStyle || ""}|${t.letterSpacing || ""}|${t.textTransform || ""}`;
}
var KT = (e, t) => {
	try {
		var n = document.getElementById(WT);
		n || (n = document.createElement("span"), n.setAttribute("id", WT), n.setAttribute("aria-hidden", "true"), document.body.appendChild(n)), Object.assign(n.style, UT, t), n.textContent = `${e}`;
		var r = n.getBoundingClientRect();
		return {
			width: r.width,
			height: r.height
		};
	} catch (e) {
		return {
			width: 0,
			height: 0
		};
	}
}, qT = function(e) {
	var t = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : {};
	if (e == null || Kl.isSsr) return {
		width: 0,
		height: 0
	};
	if (!VT.enableCache) return KT(e, t);
	var n = GT(e, t), r = HT.get(n);
	if (r) return r;
	var i = KT(e, t);
	return HT.set(n, i), i;
}, JT;
function YT(e, t) {
	return eE(e) || $T(e, t) || ZT(e, t) || XT();
}
function XT() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function ZT(e, t) {
	if (e) {
		if (typeof e == "string") return QT(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? QT(e, t) : void 0;
	}
}
function QT(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function $T(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function eE(e) {
	if (Array.isArray(e)) return e;
}
function tE(e, t, n) {
	return (t = nE(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function nE(e) {
	var t = rE(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function rE(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var iE = /(-?\d+(?:\.\d+)?[a-zA-Z%]*)([*/])(-?\d+(?:\.\d+)?[a-zA-Z%]*)/, aE = /(-?\d+(?:\.\d+)?[a-zA-Z%]*)([+-])(-?\d+(?:\.\d+)?[a-zA-Z%]*)/, oE = /^(px|cm|vh|vw|em|rem|%|mm|in|pt|pc|ex|ch|vmin|vmax|Q)$/, sE = /(-?\d+(?:\.\d+)?)([a-zA-Z%]+)?/, cE = {
	cm: 96 / 2.54,
	mm: 96 / 25.4,
	pt: 96 / 72,
	pc: 96 / 6,
	in: 96,
	Q: 96 / (2.54 * 40),
	px: 1
}, lE = [
	"cm",
	"mm",
	"pt",
	"pc",
	"in",
	"Q",
	"px"
];
function uE(e) {
	return lE.includes(e);
}
var dE = "NaN";
function fE(e, t) {
	return e * cE[t];
}
var pE = class e {
	static parse(t) {
		var n, r = YT((n = sE.exec(t)) == null ? [] : n, 3), i = r[1], a = r[2];
		return i == null ? e.NaN : new e(parseFloat(i), a == null ? "" : a);
	}
	constructor(e, t) {
		this.num = e, this.unit = t, this.num = e, this.unit = t, Kt(e) && (this.unit = ""), t !== "" && !oE.test(t) && (this.num = NaN, this.unit = ""), uE(t) && (this.num = fE(e, t), this.unit = "px");
	}
	add(t) {
		return this.unit === t.unit ? new e(this.num + t.num, this.unit) : new e(NaN, "");
	}
	subtract(t) {
		return this.unit === t.unit ? new e(this.num - t.num, this.unit) : new e(NaN, "");
	}
	multiply(t) {
		return this.unit !== "" && t.unit !== "" && this.unit !== t.unit ? new e(NaN, "") : new e(this.num * t.num, this.unit || t.unit);
	}
	divide(t) {
		return this.unit !== "" && t.unit !== "" && this.unit !== t.unit ? new e(NaN, "") : new e(this.num / t.num, this.unit || t.unit);
	}
	toString() {
		return `${this.num}${this.unit}`;
	}
	isNaN() {
		return Kt(this.num);
	}
};
JT = pE, tE(pE, "NaN", new JT(NaN, ""));
function mE(e) {
	if (e == null || e.includes(dE)) return dE;
	for (var t = e; t.includes("*") || t.includes("/");) {
		var n, r = YT((n = iE.exec(t)) == null ? [] : n, 4), i = r[1], a = r[2], o = r[3], s = pE.parse(i == null ? "" : i), c = pE.parse(o == null ? "" : o), l = a === "*" ? s.multiply(c) : s.divide(c);
		if (l.isNaN()) return dE;
		t = t.replace(iE, l.toString());
	}
	for (; t.includes("+") || /.-\d+(?:\.\d+)?/.test(t);) {
		var u, d = YT((u = aE.exec(t)) == null ? [] : u, 4), f = d[1], p = d[2], m = d[3], h = pE.parse(f == null ? "" : f), g = pE.parse(m == null ? "" : m), _ = p === "+" ? h.add(g) : h.subtract(g);
		if (_.isNaN()) return dE;
		t = t.replace(aE, _.toString());
	}
	return t;
}
var hE = /\(([^()]*)\)/;
function gE(e) {
	for (var t = e, n; (n = hE.exec(t)) != null;) {
		var r = YT(n, 2)[1];
		t = t.replace(hE, mE(r));
	}
	return t;
}
function _E(e) {
	var t = e.replace(/\s+/g, "");
	return t = gE(t), t = mE(t), t;
}
function vE(e) {
	try {
		return _E(e);
	} catch (e) {
		return dE;
	}
}
function yE(e) {
	var t = vE(e.slice(5, -1));
	return t === dE ? "" : t;
}
//#endregion
//#region node_modules/recharts/es6/component/Text.js
var bE = [
	"x",
	"y",
	"lineHeight",
	"capHeight",
	"fill",
	"scaleToFit",
	"textAnchor",
	"verticalAnchor"
], xE = [
	"dx",
	"dy",
	"angle",
	"className",
	"breakAll"
];
function SE() {
	return SE = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, SE.apply(null, arguments);
}
function CE(e, t) {
	if (e == null) return {};
	var n, r, i = wE(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function wE(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function TE(e, t) {
	return AE(e) || kE(e, t) || DE(e, t) || EE();
}
function EE() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function DE(e, t) {
	if (e) {
		if (typeof e == "string") return OE(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? OE(e, t) : void 0;
	}
}
function OE(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function kE(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function AE(e) {
	if (Array.isArray(e)) return e;
}
var jE = /[ \f\n\r\t\v\u2028\u2029]+/, ME = (e) => {
	var t = e.children, n = e.breakAll, r = e.style;
	try {
		var i = [];
		return en(t) || (i = n ? t.toString().split("") : t.toString().split(jE)), {
			wordsWithComputedWidth: i.map((e) => ({
				word: e,
				width: qT(e, r).width
			})),
			spaceWidth: n ? 0 : qT("\xA0", r).width
		};
	} catch (e) {
		return null;
	}
};
function NE(e) {
	return e === "start" || e === "middle" || e === "end" || e === "inherit";
}
function PE(e) {
	return en(e) || typeof e == "string" || typeof e == "number" || typeof e == "boolean";
}
var FE = (e, t, n, r) => e.reduce((e, i) => {
	var a = i.word, o = i.width, s = e[e.length - 1];
	if (s && o != null && (t == null || r || s.width + o + n < Number(t))) s.words.push(a), s.width += o + n;
	else {
		var c = {
			words: [a],
			width: o
		};
		e.push(c);
	}
	return e;
}, []), IE = (e) => e.reduce((e, t) => e.width > t.width ? e : t), LE = "…", RE = (e, t, n, r, i, a, o, s) => {
	var c = ME({
		breakAll: n,
		style: r,
		children: e.slice(0, t) + LE
	});
	if (!c) return [!1, []];
	var l = FE(c.wordsWithComputedWidth, a, o, s);
	return [l.length > i || IE(l).width > Number(a), l];
}, zE = (e, t, n, r, i) => {
	var a = e.maxLines, o = e.children, s = e.style, c = e.breakAll, l = I(a), u = String(o), d = FE(t, r, n, i);
	if (!l || i || !(d.length > a || IE(d).width > Number(r))) return d;
	for (var f = 0, p = u.length - 1, m = 0, h; f <= p && m <= u.length - 1;) {
		var g = Math.floor((f + p) / 2), _ = TE(RE(u, g - 1, c, s, a, r, n, i), 2), v = _[0], y = _[1], b = TE(RE(u, g, c, s, a, r, n, i), 1)[0];
		if (!v && !b && (f = g + 1), v && b && (p = g - 1), !v && b) {
			h = y;
			break;
		}
		m++;
	}
	return h || d;
}, BE = (e) => [{
	words: en(e) ? [] : e.toString().split(jE),
	width: void 0
}], VE = (e) => {
	var t = e.width, n = e.scaleToFit, r = e.children, i = e.style, a = e.breakAll, o = e.maxLines;
	if ((t || n) && !Kl.isSsr) {
		var s, c, l = ME({
			breakAll: a,
			children: r,
			style: i
		});
		if (l) {
			var u = l.wordsWithComputedWidth, d = l.spaceWidth;
			s = u, c = d;
		} else return BE(r);
		return zE({
			breakAll: a,
			children: r,
			maxLines: o,
			style: i
		}, s, c, t, !!n);
	}
	return BE(r);
}, HE = "#808080", UE = {
	angle: 0,
	breakAll: !1,
	capHeight: "0.71em",
	fill: HE,
	lineHeight: "1em",
	scaleToFit: !1,
	textAnchor: "start",
	verticalAnchor: "end",
	x: 0,
	y: 0
}, WE = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = mn(e, UE), r = n.x, i = n.y, a = n.lineHeight, o = n.capHeight, s = n.fill, c = n.scaleToFit, l = n.textAnchor, u = n.verticalAnchor, d = CE(n, bE), f = (0, C.useMemo)(() => VE({
		breakAll: d.breakAll,
		children: d.children,
		maxLines: d.maxLines,
		scaleToFit: c,
		style: d.style,
		width: d.width
	}), [
		d.breakAll,
		d.children,
		d.maxLines,
		c,
		d.style,
		d.width
	]), p = d.dx, m = d.dy, h = d.angle, g = d.className, _ = d.breakAll, v = CE(d, xE);
	if (!qt(r) || !qt(i) || f.length === 0) return null;
	var y = Number(r) + (I(p) ? p : 0), b = Number(i) + (I(m) ? m : 0);
	if (!U(y) || !U(b)) return null;
	var x;
	switch (u) {
		case "start":
			x = yE(`calc(${o})`);
			break;
		case "middle":
			x = yE(`calc(${(f.length - 1) / 2} * -${a} + (${o} / 2))`);
			break;
		default:
			x = yE(`calc(${f.length - 1} * -${a})`);
			break;
	}
	var S = [], w = f[0];
	if (c && w != null) {
		var T = w.width, E = d.width;
		S.push(`scale(${I(E) && I(T) ? E / T : 1})`);
	}
	return h && S.push(`rotate(${h}, ${y}, ${b})`), S.length && (v.transform = S.join(" ")), /*#__PURE__*/ C.createElement("text", SE({}, Ce(v), {
		ref: t,
		x: y,
		y: b,
		className: he("recharts-text", g),
		textAnchor: l,
		fill: s.includes("url") ? HE : s
	}), f.map((e, t) => {
		var n = e.words.join(_ ? "" : " ");
		return /*#__PURE__*/ C.createElement("tspan", {
			x: y,
			dy: t === 0 ? x : a,
			key: `${n}-${t}`
		}, n);
	}));
});
WE.displayName = "Text";
//#endregion
//#region node_modules/recharts/es6/cartesian/getCartesianPosition.js
function GE(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function KE(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? GE(Object(n), !0).forEach(function(t) {
			qE(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : GE(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function qE(e, t, n) {
	return (t = JE(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function JE(e) {
	var t = YE(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function YE(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var XE = (e) => {
	var t = e.viewBox, n = e.position, r = e.offset, i = r === void 0 ? 0 : r, a = e.parentViewBox, o = e.clamp, s = Uc(t), c = s.x, l = s.y, u = s.height, d = s.upperWidth, f = s.lowerWidth, p = c, m = c + (d - f) / 2, h = (p + m) / 2, g = (d + f) / 2, _ = p + d / 2, v = u >= 0 ? 1 : -1, y = v * i, b = v > 0 ? "end" : "start", x = v > 0 ? "start" : "end", S = d >= 0 ? 1 : -1, C = S * i, w = S > 0 ? "end" : "start", T = S > 0 ? "start" : "end", E = a;
	if (n === "top") {
		var D = {
			x: p + d / 2,
			y: l - y,
			horizontalAnchor: "middle",
			verticalAnchor: b
		};
		return o && E && (D.height = Math.max(l - E.y, 0), D.width = d), D;
	}
	if (n === "bottom") {
		var O = {
			x: m + f / 2,
			y: l + u + y,
			horizontalAnchor: "middle",
			verticalAnchor: x
		};
		return o && E && (O.height = Math.max(E.y + E.height - (l + u), 0), O.width = f), O;
	}
	if (n === "left") {
		var k = {
			x: h - C,
			y: l + u / 2,
			horizontalAnchor: w,
			verticalAnchor: "middle"
		};
		return o && E && (k.width = Math.max(k.x - E.x, 0), k.height = u), k;
	}
	if (n === "right") {
		var A = {
			x: h + g + C,
			y: l + u / 2,
			horizontalAnchor: T,
			verticalAnchor: "middle"
		};
		return o && E && (A.width = Math.max(E.x + E.width - A.x, 0), A.height = u), A;
	}
	var j = o && E ? {
		width: g,
		height: u
	} : {};
	return n === "insideLeft" ? KE({
		x: h + C,
		y: l + u / 2,
		horizontalAnchor: T,
		verticalAnchor: "middle"
	}, j) : n === "insideRight" ? KE({
		x: h + g - C,
		y: l + u / 2,
		horizontalAnchor: w,
		verticalAnchor: "middle"
	}, j) : n === "insideTop" ? KE({
		x: p + d / 2,
		y: l + y,
		horizontalAnchor: "middle",
		verticalAnchor: x
	}, j) : n === "insideBottom" ? KE({
		x: m + f / 2,
		y: l + u - y,
		horizontalAnchor: "middle",
		verticalAnchor: b
	}, j) : n === "insideTopLeft" ? KE({
		x: p + C,
		y: l + y,
		horizontalAnchor: T,
		verticalAnchor: x
	}, j) : n === "insideTopRight" ? KE({
		x: p + d - C,
		y: l + y,
		horizontalAnchor: w,
		verticalAnchor: x
	}, j) : n === "insideBottomLeft" ? KE({
		x: m + C,
		y: l + u - y,
		horizontalAnchor: T,
		verticalAnchor: b
	}, j) : n === "insideBottomRight" ? KE({
		x: m + f - C,
		y: l + u - y,
		horizontalAnchor: w,
		verticalAnchor: b
	}, j) : n && typeof n == "object" && (I(n.x) || F(n.x)) && (I(n.y) || F(n.y)) ? KE({
		x: c + Xt(n.x, g),
		y: l + Xt(n.y, u),
		horizontalAnchor: "end",
		verticalAnchor: "end"
	}, j) : KE({
		x: _,
		y: l + u / 2,
		horizontalAnchor: "middle",
		verticalAnchor: "middle"
	}, j);
}, ZE = ["labelRef"], QE = ["content"];
function $E(e, t) {
	if (e == null) return {};
	var n, r, i = eD(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function eD(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function tD(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function nD(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? tD(Object(n), !0).forEach(function(t) {
			rD(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : tD(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function rD(e, t, n) {
	return (t = iD(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function iD(e) {
	var t = aD(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function aD(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function oD() {
	return oD = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, oD.apply(null, arguments);
}
var sD = /*#__PURE__*/ (0, C.createContext)(null), cD = (e) => {
	var t = e.x, n = e.y, r = e.upperWidth, i = e.lowerWidth, a = e.width, o = e.height, s = e.children, c = (0, C.useMemo)(() => ({
		x: t,
		y: n,
		upperWidth: r,
		lowerWidth: i,
		width: a,
		height: o
	}), [
		t,
		n,
		r,
		i,
		a,
		o
	]);
	return /*#__PURE__*/ C.createElement(sD.Provider, { value: c }, s);
}, lD = () => {
	var e = (0, C.useContext)(sD), t = Wc();
	return e || (t ? Uc(t) : void 0);
}, uD = /*#__PURE__*/ (0, C.createContext)(null), dD = () => {
	var e = (0, C.useContext)(uD), t = L(Hp);
	return e || t;
}, fD = (e) => {
	var t = e.value, n = e.formatter, r = en(e.children) ? t : e.children;
	return typeof n == "function" ? n(r) : r;
}, pD = (e) => e != null && typeof e == "function", mD = (e, t) => Gt(t - e) * Math.min(Math.abs(t - e), 360), hD = (e, t, n, r, i) => {
	var a = e.offset, o = e.className, s = i.cx, c = i.cy, l = i.innerRadius, u = i.outerRadius, d = i.startAngle, f = i.endAngle, p = i.clockWise, m = (l + u) / 2, h = mD(d, f), g = h >= 0 ? 1 : -1, _, v;
	switch (t) {
		case "insideStart":
			_ = d + g * a, v = p;
			break;
		case "insideEnd":
			_ = f - g * a, v = !p;
			break;
		case "end":
			_ = f + g * a, v = p;
			break;
		default: throw Error(`Unsupported position ${t}`);
	}
	v = h <= 0 ? v : !v;
	var y = cf(s, c, m, _), b = cf(s, c, m, _ + (v ? 1 : -1) * 359), x = `M${y.x},${y.y}
    A${m},${m},0,1,${+!v},
    ${b.x},${b.y}`, S = en(e.id) ? Yt("recharts-radial-line-") : e.id;
	return /*#__PURE__*/ C.createElement("text", oD({}, r, {
		dominantBaseline: "central",
		className: he("recharts-radial-bar-label", o)
	}), /*#__PURE__*/ C.createElement("defs", null, /*#__PURE__*/ C.createElement("path", {
		id: S,
		d: x
	})), /*#__PURE__*/ C.createElement("textPath", { xlinkHref: `#${S}` }, n));
}, gD = (e, t, n) => {
	var r = e.cx, i = e.cy, a = e.innerRadius, o = e.outerRadius, s = (e.startAngle + e.endAngle) / 2;
	if (n === "outside") {
		var c = cf(r, i, o + t, s), l = c.x;
		return {
			x: l,
			y: c.y,
			textAnchor: l >= r ? "start" : "end",
			verticalAnchor: "middle"
		};
	}
	if (n === "center") return {
		x: r,
		y: i,
		textAnchor: "middle",
		verticalAnchor: "middle"
	};
	if (n === "centerTop") return {
		x: r,
		y: i,
		textAnchor: "middle",
		verticalAnchor: "start"
	};
	if (n === "centerBottom") return {
		x: r,
		y: i,
		textAnchor: "middle",
		verticalAnchor: "end"
	};
	var u = cf(r, i, (a + o) / 2, s);
	return {
		x: u.x,
		y: u.y,
		textAnchor: "middle",
		verticalAnchor: "middle"
	};
}, _D = (e) => e != null && "cx" in e && I(e.cx), vD = {
	angle: 0,
	offset: 5,
	zIndex: Sp.label,
	position: "middle",
	textBreakAll: !1
};
function yD(e) {
	if (!_D(e)) return e;
	var t = e.cx, n = e.cy, r = e.outerRadius, i = r * 2;
	return {
		x: t - r,
		y: n - r,
		width: i,
		upperWidth: i,
		lowerWidth: i,
		height: i
	};
}
function bD(e) {
	var t = mn(e, vD), n = t.viewBox, r = t.parentViewBox, i = t.position, a = t.value, o = t.children, s = t.content, c = t.className, l = c === void 0 ? "" : c, u = t.textBreakAll, d = t.labelRef, f = dD(), p = lD(), m = n == null ? i === "center" || f == null ? p : f : _D(n) ? n : Uc(n), h, g, _ = yD(m);
	if (!m || en(a) && en(o) && !/*#__PURE__*/ (0, C.isValidElement)(s) && typeof s != "function") return null;
	var v = nD(nD({}, t), {}, { viewBox: m });
	if (/*#__PURE__*/ (0, C.isValidElement)(s)) return v.labelRef, /*#__PURE__*/ (0, C.cloneElement)(s, $E(v, ZE));
	if (typeof s == "function") {
		if (v.content, h = /*#__PURE__*/ (0, C.createElement)(s, $E(v, QE)), /*#__PURE__*/ (0, C.isValidElement)(h)) return h;
	} else h = fD(t);
	var y = Ce(t);
	if (_D(m)) {
		if (i === "insideStart" || i === "insideEnd" || i === "end") return hD(t, i, h, y, m);
		g = gD(m, t.offset, t.position);
	} else {
		if (!_) return null;
		var b = XE({
			viewBox: _,
			position: i,
			offset: t.offset,
			parentViewBox: _D(r) ? void 0 : r,
			clamp: !0
		});
		g = nD(nD({
			x: b.x,
			y: b.y,
			textAnchor: b.horizontalAnchor,
			verticalAnchor: b.verticalAnchor
		}, b.width === void 0 ? {} : { width: b.width }), b.height === void 0 ? {} : { height: b.height });
	}
	return /*#__PURE__*/ C.createElement(jw, { zIndex: t.zIndex }, /*#__PURE__*/ C.createElement(WE, oD({
		ref: d,
		className: he("recharts-label", l)
	}, y, g, {
		textAnchor: NE(y.textAnchor) ? y.textAnchor : g.textAnchor,
		breakAll: u
	}), h));
}
bD.displayName = "Label";
var xD = (e, t, n) => {
	if (!e) return null;
	var r = {
		viewBox: t,
		labelRef: n
	};
	return e === !0 ? /*#__PURE__*/ C.createElement(bD, oD({ key: "label-implicit" }, r)) : qt(e) ? /*#__PURE__*/ C.createElement(bD, oD({
		key: "label-implicit",
		value: e
	}, r)) : /*#__PURE__*/ (0, C.isValidElement)(e) ? e.type === bD ? /*#__PURE__*/ (0, C.cloneElement)(e, nD({ key: "label-implicit" }, r)) : /*#__PURE__*/ C.createElement(bD, oD({
		key: "label-implicit",
		content: e
	}, r)) : pD(e) ? /*#__PURE__*/ C.createElement(bD, oD({
		key: "label-implicit",
		content: e
	}, r)) : e && typeof e == "object" ? /*#__PURE__*/ C.createElement(bD, oD({}, e, { key: "label-implicit" }, r)) : null;
};
function SD(e) {
	var t = e.label, n = e.labelRef;
	return xD(t, lD(), n) || null;
}
//#endregion
//#region node_modules/recharts/es6/component/LabelList.js
var CD = ["valueAccessor"], wD = [
	"dataKey",
	"clockWise",
	"id",
	"textBreakAll",
	"zIndex"
];
function TD() {
	return TD = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, TD.apply(null, arguments);
}
function ED(e, t) {
	if (e == null) return {};
	var n, r, i = DD(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function DD(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var OD = (e) => {
	var t = Array.isArray(e.value) ? e.value[e.value.length - 1] : e.value;
	if (PE(t)) return t;
}, kD = /*#__PURE__*/ (0, C.createContext)(void 0), AD = kD.Provider, jD = /*#__PURE__*/ (0, C.createContext)(void 0);
jD.Provider;
function MD() {
	return (0, C.useContext)(kD);
}
function ND() {
	return (0, C.useContext)(jD);
}
function PD(e) {
	var t = e.valueAccessor, n = t === void 0 ? OD : t, r = ED(e, CD), i = r.dataKey;
	r.clockWise;
	var a = r.id, o = r.textBreakAll, s = r.zIndex, c = ED(r, wD), l = MD(), u = ND(), d = l || u;
	return !d || !d.length ? null : /*#__PURE__*/ C.createElement(jw, { zIndex: s == null ? Sp.label : s }, /*#__PURE__*/ C.createElement(Ne, { className: "recharts-label-list" }, d.map((e, t) => {
		var s, l = en(i) ? n(e, t) : W(e.payload, i), u = en(a) ? {} : { id: `${a}-${t}` };
		return /*#__PURE__*/ C.createElement(bD, TD({ key: `label-${t}` }, Ce(e), c, u, {
			fill: (s = r.fill) == null ? e.fill : s,
			parentViewBox: e.parentViewBox,
			value: l,
			textBreakAll: o,
			viewBox: e.viewBox,
			index: t,
			zIndex: 0
		}));
	})));
}
PD.displayName = "LabelList";
function FD(e) {
	var t = e.label;
	return t ? t === !0 ? /*#__PURE__*/ C.createElement(PD, { key: "labelList-implicit" }) : /*#__PURE__*/ C.isValidElement(t) || pD(t) ? /*#__PURE__*/ C.createElement(PD, {
		key: "labelList-implicit",
		content: t
	}) : typeof t == "object" ? /*#__PURE__*/ C.createElement(PD, TD({ key: "labelList-implicit" }, t, { type: String(t.type) })) : null : null;
}
//#endregion
//#region node_modules/recharts/es6/state/polarAxisSlice.js
var ID = xo({
	name: "polarAxis",
	initialState: {
		radiusAxis: {},
		angleAxis: {}
	},
	reducers: {
		addRadiusAxis(e, t) {
			e.radiusAxis[t.payload.id] = H(t.payload);
		},
		removeRadiusAxis(e, t) {
			delete e.radiusAxis[t.payload.id];
		},
		addAngleAxis(e, t) {
			e.angleAxis[t.payload.id] = H(t.payload);
		},
		removeAngleAxis(e, t) {
			delete e.angleAxis[t.payload.id];
		}
	}
}), LD = ID.actions;
LD.addRadiusAxis, LD.removeRadiusAxis, LD.addAngleAxis, LD.removeAngleAxis;
var RD = ID.reducer;
//#endregion
//#region node_modules/recharts/es6/util/getClassNameFromUnknown.js
function zD(e) {
	return e && typeof e == "object" && "className" in e && typeof e.className == "string" ? e.className : "";
}
//#endregion
//#region node_modules/react-is/cjs/react-is.production.min.js
var BD = /* @__PURE__ */ o(((e) => {
	var t = 60103, n = 60106, r = 60107, i = 60108, a = 60114, o = 60109, s = 60110, c = 60112, l = 60113, u = 60120, d = 60115, f = 60116;
	if (typeof Symbol == "function" && Symbol.for) {
		var p = Symbol.for;
		t = p("react.element"), n = p("react.portal"), r = p("react.fragment"), i = p("react.strict_mode"), a = p("react.profiler"), o = p("react.provider"), s = p("react.context"), c = p("react.forward_ref"), l = p("react.suspense"), u = p("react.suspense_list"), d = p("react.memo"), f = p("react.lazy"), p("react.block"), p("react.server.block"), p("react.fundamental"), p("react.debug_trace_mode"), p("react.legacy_hidden");
	}
	function m(e) {
		if (typeof e == "object" && e) {
			var p = e.$$typeof;
			switch (p) {
				case t: switch (e = e.type, e) {
					case r:
					case a:
					case i:
					case l:
					case u: return e;
					default: switch (e = e && e.$$typeof, e) {
						case s:
						case c:
						case f:
						case d:
						case o: return e;
						default: return p;
					}
				}
				case n: return p;
			}
		}
	}
	e.isFragment = function(e) {
		return m(e) === r;
	};
})), VD = (/* @__PURE__ */ o(((e, t) => {
	t.exports = BD();
})))(), HD = (e) => typeof e == "string" ? e : e ? e.displayName || e.name || "Component" : "", UD = null, WD = null, GD = (e) => {
	if (e === UD && Array.isArray(WD)) return WD;
	var t = [];
	return C.Children.forEach(e, (e) => {
		en(e) || ((0, VD.isFragment)(e) ? t = t.concat(GD(e.props.children)) : t.push(e));
	}), WD = t, UD = e, t;
};
function KD(e, t) {
	var n = [], r = [];
	return r = Array.isArray(t) ? t.map((e) => HD(e)) : [HD(t)], GD(e).forEach((e) => {
		var t = Bt(e, "type.displayName") || Bt(e, "type.name");
		t && r.indexOf(t) !== -1 && n.push(e);
	}), n;
}
//#endregion
//#region node_modules/recharts/es6/util/ActiveShapeUtils.js
function qD(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function JD(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? qD(Object(n), !0).forEach(function(t) {
			YD(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : qD(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function YD(e, t, n) {
	return (t = XD(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function XD(e) {
	var t = ZD(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function ZD(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function QD(e, t) {
	return JD(JD({}, t), e);
}
function $D(e) {
	return /*#__PURE__*/ (0, C.isValidElement)(e) ? e.props : e;
}
function eO(e, t) {
	return /*#__PURE__*/ (0, C.cloneElement)(e, QD($D(e), t));
}
function tO(e) {
	if ("index" in e) {
		var t = e.index;
		return typeof t == "number" || typeof t == "string" ? t : void 0;
	}
}
function nO(e) {
	return "isActive" in e && e.isActive === !0;
}
function rO(e) {
	var t = e.option, n = e.DefaultShape, r = e.shapeProps, i = e.activeClassName, a = i === void 0 ? "recharts-active-shape" : i, o = e.inActiveClassName, s = o === void 0 ? "recharts-shape" : o, c = tO(r), l = /*#__PURE__*/ (0, C.isValidElement)(t) ? eO(t, r) : t === n ? /*#__PURE__*/ C.createElement(n, r) : typeof t == "function" ? t(r, c) : typeof t == "object" ? /*#__PURE__*/ C.createElement(n, QD(t, r)) : /*#__PURE__*/ C.createElement(n, r);
	return nO(r) ? /*#__PURE__*/ C.createElement(Ne, { className: a }, l) : /*#__PURE__*/ C.createElement(Ne, { className: s }, l);
}
//#endregion
//#region node_modules/recharts/es6/context/tooltipContext.js
var iO = (e, t, n) => {
	var r = kr();
	return (i, a) => (o) => {
		e == null || e(i, a, o), r(bS({
			activeIndex: String(a),
			activeDataKey: t,
			activeCoordinate: i.tooltipPosition,
			activeGraphicalItemId: n
		}));
	};
}, aO = (e) => {
	var t = kr();
	return (n, r) => (i) => {
		e == null || e(n, r, i), t(xS());
	};
}, oO = (e, t, n) => {
	var r = kr();
	return (i, a) => (o) => {
		e == null || e(i, a, o), r(CS({
			activeIndex: String(a),
			activeDataKey: t,
			activeCoordinate: i.tooltipPosition,
			activeGraphicalItemId: n
		}));
	};
};
//#endregion
//#region node_modules/recharts/es6/state/SetTooltipEntrySettings.js
function sO(e) {
	var t = e.tooltipEntrySettings, n = kr(), r = cc(), i = (0, C.useRef)(null);
	return (0, C.useLayoutEffect)(() => {
		r || (i.current === null ? n(gS(t)) : i.current !== t && n(_S({
			prev: i.current,
			next: t
		})), i.current = t);
	}, [
		t,
		n,
		r
	]), (0, C.useLayoutEffect)(() => () => {
		i.current && (n(vS(i.current)), i.current = null);
	}, [n]), null;
}
//#endregion
//#region node_modules/recharts/es6/state/SetLegendPayload.js
function cO(e) {
	var t = e.legendPayload, n = kr(), r = cc(), i = (0, C.useRef)(null);
	return (0, C.useLayoutEffect)(() => {
		r || (i.current === null ? n(tl(t)) : i.current !== t && n(nl({
			prev: i.current,
			next: t
		})), i.current = t);
	}, [
		n,
		r,
		t
	]), (0, C.useLayoutEffect)(() => () => {
		i.current && (n(rl(i.current)), i.current = null);
	}, [n]), null;
}
//#endregion
//#region node_modules/recharts/es6/animation/matchBy.js
function lO(e, t) {
	return mO(e) || pO(e, t) || dO(e, t) || uO();
}
function uO() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function dO(e, t) {
	if (e) {
		if (typeof e == "string") return fO(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? fO(e, t) : void 0;
	}
}
function fO(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function pO(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function mO(e) {
	if (Array.isArray(e)) return e;
}
var hO = "index", gO = "append";
function _O(e, t) {
	var n = arguments.length > 2 && arguments[2] !== void 0 ? arguments[2] : [], r = [];
	for (var i of n) r.push({
		status: "removed",
		prev: i
	});
	for (var a = 0; a < t.length; a++) {
		var o = e[a], s = t[a];
		o == null ? r.push({
			status: "added",
			next: s
		}) : r.push({
			status: "matched",
			prev: o,
			next: s
		});
	}
	return r;
}
function vO(e, t) {
	var n = e.length / t.length;
	return _O(t.map((t, r) => e[Math.floor(r * n)]), t);
}
function yO(e, t) {
	return _O(t.map((t, n) => e[n]), t);
}
function bO(e, t) {
	for (var n = /* @__PURE__ */ new Map(), r = 0; r < e.length; r++) {
		var i = e[r];
		if (i != null) {
			var a = t(i, r);
			a != null && !n.has(a) && n.set(a, i);
		}
	}
	return n;
}
function xO(e, t, n) {
	var r = bO(e, n), i = /* @__PURE__ */ new Set(), a = t.map((e, t) => {
		var a = n(e, t);
		if (a != null) {
			var o = r.get(a);
			if (o !== void 0) return i.add(a), o;
		}
	}), o = [];
	for (var s of r) {
		var c = lO(s, 2), l = c[0], u = c[1];
		i.has(l) || o.push(u);
	}
	return _O(a, t, o);
}
function SO(e, t, n) {
	return t == null ? null : e == null ? t.map((e) => ({
		status: "added",
		next: e
	})) : n === "index" ? vO(e, t) : n === "append" ? yO(e, t) : xO(e, t, n);
}
//#endregion
//#region node_modules/recharts/es6/animation/useAnimationStartSnapshot.js
function CO(e, t) {
	var n = (0, C.useRef)(e), r = (0, C.useRef)(t.current), i = (0, C.useRef)(!0);
	n.current !== e && (n.current = e, r.current = t.current, i.current = !1);
	var a = (0, C.useCallback)(function(e, n) {
		var a = arguments.length > 2 && arguments[2] !== void 0 ? arguments[2] : !0;
		if (n === 0) {
			i.current = !0;
			return;
		}
		n === 1 && (r.current = e), n > 0 && i.current && a && (t.current = e);
	}, [t]);
	return {
		startValue: r.current,
		syncStepValue: a
	};
}
//#endregion
//#region node_modules/recharts/es6/animation/AnimatedItems.js
function wO(e, t) {
	return kO(e) || OO(e, t) || EO(e, t) || TO();
}
function TO() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function EO(e, t) {
	if (e) {
		if (typeof e == "string") return DO(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? DO(e, t) : void 0;
	}
}
function DO(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function OO(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function kO(e) {
	if (Array.isArray(e)) return e;
}
function AO(e, t) {
	var n = wO((0, C.useState)(!1), 2), r = n[0], i = n[1];
	return {
		isAnimating: r,
		handleAnimationStart: (0, C.useCallback)(() => {
			typeof e == "function" && e(), i(!0);
		}, [e]),
		handleAnimationEnd: (0, C.useCallback)(() => {
			typeof t == "function" && t(), i(!1);
		}, [t])
	};
}
function jO(e) {
	var t, n = e.animationInput, r = e.animationIdPrefix, i = e.items, a = e.previousItemsRef, o = e.isAnimationActive, s = e.animationBegin, c = e.animationDuration, l = e.animationEasing, u = e.onAnimationStart, d = e.onAnimationEnd, f = e.animationInterpolateFn, p = e.animationMatchBy, m = e.shouldUpdatePreviousRef, h = e.children, g = e.layout, _ = xd(n, r), v = CO(_, a), y = (t = v.startValue) == null ? null : t, b = SO(y, i, p == null ? hO : p);
	return /*#__PURE__*/ C.createElement(bd, {
		animationId: _,
		begin: s,
		duration: c,
		isActive: o,
		easing: l,
		onAnimationEnd: d,
		onAnimationStart: u,
		key: _
	}, (e) => {
		var t = y == null, n = i == null ? i : f(b, e, g), r = m ? m(e) : e > 0;
		return v.syncStepValue(n, e, r), n == null ? null : h(n, e, t);
	});
}
//#endregion
//#region node_modules/recharts/es6/util/useId.js
var MO;
function NO(e, t) {
	return RO(e) || LO(e, t) || FO(e, t) || PO();
}
function PO() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function FO(e, t) {
	if (e) {
		if (typeof e == "string") return IO(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? IO(e, t) : void 0;
	}
}
function IO(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function LO(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function RO(e) {
	if (Array.isArray(e)) return e;
}
var zO = (MO = C.useId) == null ? () => NO(C.useState(() => Yt("uid-")), 1)[0] : MO;
//#endregion
//#region node_modules/recharts/es6/util/useUniqueId.js
function BO(e, t) {
	var n = zO();
	return t || (e ? `${e}-${n}` : n);
}
//#endregion
//#region node_modules/recharts/es6/context/RegisterGraphicalItemId.js
var VO = /*#__PURE__*/ (0, C.createContext)(void 0), HO = (e) => {
	var t = e.id, n = e.type, r = e.children, i = BO(`recharts-${n}`, t);
	return /*#__PURE__*/ C.createElement(VO.Provider, { value: i }, r(i));
}, UO = xo({
	name: "graphicalItems",
	initialState: {
		cartesianItems: [],
		polarItems: []
	},
	reducers: {
		addCartesianGraphicalItem: {
			reducer(e, t) {
				e.cartesianItems.push(H(t.payload));
			},
			prepare: ao()
		},
		replaceCartesianGraphicalItem: {
			reducer(e, t) {
				var n = t.payload, r = n.prev, i = n.next, a = Ga(e).cartesianItems.indexOf(H(r));
				a > -1 && (e.cartesianItems[a] = H(i));
			},
			prepare: ao()
		},
		removeCartesianGraphicalItem: {
			reducer(e, t) {
				var n = Ga(e).cartesianItems.indexOf(H(t.payload));
				n > -1 && e.cartesianItems.splice(n, 1);
			},
			prepare: ao()
		},
		addPolarGraphicalItem: {
			reducer(e, t) {
				e.polarItems.push(H(t.payload));
			},
			prepare: ao()
		},
		removePolarGraphicalItem: {
			reducer(e, t) {
				var n = Ga(e).polarItems.indexOf(H(t.payload));
				n > -1 && e.polarItems.splice(n, 1);
			},
			prepare: ao()
		},
		replacePolarGraphicalItem: {
			reducer(e, t) {
				var n = t.payload, r = n.prev, i = n.next, a = Ga(e).polarItems.indexOf(H(r));
				a > -1 && (e.polarItems[a] = H(i));
			},
			prepare: ao()
		}
	}
}), WO = UO.actions, GO = WO.addCartesianGraphicalItem, KO = WO.replaceCartesianGraphicalItem, qO = WO.removeCartesianGraphicalItem;
WO.addPolarGraphicalItem, WO.removePolarGraphicalItem, WO.replacePolarGraphicalItem;
var JO = UO.reducer, YO = /*#__PURE__*/ (0, C.memo)((e) => {
	var t = kr(), n = (0, C.useRef)(null);
	return (0, C.useLayoutEffect)(() => {
		n.current === null ? t(GO(e)) : n.current !== e && t(KO({
			prev: n.current,
			next: e
		})), n.current = e;
	}, [t, e]), (0, C.useLayoutEffect)(() => () => {
		n.current && (t(qO(n.current)), n.current = null);
	}, [t]), null;
});
//#endregion
//#region node_modules/recharts/es6/state/cartesianAxisSlice.js
function XO(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function ZO(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? XO(Object(n), !0).forEach(function(t) {
			QO(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : XO(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function QO(e, t, n) {
	return (t = $O(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function $O(e) {
	var t = ek(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function ek(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var tk = xo({
	name: "cartesianAxis",
	initialState: {
		xAxis: {},
		yAxis: {},
		zAxis: {}
	},
	reducers: {
		addXAxis: {
			reducer(e, t) {
				e.xAxis[t.payload.id] = H(t.payload);
			},
			prepare: ao()
		},
		replaceXAxis: {
			reducer(e, t) {
				var n = t.payload, r = n.prev, i = n.next;
				e.xAxis[r.id] !== void 0 && (r.id !== i.id && delete e.xAxis[r.id], e.xAxis[i.id] = H(i));
			},
			prepare: ao()
		},
		removeXAxis: {
			reducer(e, t) {
				delete e.xAxis[t.payload.id];
			},
			prepare: ao()
		},
		addYAxis: {
			reducer(e, t) {
				e.yAxis[t.payload.id] = H(t.payload);
			},
			prepare: ao()
		},
		replaceYAxis: {
			reducer(e, t) {
				var n = t.payload, r = n.prev, i = n.next;
				e.yAxis[r.id] !== void 0 && (r.id !== i.id && delete e.yAxis[r.id], e.yAxis[i.id] = H(i));
			},
			prepare: ao()
		},
		removeYAxis: {
			reducer(e, t) {
				delete e.yAxis[t.payload.id];
			},
			prepare: ao()
		},
		addZAxis: {
			reducer(e, t) {
				e.zAxis[t.payload.id] = H(t.payload);
			},
			prepare: ao()
		},
		replaceZAxis: {
			reducer(e, t) {
				var n = t.payload, r = n.prev, i = n.next;
				e.zAxis[r.id] !== void 0 && (r.id !== i.id && delete e.zAxis[r.id], e.zAxis[i.id] = H(i));
			},
			prepare: ao()
		},
		removeZAxis: {
			reducer(e, t) {
				delete e.zAxis[t.payload.id];
			},
			prepare: ao()
		},
		updateYAxisWidth(e, t) {
			var n = t.payload, r = n.id, i = n.width, a = e.yAxis[r];
			if (a) {
				var o, s = a.widthHistory || [];
				if (s.length === 3 && s[0] === s[2] && i === s[1] && i !== a.width && Math.abs(i - ((o = s[0]) == null ? 0 : o)) <= 1) return;
				var c = [...s, i].slice(-3);
				e.yAxis[r] = ZO(ZO({}, a), {}, {
					width: i,
					widthHistory: c
				});
			}
		}
	}
}), nk = tk.actions, rk = nk.addXAxis, ik = nk.replaceXAxis, ak = nk.removeXAxis, ok = nk.addYAxis, sk = nk.replaceYAxis, ck = nk.removeYAxis;
nk.addZAxis, nk.replaceZAxis, nk.removeZAxis;
var lk = nk.updateYAxisWidth, uk = tk.reducer, dk = R([
	R([ic], (e) => ({
		top: e.top,
		bottom: e.bottom,
		left: e.left,
		right: e.right
	})),
	Vs,
	Hs
], (e, t, n) => {
	if (!(!e || t == null || n == null)) return {
		x: e.left,
		y: e.top,
		width: Math.max(0, t - e.left - e.right),
		height: Math.max(0, n - e.top - e.bottom)
	};
}), fk = () => L(dk);
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineBarSizeList.js
function pk(e, t) {
	return vk(e) || _k(e, t) || hk(e, t) || mk();
}
function mk() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function hk(e, t) {
	if (e) {
		if (typeof e == "string") return gk(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? gk(e, t) : void 0;
	}
}
function gk(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function _k(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function vk(e) {
	if (Array.isArray(e)) return e;
}
var yk = (e, t, n) => {
	var r = n == null ? e : n;
	if (!en(r)) return Xt(r, t, 0);
}, bk = (e, t, n) => {
	var r = {}, i = e.filter(qp), a = e.filter((e) => e.stackId == null), o = i.reduce((e, t) => {
		var n = e[t.stackId];
		return n == null && (n = []), n.push(t), e[t.stackId] = n, e;
	}, r), s = Object.entries(o).map((e) => {
		var r, i = pk(e, 2), a = i[0], o = i[1];
		return {
			stackId: a,
			dataKeys: o.map((e) => e.dataKey),
			barSize: yk(t, n, (r = o[0]) == null ? void 0 : r.barSize)
		};
	}), c = a.map((e) => ({
		stackId: void 0,
		dataKeys: [e.dataKey].filter((e) => e != null),
		barSize: yk(t, n, e.barSize)
	}));
	return [...s, ...c];
};
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineAllBarPositions.js
function xk(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Sk(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? xk(Object(n), !0).forEach(function(t) {
			Ck(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : xk(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Ck(e, t, n) {
	return (t = wk(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function wk(e) {
	var t = Tk(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Tk(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function Ek(e, t, n, r, i) {
	var a, o = r.length;
	if (!(o < 1)) {
		var s = Xt(e, n, 0, !0), c, l = [];
		if (U((a = r[0]) == null ? void 0 : a.barSize)) {
			var u = !1, d = n / o, f = r.reduce((e, t) => e + (t.barSize || 0), 0);
			f += (o - 1) * s, f >= n && (f -= (o - 1) * s, s = 0), f >= n && d > 0 && (u = !0, d *= .9, f = o * d);
			var p = {
				offset: Math.round((n - f) / 2) - s,
				size: 0
			};
			c = r.reduce((e, t) => {
				var n, r = {
					stackId: t.stackId,
					dataKeys: t.dataKeys,
					position: {
						offset: p.offset + p.size + s,
						size: u ? d : (n = t.barSize) == null ? 0 : n
					}
				}, i = [...e, r];
				return p = r.position, i;
			}, l);
		} else {
			var m = Xt(t, n, 0, !0);
			n - 2 * m - (o - 1) * s <= 0 && (s = 0);
			var h = (n - 2 * m - (o - 1) * s) / o;
			h > 1 && (h = Math.round(h));
			var g = U(i) ? Math.min(h, i) : h;
			c = r.reduce((e, t, n) => [...e, {
				stackId: t.stackId,
				dataKeys: t.dataKeys,
				position: {
					offset: m + (h + s) * n + (h - g) / 2,
					size: g
				}
			}], l);
		}
		return c;
	}
}
var Dk = (e, t, n, r, i, a, o) => {
	var s = en(o) ? t : o, c = Ek(n, r, i === a ? a : i, e, s);
	return i !== a && c != null && (c = c.map((e) => Sk(Sk({}, e), {}, { position: Sk(Sk({}, e.position), {}, { offset: e.position.offset - i / 2 }) }))), c;
}, Ok = (e, t) => {
	var n = Gp(t);
	if (!(!e || n == null || t == null)) {
		var r = t.stackId;
		if (r != null) {
			var i = e[r];
			if (i) {
				var a = i.stackedData;
				if (a) return a.find((e) => e.key === n);
			}
		}
	}
}, kk = (e, t) => {
	if (!(e == null || t == null)) {
		var n = e.find((e) => e.stackId === t.stackId && t.dataKey != null && e.dataKeys.includes(t.dataKey));
		if (n != null) return n.position;
	}
};
//#endregion
//#region node_modules/recharts/es6/zIndex/getZIndexFromUnknown.js
function Ak(e, t) {
	return e && typeof e == "object" && "zIndex" in e && typeof e.zIndex == "number" && U(e.zIndex) ? e.zIndex : t;
}
//#endregion
//#region node_modules/recharts/es6/context/chartDataContext.js
var jk = (e) => {
	var t = e.chartData, n = kr(), r = cc();
	return (0, C.useEffect)(() => r ? () => {} : (n(eT(t)), () => {
		n(eT(void 0));
	}), [
		t,
		n,
		r
	]), null;
}, Mk = {
	x: 0,
	y: 0,
	width: 0,
	height: 0,
	padding: {
		top: 0,
		right: 0,
		bottom: 0,
		left: 0
	}
}, Nk = xo({
	name: "brush",
	initialState: Mk,
	reducers: { setBrushSettings(e, t) {
		return t.payload == null ? Mk : t.payload;
	} }
});
Nk.actions.setBrushSettings;
var Pk = Nk.reducer;
//#endregion
//#region node_modules/recharts/es6/util/CartesianUtils.js
function Fk(e) {
	return (e % 180 + 180) % 180;
}
var Ik = function(e) {
	var t = e.width, n = e.height, r = Fk(arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : 0) * Math.PI / 180, i = Math.atan(n / t), a = r > i && r < Math.PI - i ? n / Math.sin(r) : t / Math.cos(r);
	return Math.abs(a);
}, Lk = xo({
	name: "referenceElements",
	initialState: {
		dots: [],
		areas: [],
		lines: []
	},
	reducers: {
		addDot: (e, t) => {
			e.dots.push(t.payload);
		},
		removeDot: (e, t) => {
			var n = Ga(e).dots.findIndex((e) => e === t.payload);
			n !== -1 && e.dots.splice(n, 1);
		},
		addArea: (e, t) => {
			e.areas.push(t.payload);
		},
		removeArea: (e, t) => {
			var n = Ga(e).areas.findIndex((e) => e === t.payload);
			n !== -1 && e.areas.splice(n, 1);
		},
		addLine: (e, t) => {
			e.lines.push(H(t.payload));
		},
		removeLine: (e, t) => {
			var n = Ga(e).lines.findIndex((e) => e === t.payload);
			n !== -1 && e.lines.splice(n, 1);
		}
	}
}), Rk = Lk.actions;
Rk.addDot, Rk.removeDot, Rk.addArea, Rk.removeArea, Rk.addLine, Rk.removeLine;
var zk = Lk.reducer;
//#endregion
//#region node_modules/recharts/es6/container/ClipPathProvider.js
function Bk(e, t) {
	return Gk(e) || Wk(e, t) || Hk(e, t) || Vk();
}
function Vk() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function Hk(e, t) {
	if (e) {
		if (typeof e == "string") return Uk(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? Uk(e, t) : void 0;
	}
}
function Uk(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function Wk(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function Gk(e) {
	if (Array.isArray(e)) return e;
}
var Kk = /*#__PURE__*/ (0, C.createContext)(void 0), qk = (e) => {
	var t = e.children, n = Bk((0, C.useState)(`${Yt("recharts")}-clip`), 1)[0], r = fk();
	if (r == null) return null;
	var i = r.x, a = r.y, o = r.width, s = r.height;
	return /*#__PURE__*/ C.createElement(Kk.Provider, { value: n }, /*#__PURE__*/ C.createElement("defs", null, /*#__PURE__*/ C.createElement("clipPath", { id: n }, /*#__PURE__*/ C.createElement("rect", {
		x: i,
		y: a,
		height: s,
		width: o
	}))), t);
};
//#endregion
//#region node_modules/recharts/es6/util/getEveryNth.js
function Jk(e, t) {
	if (t < 1) return [];
	if (t === 1) return e;
	for (var n = [], r = 0; r < e.length; r += t) {
		var i = e[r];
		i !== void 0 && n.push(i);
	}
	return n;
}
//#endregion
//#region node_modules/recharts/es6/util/TickUtils.js
function Yk(e, t, n) {
	return Ik({
		width: e.width + t.width,
		height: e.height + t.height
	}, n);
}
function Xk(e, t, n) {
	var r = n === "width", i = e.x, a = e.y, o = e.width, s = e.height;
	return t === 1 ? {
		start: r ? i : a,
		end: r ? i + o : a + s
	} : {
		start: r ? i + o : a + s,
		end: r ? i : a
	};
}
function Zk(e, t, n, r, i) {
	if (e * t < e * r || e * t > e * i) return !1;
	var a = n();
	return e * (t - e * a / 2 - r) >= 0 && e * (t + e * a / 2 - i) <= 0;
}
function Qk(e, t) {
	return Jk(e, t + 1);
}
//#endregion
//#region node_modules/recharts/es6/cartesian/getEquidistantTicks.js
function $k(e, t, n, r, i) {
	for (var a = (r || []).slice(), o = t.start, s = t.end, c = 0, l = 1, u = o, d = function() {
		var t = r == null ? void 0 : r[c];
		if (t === void 0) return { v: Jk(r, l) };
		var a = c, d, f = () => (d === void 0 && (d = n(t, a)), d), p = t.coordinate, m = c === 0 || Zk(e, p, f, u, s);
		m || (c = 0, u = o, l += 1), m && (u = p + e * (f() / 2 + i), c += l);
	}, f; l <= a.length;) if (f = d(), f) return f.v;
	return [];
}
function eA(e, t, n, r, i) {
	var a = (r || []).slice().length;
	if (a === 0) return [];
	for (var o = t.start, s = t.end, c = 1; c <= a; c++) {
		for (var l = (a - 1) % c, u = o, d = !0, f = function() {
			var t = r[m];
			if (t == null) return 0;
			var a = m, o, c = () => (o === void 0 && (o = n(t, a)), o), f = t.coordinate, p = m === l || Zk(e, f, c, u, s);
			if (!p) return d = !1, 1;
			p && (u = f + e * (c() / 2 + i));
		}, p, m = l; m < a && (p = f(), !(p !== 0 && p === 1)); m += c);
		if (d) {
			for (var h = [], g = l; g < a; g += c) {
				var _ = r[g];
				_ != null && h.push(_);
			}
			return h;
		}
	}
	return [];
}
//#endregion
//#region node_modules/recharts/es6/cartesian/getTicks.js
function tA(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function nA(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? tA(Object(n), !0).forEach(function(t) {
			rA(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : tA(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function rA(e, t, n) {
	return (t = iA(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function iA(e) {
	var t = aA(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function aA(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function oA(e, t, n, r, i) {
	for (var a = (r || []).slice(), o = a.length, s = t.start, c = t.end, l = function(t) {
		var r = a[t];
		if (r == null) return 1;
		var l = r, u, d = () => (u === void 0 && (u = n(r, t)), u);
		if (t === o - 1) {
			var f = e * (l.coordinate + e * d() / 2 - c);
			a[t] = l = nA(nA({}, l), {}, { tickCoord: f > 0 ? l.coordinate - f * e : l.coordinate });
		} else a[t] = l = nA(nA({}, l), {}, { tickCoord: l.coordinate });
		l.tickCoord != null && Zk(e, l.tickCoord, d, s, c) && (c = l.tickCoord - e * (d() / 2 + i), a[t] = nA(nA({}, l), {}, { isShow: !0 }));
	}, u = o - 1; u >= 0; u--) if (l(u)) continue;
	return a;
}
function sA(e, t, n, r, i, a) {
	var o = (r || []).slice(), s = o.length, c = t.start, l = t.end;
	if (a) {
		var u = r[s - 1];
		if (u != null) {
			var d = n(u, s - 1), f = e * (u.coordinate + e * d / 2 - l);
			o[s - 1] = u = nA(nA({}, u), {}, { tickCoord: f > 0 ? u.coordinate - f * e : u.coordinate }), u.tickCoord != null && Zk(e, u.tickCoord, () => d, c, l) && (l = u.tickCoord - e * (d / 2 + i), o[s - 1] = nA(nA({}, u), {}, { isShow: !0 }));
		}
	}
	for (var p = a ? s - 1 : s, m = function(t) {
		var r = o[t];
		if (r == null) return 1;
		var a = r, s, u = () => (s === void 0 && (s = n(r, t)), s);
		if (t === 0) {
			var d = e * (a.coordinate - e * u() / 2 - c);
			o[t] = a = nA(nA({}, a), {}, { tickCoord: d < 0 ? a.coordinate - d * e : a.coordinate });
		} else o[t] = a = nA(nA({}, a), {}, { tickCoord: a.coordinate });
		a.tickCoord != null && Zk(e, a.tickCoord, u, c, l) && (c = a.tickCoord + e * (u() / 2 + i), o[t] = nA(nA({}, a), {}, { isShow: !0 }));
	}, h = 0; h < p; h++) if (m(h)) continue;
	return o;
}
function cA(e, t, n) {
	var r = e.tick, i = e.ticks, a = e.viewBox, o = e.minTickGap, s = e.orientation, c = e.interval, l = e.tickFormatter, u = e.unit, d = e.angle;
	if (!i || !i.length || !r) return [];
	if (I(c) || Kl.isSsr) {
		var f;
		return (f = Qk(i, I(c) ? c : 0)) == null ? [] : f;
	}
	var p = [], m = s === "top" || s === "bottom" ? "width" : "height", h = u && m === "width" ? qT(u, {
		fontSize: t,
		letterSpacing: n
	}) : {
		width: 0,
		height: 0
	}, g = (e, r) => {
		var i = typeof l == "function" ? l(e.value, r) : e.value;
		return m === "width" ? Yk(qT(i, {
			fontSize: t,
			letterSpacing: n
		}), h, d) : qT(i, {
			fontSize: t,
			letterSpacing: n
		})[m];
	}, _ = i[0], v = i[1], y = i.length >= 2 && _ != null && v != null ? Gt(v.coordinate - _.coordinate) : 1, b = Xk(a, y, m);
	return c === "equidistantPreserveStart" ? $k(y, b, g, i, o) : c === "equidistantPreserveEnd" ? eA(y, b, g, i, o) : (p = c === "preserveStart" || c === "preserveStartEnd" ? sA(y, b, g, i, o, c === "preserveStartEnd") : oA(y, b, g, i, o), p.filter((e) => e.isShow));
}
//#endregion
//#region node_modules/recharts/es6/util/YAxisUtils.js
var lA = (e) => {
	var t = e.ticks, n = e.label, r = e.labelGapWithTick, i = r === void 0 ? 5 : r, a = e.tickSize, o = a === void 0 ? 0 : a, s = e.tickMargin, c = s === void 0 ? 0 : s, l = 0;
	if (t) {
		Array.from(t).forEach((e) => {
			if (e) {
				var t = e.getBoundingClientRect();
				t.width > l && (l = t.width);
			}
		});
		var u = n ? n.getBoundingClientRect().width : 0, d = o + c, f = l + d + u + (n ? i : 0);
		return Math.round(f);
	}
	return 0;
}, uA = xo({
	name: "renderedTicks",
	initialState: {
		xAxis: {},
		yAxis: {}
	},
	reducers: {
		setRenderedTicks: (e, t) => {
			var n = t.payload, r = n.axisType, i = n.axisId, a = n.ticks;
			e[r][i] = H(a);
		},
		removeRenderedTicks: (e, t) => {
			var n = t.payload, r = n.axisType, i = n.axisId;
			delete e[r][i];
		}
	}
}), dA = uA.actions, fA = dA.setRenderedTicks, pA = dA.removeRenderedTicks, mA = uA.reducer, hA = [
	"axisLine",
	"width",
	"height",
	"className",
	"hide",
	"ticks",
	"axisType",
	"axisId"
];
function gA(e, t) {
	return xA(e) || bA(e, t) || vA(e, t) || _A();
}
function _A() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function vA(e, t) {
	if (e) {
		if (typeof e == "string") return yA(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? yA(e, t) : void 0;
	}
}
function yA(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function bA(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function xA(e) {
	if (Array.isArray(e)) return e;
}
function SA(e, t) {
	if (e == null) return {};
	var n, r, i = CA(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function CA(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function wA() {
	return wA = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, wA.apply(null, arguments);
}
function TA(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function EA(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? TA(Object(n), !0).forEach(function(t) {
			DA(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : TA(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function DA(e, t, n) {
	return (t = OA(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function OA(e) {
	var t = kA(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function kA(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var AA = {
	x: 0,
	y: 0,
	width: 0,
	height: 0,
	viewBox: {
		x: 0,
		y: 0,
		width: 0,
		height: 0
	},
	orientation: "bottom",
	ticks: [],
	stroke: "#666",
	tickLine: !0,
	axisLine: !0,
	tick: !0,
	mirror: !1,
	minTickGap: 5,
	tickSize: 6,
	tickMargin: 2,
	interval: "preserveEnd",
	zIndex: Sp.axis
};
function jA(e) {
	var t = e.x, n = e.y, r = e.width, i = e.height, a = e.orientation, o = e.mirror, s = e.axisLine, c = e.otherSvgProps;
	if (!s) return null;
	var l = EA(EA(EA({}, c), xe(s)), {}, { fill: "none" });
	if (a === "top" || a === "bottom") {
		var u = +(a === "top" && !o || a === "bottom" && o);
		l = EA(EA({}, l), {}, {
			x1: t,
			y1: n + u * i,
			x2: t + r,
			y2: n + u * i
		});
	} else {
		var d = +(a === "left" && !o || a === "right" && o);
		l = EA(EA({}, l), {}, {
			x1: t + d * r,
			y1: n,
			x2: t + d * r,
			y2: n + i
		});
	}
	return /*#__PURE__*/ C.createElement("line", wA({}, l, { className: he("recharts-cartesian-axis-line", Bt(s, "className")) }));
}
function MA(e, t, n, r, i, a, o, s, c) {
	var l, u, d, f, p, m, h = s ? -1 : 1, g = e.tickSize || o, _ = I(e.tickCoord) ? e.tickCoord : e.coordinate;
	switch (a) {
		case "top":
			l = u = e.coordinate, f = n + +!s * i, d = f - h * g, m = d - h * c, p = _;
			break;
		case "left":
			d = f = e.coordinate, u = t + +!s * r, l = u - h * g, p = l - h * c, m = _;
			break;
		case "right":
			d = f = e.coordinate, u = t + +s * r, l = u + h * g, p = l + h * c, m = _;
			break;
		default:
			l = u = e.coordinate, f = n + +s * i, d = f + h * g, m = d + h * c, p = _;
			break;
	}
	return {
		line: {
			x1: l,
			y1: d,
			x2: u,
			y2: f
		},
		tick: {
			x: p,
			y: m
		}
	};
}
function NA(e, t) {
	switch (e) {
		case "left": return t ? "start" : "end";
		case "right": return t ? "end" : "start";
		default: return "middle";
	}
}
function PA(e, t) {
	switch (e) {
		case "left":
		case "right": return "middle";
		case "top": return t ? "start" : "end";
		default: return t ? "end" : "start";
	}
}
function FA(e) {
	var t = e.option, n = e.tickProps, r = e.value, i, a = he(n.className, "recharts-cartesian-axis-tick-value");
	if (/*#__PURE__*/ C.isValidElement(t)) i = /*#__PURE__*/ C.cloneElement(t, EA(EA({}, n), {}, { className: a }));
	else if (typeof t == "function") i = t(EA(EA({}, n), {}, { className: a }));
	else {
		var o = "recharts-cartesian-axis-tick-value";
		typeof t != "boolean" && (o = he(o, zD(t))), i = /*#__PURE__*/ C.createElement(WE, wA({}, n, { className: o }), r);
	}
	return i;
}
function IA(e) {
	var t = e.ticks, n = e.axisType, r = e.axisId, i = kr();
	return (0, C.useEffect)(() => r == null || n == null ? rn : (i(fA({
		ticks: t.map((e) => ({
			value: e.value,
			coordinate: e.coordinate,
			offset: e.offset,
			index: e.index
		})),
		axisId: r,
		axisType: n
	})), () => {
		i(pA({
			axisId: r,
			axisType: n
		}));
	}), [
		i,
		t,
		r,
		n
	]), null;
}
var LA = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.ticks, r = n === void 0 ? [] : n, i = e.tick, a = e.tickLine, o = e.stroke, s = e.tickFormatter, c = e.unit, l = e.padding, u = e.tickTextProps, d = e.orientation, f = e.mirror, p = e.x, m = e.y, h = e.width, g = e.height, _ = e.tickSize, v = e.tickMargin, y = e.fontSize, b = e.letterSpacing, x = e.getTicksConfig, S = e.events, w = e.axisType, T = e.axisId, E = cA(EA(EA({}, x), {}, { ticks: r }), y, b), D = xe(x), O = Se(i), k = NE(D.textAnchor) ? D.textAnchor : NA(d, f), A = PA(d, f), j = {};
	typeof a == "object" && (j = a);
	var M = EA(EA({}, D), {}, { fill: "none" }, j), N = E.map((e) => EA({ entry: e }, MA(e, p, m, h, g, d, _, f, v))), P = N.map((e) => {
		var t = e.entry, n = e.line;
		return /*#__PURE__*/ C.createElement(Ne, {
			className: "recharts-cartesian-axis-tick",
			key: `tick-${t.value}-${t.coordinate}-${t.tickCoord}`
		}, a && /*#__PURE__*/ C.createElement("line", wA({}, M, n, { className: he("recharts-cartesian-axis-tick-line", Bt(a, "className")) })));
	}), ee = N.map((e, t) => {
		var n, r, a = e.entry, d = e.tick, f = EA(EA({}, EA(EA(EA(EA({ verticalAnchor: A }, D), {}, {
			textAnchor: k,
			stroke: "none",
			fill: o
		}, d), {}, {
			index: t,
			payload: a,
			visibleTicksCount: E.length,
			tickFormatter: s,
			padding: l
		}, u), {}, { angle: (n = (r = u == null ? void 0 : u.angle) == null ? D.angle : r) == null ? 0 : n })), O);
		return /*#__PURE__*/ C.createElement(Ne, wA({
			className: "recharts-cartesian-axis-tick-label",
			key: `tick-label-${a.value}-${a.coordinate}-${a.tickCoord}`
		}, cn(S, a, t)), i && /*#__PURE__*/ C.createElement(FA, {
			option: i,
			tickProps: f,
			value: `${typeof s == "function" ? s(a.value, t) : a.value}${c || ""}`
		}));
	});
	return /*#__PURE__*/ C.createElement("g", { className: `recharts-cartesian-axis-ticks recharts-${w}-ticks` }, /*#__PURE__*/ C.createElement(IA, {
		ticks: E,
		axisId: T,
		axisType: w
	}), ee.length > 0 && /*#__PURE__*/ C.createElement(jw, { zIndex: Sp.label }, /*#__PURE__*/ C.createElement("g", {
		className: `recharts-cartesian-axis-tick-labels recharts-${w}-tick-labels`,
		ref: t
	}, ee)), P.length > 0 && /*#__PURE__*/ C.createElement("g", { className: `recharts-cartesian-axis-tick-lines recharts-${w}-tick-lines` }, P));
}), RA = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.axisLine, r = e.width, i = e.height, a = e.className, o = e.hide, s = e.ticks, c = e.axisType, l = e.axisId, u = SA(e, hA), d = gA((0, C.useState)(""), 2), f = d[0], p = d[1], m = gA((0, C.useState)(""), 2), h = m[0], g = m[1], _ = (0, C.useRef)(null);
	(0, C.useImperativeHandle)(t, () => ({ getCalculatedWidth: () => {
		var t;
		return lA({
			ticks: _.current,
			label: (t = e.labelRef) == null ? void 0 : t.current,
			labelGapWithTick: 5,
			tickSize: e.tickSize,
			tickMargin: e.tickMargin
		});
	} }));
	var v = (0, C.useCallback)((e) => {
		if (e) {
			var t = e.getElementsByClassName("recharts-cartesian-axis-tick-value");
			_.current = t;
			var n = t[0];
			if (n) {
				var r = window.getComputedStyle(n), i = r.fontSize, a = r.letterSpacing;
				(i !== f || a !== h) && (p(i), g(a));
			}
		}
	}, [f, h]);
	return o || r != null && r <= 0 || i != null && i <= 0 ? null : /*#__PURE__*/ C.createElement(jw, { zIndex: e.zIndex }, /*#__PURE__*/ C.createElement(Ne, { className: he("recharts-cartesian-axis", a) }, /*#__PURE__*/ C.createElement(jA, {
		x: e.x,
		y: e.y,
		width: r,
		height: i,
		orientation: e.orientation,
		mirror: e.mirror,
		axisLine: n,
		otherSvgProps: xe(e)
	}), /*#__PURE__*/ C.createElement(LA, {
		ref: v,
		axisType: c,
		events: u,
		fontSize: f,
		getTicksConfig: e,
		height: e.height,
		letterSpacing: h,
		mirror: e.mirror,
		orientation: e.orientation,
		padding: e.padding,
		stroke: e.stroke,
		tick: e.tick,
		tickFormatter: e.tickFormatter,
		tickLine: e.tickLine,
		tickMargin: e.tickMargin,
		tickSize: e.tickSize,
		tickTextProps: e.tickTextProps,
		ticks: s,
		unit: e.unit,
		width: e.width,
		x: e.x,
		y: e.y,
		axisId: l
	}), /*#__PURE__*/ C.createElement(cD, {
		x: e.x,
		y: e.y,
		width: e.width,
		height: e.height,
		lowerWidth: e.width,
		upperWidth: e.width
	}, /*#__PURE__*/ C.createElement(SD, {
		label: e.label,
		labelRef: e.labelRef
	}), e.children)));
}), zA = /*#__PURE__*/ C.forwardRef((e, t) => {
	var n = mn(e, AA);
	return /*#__PURE__*/ C.createElement(RA, wA({}, n, { ref: t }));
});
zA.displayName = "CartesianAxis";
//#endregion
//#region node_modules/recharts/es6/state/errorBarSlice.js
var BA = xo({
	name: "errorBars",
	initialState: {},
	reducers: {
		addErrorBar: (e, t) => {
			var n = t.payload, r = n.itemId, i = n.errorBar;
			e[r] || (e[r] = []), e[r].push(i);
		},
		replaceErrorBar: (e, t) => {
			var n = t.payload, r = n.itemId, i = n.prev, a = n.next;
			e[r] && (e[r] = e[r].map((e) => e.dataKey === i.dataKey && e.direction === i.direction ? a : e));
		},
		removeErrorBar: (e, t) => {
			var n = t.payload, r = n.itemId, i = n.errorBar;
			e[r] && (e[r] = e[r].filter((e) => e.dataKey !== i.dataKey || e.direction !== i.direction));
		}
	}
}), VA = BA.actions;
VA.addErrorBar, VA.replaceErrorBar, VA.removeErrorBar;
var HA = BA.reducer, UA = ["children"];
function WA(e, t) {
	if (e == null) return {};
	var n, r, i = GA(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function GA(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var KA = /*#__PURE__*/ (0, C.createContext)({
	data: [],
	xAxisId: "xAxis-0",
	yAxisId: "yAxis-0",
	dataPointFormatter: () => ({
		x: 0,
		y: 0,
		value: 0
	}),
	errorBarOffset: 0
});
function qA(e) {
	var t = e.children, n = WA(e, UA);
	return /*#__PURE__*/ C.createElement(KA.Provider, { value: n }, t);
}
//#endregion
//#region node_modules/recharts/es6/cartesian/GraphicalItemClipPath.js
function JA(e, t) {
	var n, r, i = L((t) => rb(t, e)), a = L((e) => ob(e, t)), o = (n = i == null ? void 0 : i.allowDataOverflow) == null ? tb.allowDataOverflow : n, s = (r = a == null ? void 0 : a.allowDataOverflow) == null ? ib.allowDataOverflow : r;
	return {
		needClip: o || s,
		needClipX: o,
		needClipY: s
	};
}
function YA(e) {
	var t = e.xAxisId, n = e.yAxisId, r = e.clipPathId, i = fk(), a = JA(t, n), o = a.needClipX, s = a.needClipY, c = a.needClip, l = L((e) => Ax(e, t, !1)), u = L((e) => jx(e, n, !1));
	if (!c || !i) return null;
	var d = i.x, f = i.y, p = i.width, m = i.height, h = o && l ? Math.min(l[0], l[1]) : d - p / 2, g = s && u ? Math.min(u[0], u[1]) : f - m / 2, _ = o && l ? Math.abs(l[1] - l[0]) : p * 2, v = s && u ? Math.abs(u[1] - u[0]) : m * 2;
	return /*#__PURE__*/ C.createElement("clipPath", { id: `clipPath-${r}` }, /*#__PURE__*/ C.createElement("rect", {
		x: h,
		y: g,
		width: _,
		height: v
	}));
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/graphicalItemSelectors.js
function XA(e, t) {
	var n, r;
	return (n = (r = e.graphicalItems.cartesianItems.find((e) => e.id === t)) == null ? void 0 : r.xAxisId) == null ? 0 : n;
}
function ZA(e, t) {
	var n, r;
	return (n = (r = e.graphicalItems.cartesianItems.find((e) => e.id === t)) == null ? void 0 : r.yAxisId) == null ? 0 : n;
}
//#endregion
//#region node_modules/tiny-invariant/dist/esm/tiny-invariant.js
var QA = "Invariant failed";
function $A(e, t) {
	if (!e) throw Error(QA);
}
//#endregion
//#region node_modules/recharts/es6/util/BarUtils.js
var ej = ["option"];
function tj(e, t) {
	if (e == null) return {};
	var n, r, i = nj(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function nj(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var rj = $d;
function ij(e) {
	var t = e.option, n = tj(e, ej);
	return /*#__PURE__*/ C.createElement(rO, {
		option: t,
		DefaultShape: rj,
		shapeProps: n,
		activeClassName: "recharts-active-bar",
		inActiveClassName: "recharts-inactive-bar"
	});
}
var aj = function(e) {
	var t = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : 0;
	return (n, r) => {
		if (I(e)) return e;
		var i = I(n) || en(n);
		return i ? e(n, r) : (!i && $A(!1, `minPointSize callback function received a value with type of ${typeof n}. Currently only numbers or null/undefined are supported.`), t);
	};
}, oj = (e, t, n) => n, sj = R([mb, (e, t) => t], (e, t) => e.filter((e) => e.type === "bar").find((e) => e.id === t)), cj = R([sj], (e) => e == null ? void 0 : e.maxBarSize), lj = (e, t, n, r) => r, uj = R([
	q,
	mb,
	XA,
	ZA,
	oj
], (e, t, n, r, i) => t.filter((t) => e === "horizontal" ? t.xAxisId === n : t.yAxisId === r).filter((e) => e.isPanorama === i).filter((e) => e.hide === !1).filter((e) => e.type === "bar")), dj = (e, t, n) => {
	var r = q(e), i = XA(e, t), a = ZA(e, t);
	if (!(i == null || a == null)) return r === "horizontal" ? Bb(e, "yAxis", a, n) : Bb(e, "xAxis", i, n);
}, fj = R([
	uj,
	hp,
	(e, t) => {
		var n = q(e), r = XA(e, t), i = ZA(e, t);
		if (!(r == null || i == null)) return n === "horizontal" ? $x(e, "xAxis", r) : $x(e, "yAxis", i);
	}
], bk), pj = (e, t, n) => {
	var r, i, a = sj(e, t);
	if (a == null) return 0;
	var o = XA(e, t), s = ZA(e, t);
	if (o == null || s == null) return 0;
	var c = q(e), l = fp(e), u = a.maxBarSize, d = en(u) ? l : u, f, p;
	return c === "horizontal" ? (f = iS(e, "xAxis", o, n), p = rS(e, "xAxis", o, n)) : (f = iS(e, "yAxis", s, n), p = rS(e, "yAxis", s, n)), (r = (i = Is(f, p, !0)) == null ? d : i) == null ? 0 : r;
}, mj = (e, t, n) => {
	var r = q(e), i = XA(e, t), a = ZA(e, t);
	if (!(i == null || a == null)) {
		var o, s;
		return r === "horizontal" ? (o = iS(e, "xAxis", i, n), s = rS(e, "xAxis", i, n)) : (o = iS(e, "yAxis", a, n), s = rS(e, "yAxis", a, n)), Is(o, s);
	}
}, hj = R([
	ic,
	oc,
	(e, t, n) => {
		var r = XA(e, t);
		if (r != null) return iS(e, "xAxis", r, n);
	},
	(e, t, n) => {
		var r = ZA(e, t);
		if (r != null) return iS(e, "yAxis", r, n);
	},
	(e, t, n) => {
		var r = XA(e, t);
		if (r != null) return rS(e, "xAxis", r, n);
	},
	(e, t, n) => {
		var r = ZA(e, t);
		if (r != null) return rS(e, "yAxis", r, n);
	},
	R([R([
		fj,
		fp,
		pp,
		mp,
		pj,
		mj,
		cj
	], Dk), sj], kk),
	q,
	Rf,
	mj,
	R([dj, sj], Ok),
	sj,
	lj
], (e, t, n, r, i, a, o, s, c, l, u, d, f) => {
	var p = c.chartData, m = c.dataStartIndex, h = c.dataEndIndex;
	if (!(d == null || o == null || t == null || s !== "horizontal" && s !== "vertical" || n == null || r == null || i == null || a == null || l == null)) {
		var g = d.data, _ = g != null && g.length > 0 ? g : p == null ? void 0 : p.slice(m, h + 1);
		if (_ != null) return iM({
			layout: s,
			barSettings: d,
			pos: o,
			parentViewBox: t,
			bandSize: l,
			xAxis: n,
			yAxis: r,
			xAxisTicks: i,
			yAxisTicks: a,
			stackedData: u,
			displayedData: _,
			offset: e,
			cells: f,
			dataStartIndex: m
		});
	}
}), gj = ["index"];
function _j() {
	return _j = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, _j.apply(null, arguments);
}
function vj(e, t) {
	if (e == null) return {};
	var n, r, i = yj(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function yj(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var bj = /*#__PURE__*/ (0, C.createContext)(void 0), xj = (e) => {
	var t = (0, C.useContext)(bj);
	if (t != null) return t.stackId;
	if (e != null) return Os(e);
}, Sj = (e, t) => `recharts-bar-stack-clip-path-${e}-${t}`, Cj = (e) => {
	var t = (0, C.useContext)(bj);
	if (t != null) {
		var n = t.stackId;
		return `url(#${Sj(n, e)})`;
	}
}, wj = (e) => {
	var t = e.index, n = vj(e, gj), r = Cj(t);
	return /*#__PURE__*/ C.createElement(Ne, _j({
		className: "recharts-bar-stack-layer",
		clipPath: r
	}, n));
}, Tj = [
	"onMouseEnter",
	"onMouseLeave",
	"onClick"
], Ej = [
	"value",
	"background",
	"tooltipPosition"
], Dj = ["id"], Oj = [
	"onMouseEnter",
	"onClick",
	"onMouseLeave"
];
function kj(e, t) {
	return Pj(e) || Nj(e, t) || jj(e, t) || Aj();
}
function Aj() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function jj(e, t) {
	if (e) {
		if (typeof e == "string") return Mj(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? Mj(e, t) : void 0;
	}
}
function Mj(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function Nj(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function Pj(e) {
	if (Array.isArray(e)) return e;
}
function Fj() {
	return Fj = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, Fj.apply(null, arguments);
}
function Ij(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Lj(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Ij(Object(n), !0).forEach(function(t) {
			Rj(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Ij(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Rj(e, t, n) {
	return (t = zj(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function zj(e) {
	var t = Bj(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Bj(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function Vj(e, t) {
	if (e == null) return {};
	var n, r, i = Hj(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function Hj(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var Uj = (e) => {
	var t = e.dataKey, n = e.name, r = e.fill, i = e.legendType;
	return [{
		inactive: e.hide,
		dataKey: t,
		type: i,
		color: r,
		value: Rs(n, t),
		payload: e
	}];
}, Wj = /*#__PURE__*/ C.memo((e) => {
	var t = e.dataKey, n = e.stroke, r = e.strokeWidth, i = e.fill, a = e.name, o = e.hide, s = e.unit, c = e.formatter, l = e.tooltipType, u = e.id, d = {
		dataDefinedOnItem: void 0,
		getPosition: rn,
		settings: {
			stroke: n,
			strokeWidth: r,
			fill: i,
			dataKey: t,
			nameKey: void 0,
			name: Rs(a, t),
			hide: o,
			type: l,
			color: i,
			unit: s,
			formatter: c,
			graphicalItemId: u
		}
	};
	return /*#__PURE__*/ C.createElement(sO, { tooltipEntrySettings: d });
});
function Gj(e) {
	var t = L(DC), n = e.data, r = e.dataKey, i = e.background, a = e.allOtherBarProps, o = a.onMouseEnter, s = a.onMouseLeave, c = a.onClick, l = Vj(a, Tj), u = iO(o, r, a.id), d = aO(s), f = oO(c, r, a.id);
	if (!i || n == null) return null;
	var p = Se(i);
	return /*#__PURE__*/ C.createElement(jw, { zIndex: Ak(i, Sp.barBackground) }, n.map((e, n) => {
		e.value;
		var a = e.background;
		e.tooltipPosition;
		var o = Vj(e, Ej);
		if (!a) return null;
		var s = u(e, e.originalDataIndex), c = d(e, e.originalDataIndex), m = f(e, e.originalDataIndex), h = Lj(Lj(Lj(Lj(Lj({
			option: i,
			isActive: String(e.originalDataIndex) === t
		}, o), {}, { fill: "#eee" }, a), p), cn(l, e, n)), {}, {
			onMouseEnter: s,
			onMouseLeave: c,
			onClick: m,
			dataKey: r,
			index: n,
			className: "recharts-bar-background-rectangle"
		});
		return /*#__PURE__*/ C.createElement(ij, Fj({ key: `background-bar-${n}` }, h));
	}));
}
function Kj(e) {
	var t = e.showLabels, n = e.children, r = e.rects, i = r == null ? void 0 : r.map((e) => {
		var t = {
			x: e.x,
			y: e.y,
			width: e.width,
			lowerWidth: e.width,
			upperWidth: e.width,
			height: e.height
		};
		return Lj(Lj({}, t), {}, {
			value: e.value,
			payload: e.payload,
			parentViewBox: e.parentViewBox,
			viewBox: t,
			fill: e.fill
		});
	});
	return /*#__PURE__*/ C.createElement(AD, { value: t ? i : void 0 }, n);
}
function qj(e) {
	var t = e.shape, n = e.activeBar, r = e.baseProps, i = e.entry, a = e.index, o = e.dataKey, s = L(DC), c = L(kC), l = n && String(i.originalDataIndex) === s && (c == null || o === c), u = kj((0, C.useState)(!1), 2), d = u[0], f = u[1], p = kj((0, C.useState)(!1), 2), m = p[0], h = p[1];
	(0, C.useEffect)(() => {
		var e;
		return l ? (f(!0), e = requestAnimationFrame(() => {
			h(!0);
		})) : h(!1), () => {
			cancelAnimationFrame(e);
		};
	}, [l]);
	var g = (0, C.useCallback)(() => {
		l || f(!1);
	}, [l]), _ = l && m, v = l || d, y = l ? n === !0 ? t : n : t, b = /*#__PURE__*/ C.createElement(ij, Fj({}, r, { name: String(r.name) }, i, {
		isActive: _,
		option: y,
		index: a,
		dataKey: o,
		animationElapsedTime: e.animationElapsedTime,
		isAnimating: e.isAnimating,
		isEntrance: e.isEntrance,
		onTransitionEnd: g
	}));
	return v ? /*#__PURE__*/ C.createElement(jw, { zIndex: Sp.activeBar }, /*#__PURE__*/ C.createElement(wj, { index: i.originalDataIndex }, b)) : b;
}
function Jj(e) {
	var t = e.shape, n = e.baseProps, r = e.entry, i = e.index, a = e.dataKey;
	return /*#__PURE__*/ C.createElement(ij, Fj({}, n, { name: String(n.name) }, r, {
		isActive: !1,
		option: t,
		index: i,
		dataKey: a,
		animationElapsedTime: e.animationElapsedTime,
		isAnimating: e.isAnimating,
		isEntrance: e.isEntrance
	}));
}
function Yj(e) {
	var t, n = e.data, r = e.props, i = e.animationElapsedTime, a = e.isAnimating, o = e.isEntrance, s = (t = xe(r)) == null ? {} : t, c = s.id, l = Vj(s, Dj), u = r.shape, d = r.dataKey, f = r.activeBar, p = r.onMouseEnter, m = r.onClick, h = r.onMouseLeave, g = Vj(r, Oj), _ = iO(p, d, c), v = aO(h), y = oO(m, d, c);
	return n ? /*#__PURE__*/ C.createElement(C.Fragment, null, n.map((e, t) => /*#__PURE__*/ C.createElement(wj, Fj({
		index: e.originalDataIndex,
		key: `rectangle-${e == null ? void 0 : e.x}-${e == null ? void 0 : e.y}-${e == null ? void 0 : e.value}-${t}`,
		className: "recharts-bar-rectangle"
	}, cn(g, e, t), {
		onMouseEnter: _(e, e.originalDataIndex),
		onMouseLeave: v(e, e.originalDataIndex),
		onClick: y(e, e.originalDataIndex)
	}), f ? /*#__PURE__*/ C.createElement(qj, {
		shape: u,
		activeBar: f,
		baseProps: l,
		entry: e,
		index: t,
		dataKey: d,
		animationElapsedTime: i,
		isAnimating: a,
		isEntrance: o
	}) : /*#__PURE__*/ C.createElement(Jj, {
		shape: u,
		baseProps: l,
		entry: e,
		index: t,
		dataKey: d,
		animationElapsedTime: i,
		isAnimating: a,
		isEntrance: o
	})))) : null;
}
var Xj = (e, t, n) => e == null ? [] : t === 1 ? e.flatMap((e) => e.status === "removed" ? [] : [e.next]) : e.flatMap((e) => {
	if (e.status === "removed") return n === "horizontal" ? [Lj(Lj({}, e.prev), {}, {
		height: Qt(e.prev.height, 0, t),
		y: Qt(e.prev.y, e.prev.y + e.prev.height, t)
	})] : [Lj(Lj({}, e.prev), {}, { width: Qt(e.prev.width, 0, t) })];
	if (e.status === "matched") return [Lj(Lj({}, e.next), {}, {
		x: Qt(e.prev.x, e.next.x, t),
		y: Qt(e.prev.y, e.next.y, t),
		width: Qt(e.prev.width, e.next.width, t),
		height: Qt(e.prev.height, e.next.height, t)
	})];
	var r = e.next;
	return n === "horizontal" ? [Lj(Lj({}, r), {}, {
		height: Qt(0, r.height, t),
		y: Qt(r.stackedBarStart, r.y, t)
	})] : [Lj(Lj({}, r), {}, {
		width: Qt(0, r.width, t),
		x: Qt(r.stackedBarStart, r.x, t)
	})];
});
function Zj(e) {
	var t = e.props, n = e.previousRectanglesRef, r = t.data, i = t.isAnimationActive, a = t.animationBegin, o = t.animationDuration, s = t.animationEasing, c = t.animationInterpolateFn, l = t.layout, u = AO(t.onAnimationStart, t.onAnimationEnd), d = u.isAnimating, f = u.handleAnimationStart, p = u.handleAnimationEnd;
	return /*#__PURE__*/ C.createElement(Kj, {
		showLabels: !d,
		rects: r
	}, /*#__PURE__*/ C.createElement(jO, {
		animationInput: r,
		animationIdPrefix: "recharts-bar-",
		items: r,
		previousItemsRef: n,
		isAnimationActive: i,
		animationBegin: a,
		animationDuration: o,
		animationEasing: s,
		onAnimationStart: f,
		onAnimationEnd: p,
		animationInterpolateFn: c,
		animationMatchBy: t.animationMatchBy,
		layout: l
	}, (e, n, r) => /*#__PURE__*/ C.createElement(Ne, null, /*#__PURE__*/ C.createElement(Yj, {
		props: t,
		data: e,
		animationElapsedTime: n,
		isAnimating: d || n < 1,
		isEntrance: r
	}))), /*#__PURE__*/ C.createElement(FD, { label: t.label }), t.children);
}
function Qj(e) {
	var t = (0, C.useRef)(null);
	return /*#__PURE__*/ C.createElement(Zj, {
		previousRectanglesRef: t,
		props: e
	});
}
var $j = 0, eM = (e, t) => {
	var n = Array.isArray(e.value) ? e.value[1] : e.value;
	return {
		x: e.x,
		y: e.y,
		value: n,
		errorVal: W(e, t)
	};
}, tM = class extends C.PureComponent {
	render() {
		var e = this.props, t = e.hide, n = e.data, r = e.dataKey, i = e.className, a = e.xAxisId, o = e.yAxisId, s = e.needClip, c = e.background, l = e.id;
		if (t || n == null) return null;
		var u = he("recharts-bar", i), d = l;
		return /*#__PURE__*/ C.createElement(Ne, {
			className: u,
			id: l
		}, s && /*#__PURE__*/ C.createElement("defs", null, /*#__PURE__*/ C.createElement(YA, {
			clipPathId: d,
			xAxisId: a,
			yAxisId: o
		})), /*#__PURE__*/ C.createElement(Ne, {
			className: "recharts-bar-rectangles",
			clipPath: s ? `url(#clipPath-${d})` : void 0
		}, /*#__PURE__*/ C.createElement(Gj, {
			data: n,
			dataKey: r,
			background: c,
			allOtherBarProps: this.props
		}), /*#__PURE__*/ C.createElement(Qj, this.props)));
	}
}, nM = {
	activeBar: !1,
	animationBegin: 0,
	animationDuration: 400,
	animationEasing: "ease",
	animationInterpolateFn: Xj,
	animationMatchBy: gO,
	background: !1,
	hide: !1,
	isAnimationActive: "auto",
	label: !1,
	legendType: "rect",
	minPointSize: $j,
	shape: rj,
	xAxisId: 0,
	yAxisId: 0,
	zIndex: Sp.bar
};
function rM(e) {
	var t = e.xAxisId, n = e.yAxisId, r = e.hide, i = e.legendType, a = e.minPointSize, o = e.activeBar, s = e.animationBegin, c = e.animationDuration, l = e.animationEasing, u = e.isAnimationActive, d = JA(t, n).needClip, f = Jc(), p = cc(), m = KD(e.children, jT), h = L((t) => hj(t, e.id, p, m));
	if (f !== "vertical" && f !== "horizontal") return null;
	var g, _ = h == null ? void 0 : h[0];
	return g = _ == null || _.height == null || _.width == null ? 0 : f === "vertical" ? _.height / 2 : _.width / 2, /*#__PURE__*/ C.createElement(qA, {
		xAxisId: t,
		yAxisId: n,
		data: h,
		dataPointFormatter: eM,
		errorBarOffset: g
	}, /*#__PURE__*/ C.createElement(tM, Fj({}, e, {
		layout: f,
		needClip: d,
		data: h,
		xAxisId: t,
		yAxisId: n,
		hide: r,
		legendType: i,
		minPointSize: a,
		activeBar: o,
		animationBegin: s,
		animationDuration: c,
		animationEasing: l,
		isAnimationActive: u
	})));
}
function iM(e) {
	var t = e.layout, n = e.barSettings, r = n.dataKey, i = n.minPointSize, a = n.hasCustomShape, o = e.pos, s = e.bandSize, c = e.xAxis, l = e.yAxis, u = e.xAxisTicks, d = e.yAxisTicks, f = e.stackedData, p = e.displayedData, m = e.offset, h = e.cells, g = e.parentViewBox, _ = e.dataStartIndex, v = t === "horizontal" ? l : c, y = f ? v.scale.domain() : null, b = As({ numericAxis: v }), x = v.scale.map(b);
	return p.map((e, n) => {
		var p, v, S, C, w, T;
		if (f) {
			var E = f[n + _];
			if (E == null) return null;
			p = Ts(E, y);
		} else p = W(e, r), Array.isArray(p) || (p = [b, p]);
		var D = aj(i, $j)(p[1], n);
		if (t === "horizontal") {
			var O, k = l.scale.map(p[0]), A = l.scale.map(p[1]);
			if (k == null || A == null) return null;
			v = ks({
				axis: c,
				ticks: u,
				bandSize: s,
				offset: o.offset,
				entry: e,
				index: n
			}), S = (O = A == null ? k : A) == null ? void 0 : O, C = o.size;
			var j = k - A;
			if (w = Kt(j) ? 0 : j, T = {
				x: v,
				y: m.top,
				width: C,
				height: m.height
			}, Math.abs(D) > 0 && Math.abs(w) < Math.abs(D)) {
				var M = Gt(w || D) * (Math.abs(D) - Math.abs(w));
				S -= M, w += M;
			}
		} else {
			var N = c.scale.map(p[0]), P = c.scale.map(p[1]);
			if (N == null || P == null) return null;
			if (v = N, S = ks({
				axis: l,
				ticks: d,
				bandSize: s,
				offset: o.offset,
				entry: e,
				index: n
			}), C = P - N, w = o.size, T = {
				x: m.left,
				y: S,
				width: m.width,
				height: w
			}, Math.abs(D) > 0 && Math.abs(C) < Math.abs(D)) {
				var ee = Gt(C || D) * (Math.abs(D) - Math.abs(C));
				C += ee;
			}
		}
		return v == null || S == null || C == null || w == null || !a && (C === 0 || w === 0) ? null : Lj(Lj({}, e), {}, {
			stackedBarStart: x,
			x: v,
			y: S,
			width: C,
			height: w,
			value: f ? p : p[1],
			payload: e,
			background: T,
			tooltipPosition: {
				x: v + C / 2,
				y: S + w / 2
			},
			parentViewBox: g,
			originalDataIndex: n
		}, h && h[n] && h[n].props);
	}).filter(Boolean);
}
function aM(e) {
	var t = mn(e, nM), n = xj(t.stackId), r = cc();
	return /*#__PURE__*/ C.createElement(HO, {
		id: t.id,
		type: "bar"
	}, (e) => /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(cO, { legendPayload: Uj(t) }), /*#__PURE__*/ C.createElement(Wj, {
		dataKey: t.dataKey,
		stroke: t.stroke,
		strokeWidth: t.strokeWidth,
		fill: t.fill,
		name: t.name,
		hide: t.hide,
		unit: t.unit,
		formatter: t.formatter,
		tooltipType: t.tooltipType,
		id: e
	}), /*#__PURE__*/ C.createElement(YO, {
		type: "bar",
		id: e,
		data: void 0,
		xAxisId: t.xAxisId,
		yAxisId: t.yAxisId,
		zAxisId: 0,
		dataKey: t.dataKey,
		stackId: n,
		hide: t.hide,
		barSize: t.barSize,
		minPointSize: t.minPointSize,
		maxBarSize: t.maxBarSize,
		isPanorama: r,
		hasCustomShape: t.shape != null && t.shape !== rj
	}), /*#__PURE__*/ C.createElement(jw, { zIndex: t.zIndex }, /*#__PURE__*/ C.createElement(rM, Fj({}, t, { id: e })))));
}
var oM = /*#__PURE__*/ C.memo(aM, Cl);
oM.displayName = "Bar";
//#endregion
//#region node_modules/recharts/es6/util/axisPropsAreEqual.js
var sM = ["domain", "range"], cM = ["domain", "range"];
function lM(e, t) {
	if (e == null) return {};
	var n, r, i = uM(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function uM(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function dM(e, t) {
	return e === t ? !0 : Array.isArray(e) && e.length === 2 && Array.isArray(t) && t.length === 2 ? e[0] === t[0] && e[1] === t[1] : !1;
}
function fM(e, t) {
	if (e === t) return !0;
	var n = e.domain, r = e.range, i = lM(e, sM), a = t.domain, o = t.range, s = lM(t, cM);
	return !dM(n, a) || !dM(r, o) ? !1 : Cl(i, s);
}
//#endregion
//#region node_modules/recharts/es6/cartesian/XAxis.js
var pM = ["type"], mM = [
	"dangerouslySetInnerHTML",
	"ticks",
	"scale"
], hM = ["id", "scale"];
function gM() {
	return gM = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, gM.apply(null, arguments);
}
function _M(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function vM(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? _M(Object(n), !0).forEach(function(t) {
			yM(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : _M(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function yM(e, t, n) {
	return (t = bM(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function bM(e) {
	var t = xM(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function xM(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function SM(e, t) {
	if (e == null) return {};
	var n, r, i = CM(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function CM(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function wM(e) {
	var t = kr(), n = (0, C.useRef)(null), r = Yc(), i = e.type, a = SM(e, pM), o = Ep(r, "xAxis", i), s = (0, C.useMemo)(() => {
		if (o != null) return vM(vM({}, a), {}, { type: o });
	}, [a, o]);
	return (0, C.useLayoutEffect)(() => {
		s != null && (n.current === null ? t(rk(s)) : n.current !== s && t(ik({
			prev: n.current,
			next: s
		})), n.current = s);
	}, [s, t]), (0, C.useLayoutEffect)(() => () => {
		n.current && (t(ak(n.current)), n.current = null);
	}, [t]), null;
}
var TM = (e) => {
	var t = e.xAxisId, n = e.className, r = L(oc), i = cc(), a = "xAxis", o = L((e) => nS(e, a, t, i)), s = L((e) => Gx(e, t)), c = L((e) => Xx(e, t)), l = L((e) => nb(e, t));
	if (s == null || c == null || l == null) return null;
	e.dangerouslySetInnerHTML, e.ticks, e.scale;
	var u = SM(e, mM);
	l.id, l.scale;
	var d = SM(l, hM);
	return /*#__PURE__*/ C.createElement(zA, gM({}, u, d, {
		x: c.x,
		y: c.y,
		width: s.width,
		height: s.height,
		className: he(`recharts-${a} ${a}`, n),
		viewBox: r,
		ticks: o,
		axisType: a,
		axisId: t
	}));
}, EM = {
	allowDataOverflow: tb.allowDataOverflow,
	allowDecimals: tb.allowDecimals,
	allowDuplicatedCategory: tb.allowDuplicatedCategory,
	angle: tb.angle,
	axisLine: AA.axisLine,
	height: tb.height,
	hide: !1,
	includeHidden: tb.includeHidden,
	interval: tb.interval,
	label: !1,
	minTickGap: tb.minTickGap,
	mirror: tb.mirror,
	orientation: tb.orientation,
	padding: tb.padding,
	reversed: tb.reversed,
	scale: tb.scale,
	tick: tb.tick,
	tickCount: tb.tickCount,
	tickLine: AA.tickLine,
	tickSize: AA.tickSize,
	type: tb.type,
	niceTicks: tb.niceTicks,
	xAxisId: 0
}, DM = /*#__PURE__*/ C.memo((e) => {
	var t = mn(e, EM);
	return /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(wM, {
		allowDataOverflow: t.allowDataOverflow,
		allowDecimals: t.allowDecimals,
		allowDuplicatedCategory: t.allowDuplicatedCategory,
		angle: t.angle,
		dataKey: t.dataKey,
		domain: t.domain,
		height: t.height,
		hide: t.hide,
		id: t.xAxisId,
		includeHidden: t.includeHidden,
		interval: t.interval,
		minTickGap: t.minTickGap,
		mirror: t.mirror,
		name: t.name,
		orientation: t.orientation,
		padding: t.padding,
		reversed: t.reversed,
		scale: t.scale,
		tick: t.tick,
		tickCount: t.tickCount,
		tickFormatter: t.tickFormatter,
		ticks: t.ticks,
		type: t.type,
		unit: t.unit,
		niceTicks: t.niceTicks
	}), /*#__PURE__*/ C.createElement(TM, t));
}, fM);
DM.displayName = "XAxis";
//#endregion
//#region node_modules/recharts/es6/cartesian/YAxis.js
var OM = ["type"], kM = [
	"dangerouslySetInnerHTML",
	"ticks",
	"scale"
], AM = ["id", "scale"];
function jM() {
	return jM = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, jM.apply(null, arguments);
}
function MM(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function NM(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? MM(Object(n), !0).forEach(function(t) {
			PM(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : MM(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function PM(e, t, n) {
	return (t = FM(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function FM(e) {
	var t = IM(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function IM(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function LM(e, t) {
	if (e == null) return {};
	var n, r, i = RM(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function RM(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function zM(e) {
	var t = kr(), n = (0, C.useRef)(null), r = Yc(), i = e.type, a = LM(e, OM), o = Ep(r, "yAxis", i), s = (0, C.useMemo)(() => {
		if (o != null) return NM(NM({}, a), {}, { type: o });
	}, [o, a]);
	return (0, C.useLayoutEffect)(() => {
		s != null && (n.current === null ? t(ok(s)) : n.current !== s && t(sk({
			prev: n.current,
			next: s
		})), n.current = s);
	}, [s, t]), (0, C.useLayoutEffect)(() => () => {
		n.current && (t(ck(n.current)), n.current = null);
	}, [t]), null;
}
function BM(e) {
	var t = e.yAxisId, n = e.className, r = e.width, i = e.label, a = (0, C.useRef)(null), o = (0, C.useRef)(null), s = L(oc), c = cc(), l = kr(), u = "yAxis", d = L((e) => Qx(e, t)), f = L((e) => Zx(e, t)), p = L((e) => nS(e, u, t, c)), m = L((e) => ab(e, t));
	if ((0, C.useLayoutEffect)(() => {
		if (!(r !== "auto" || !d || pD(i) || /*#__PURE__*/ (0, C.isValidElement)(i) || m == null)) {
			var e = a.current;
			if (e) {
				var n = e.getCalculatedWidth();
				Math.round(d.width) !== Math.round(n) && l(lk({
					id: t,
					width: n
				}));
			}
		}
	}, [
		p,
		d,
		l,
		i,
		t,
		r,
		m
	]), d == null || f == null || m == null) return null;
	e.dangerouslySetInnerHTML, e.ticks, e.scale;
	var h = LM(e, kM);
	m.id, m.scale;
	var g = LM(m, AM);
	return /*#__PURE__*/ C.createElement(zA, jM({}, h, g, {
		ref: a,
		labelRef: o,
		x: f.x,
		y: f.y,
		tickTextProps: r === "auto" ? { width: void 0 } : { width: r },
		width: d.width,
		height: d.height,
		className: he(`recharts-${u} ${u}`, n),
		viewBox: s,
		ticks: p,
		axisType: u,
		axisId: t
	}));
}
var VM = {
	allowDataOverflow: ib.allowDataOverflow,
	allowDecimals: ib.allowDecimals,
	allowDuplicatedCategory: ib.allowDuplicatedCategory,
	angle: ib.angle,
	axisLine: AA.axisLine,
	hide: !1,
	includeHidden: ib.includeHidden,
	interval: ib.interval,
	label: !1,
	minTickGap: ib.minTickGap,
	mirror: ib.mirror,
	orientation: ib.orientation,
	padding: ib.padding,
	reversed: ib.reversed,
	scale: ib.scale,
	tick: ib.tick,
	tickCount: ib.tickCount,
	tickLine: AA.tickLine,
	tickSize: AA.tickSize,
	type: ib.type,
	niceTicks: ib.niceTicks,
	width: ib.width,
	yAxisId: 0
}, HM = /*#__PURE__*/ C.memo((e) => {
	var t = mn(e, VM);
	return /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(zM, {
		interval: t.interval,
		id: t.yAxisId,
		scale: t.scale,
		type: t.type,
		domain: t.domain,
		allowDataOverflow: t.allowDataOverflow,
		dataKey: t.dataKey,
		allowDuplicatedCategory: t.allowDuplicatedCategory,
		allowDecimals: t.allowDecimals,
		tickCount: t.tickCount,
		padding: t.padding,
		includeHidden: t.includeHidden,
		reversed: t.reversed,
		ticks: t.ticks,
		width: t.width,
		orientation: t.orientation,
		mirror: t.mirror,
		hide: t.hide,
		unit: t.unit,
		name: t.name,
		angle: t.angle,
		minTickGap: t.minTickGap,
		tick: t.tick,
		tickFormatter: t.tickFormatter,
		niceTicks: t.niceTicks
	}), /*#__PURE__*/ C.createElement(BM, t));
}, fM);
HM.displayName = "YAxis";
var UM = R([
	(e, t) => t,
	q,
	Hp,
	Zp,
	bC,
	SC,
	ew,
	ic
], fw);
//#endregion
//#region node_modules/recharts/es6/util/getRelativeCoordinate.js
function WM(e) {
	return "getBBox" in e.currentTarget && typeof e.currentTarget.getBBox == "function";
}
function GM(e) {
	var t = e.currentTarget.getBoundingClientRect(), n, r;
	if (WM(e)) {
		var i = e.currentTarget.getBBox();
		n = i.width > 0 ? t.width / i.width : 1, r = i.height > 0 ? t.height / i.height : 1;
	} else {
		var a = e.currentTarget;
		n = a.offsetWidth > 0 ? t.width / a.offsetWidth : 1, r = a.offsetHeight > 0 ? t.height / a.offsetHeight : 1;
	}
	var o = (e, i) => ({
		relativeX: Math.round((e - t.left) / n),
		relativeY: Math.round((i - t.top) / r)
	});
	return "touches" in e ? Array.from(e.touches).map((e) => o(e.clientX, e.clientY)) : o(e.clientX, e.clientY);
}
//#endregion
//#region node_modules/recharts/es6/state/mouseEventsMiddleware.js
var KM = Qa("mouseClick"), qM = ss();
qM.startListening({
	actionCreator: KM,
	effect: (e, t) => {
		var n = e.payload, r = UM(t.getState(), GM(n));
		(r == null ? void 0 : r.activeIndex) != null && t.dispatch(TS({
			activeIndex: r.activeIndex,
			activeDataKey: void 0,
			activeCoordinate: r.activeCoordinate
		}));
	}
});
var JM = Qa("mouseMove"), YM = ss(), XM = null, ZM = null, QM = null;
YM.startListening({
	actionCreator: JM,
	effect: (e, t) => {
		var n = e.payload, r = t.getState().eventSettings, i = r.throttleDelay, a = r.throttledEvents, o = a === "all" || (a == null ? void 0 : a.includes("mousemove"));
		XM !== null && (cancelAnimationFrame(XM), XM = null), ZM !== null && (typeof i != "number" || !o) && (clearTimeout(ZM), ZM = null), QM = GM(n);
		var s = () => {
			var e = t.getState(), n = lS(e, e.tooltip.settings.shared);
			if (!QM) {
				XM = null, ZM = null;
				return;
			}
			if (n === "axis") {
				var r = UM(e, QM);
				(r == null ? void 0 : r.activeIndex) == null ? t.dispatch(SS()) : t.dispatch(wS({
					activeIndex: r.activeIndex,
					activeDataKey: void 0,
					activeCoordinate: r.activeCoordinate
				}));
			}
			XM = null, ZM = null;
		};
		if (!o) {
			s();
			return;
		}
		i === "raf" ? XM = requestAnimationFrame(s) : typeof i == "number" && ZM === null && (ZM = setTimeout(s, i));
	}
});
//#endregion
//#region node_modules/recharts/es6/state/reduxDevtoolsJsonStringifyReplacer.js
function $M(e, t) {
	return t instanceof HTMLElement ? `HTMLElement <${t.tagName} class="${t.className}">` : t === window ? "global.window" : e === "children" && typeof t == "object" && t ? "<<CHILDREN>>" : t;
}
//#endregion
//#region node_modules/recharts/es6/state/rootPropsSlice.js
var eN = {
	accessibilityLayer: !0,
	barCategoryGap: "10%",
	barGap: 4,
	barSize: void 0,
	className: void 0,
	maxBarSize: void 0,
	stackOffset: "none",
	syncId: void 0,
	syncMethod: "index",
	baseValue: void 0,
	reverseStackOrder: !1
}, tN = xo({
	name: "rootProps",
	initialState: eN,
	reducers: { updateOptions: (e, t) => {
		var n;
		e.accessibilityLayer = t.payload.accessibilityLayer, e.barCategoryGap = t.payload.barCategoryGap, e.barGap = (n = t.payload.barGap) == null ? eN.barGap : n, e.barSize = t.payload.barSize, e.maxBarSize = t.payload.maxBarSize, e.stackOffset = t.payload.stackOffset, e.syncId = t.payload.syncId, e.syncMethod = t.payload.syncMethod, e.className = t.payload.className, e.baseValue = t.payload.baseValue, e.reverseStackOrder = t.payload.reverseStackOrder;
	} }
}), nN = tN.reducer, rN = tN.actions.updateOptions, iN = xo({
	name: "polarOptions",
	initialState: null,
	reducers: { updatePolarOptions: (e, t) => e === null ? t.payload : (e.startAngle = t.payload.startAngle, e.endAngle = t.payload.endAngle, e.cx = t.payload.cx, e.cy = t.payload.cy, e.innerRadius = t.payload.innerRadius, e.outerRadius = t.payload.outerRadius, e) }
});
iN.actions.updatePolarOptions;
var aN = iN.reducer, oN = Qa("keyDown"), sN = Qa("focus"), cN = Qa("blur"), lN = ss(), uN = null, dN = null, fN = null;
lN.startListening({
	actionCreator: oN,
	effect: (e, t) => {
		fN = e.payload, uN !== null && (cancelAnimationFrame(uN), uN = null);
		var n = t.getState().eventSettings, r = n.throttleDelay, i = n.throttledEvents, a = i === "all" || i.includes("keydown");
		dN !== null && (typeof r != "number" || !a) && (clearTimeout(dN), dN = null);
		var o = () => {
			try {
				var e = t.getState();
				if (e.rootProps.accessibilityLayer === !1) return;
				var n = e.tooltip.keyboardInteraction, r = fN;
				if (r !== "ArrowRight" && r !== "ArrowLeft" && r !== "Enter") return;
				var i = BS(n, cC(e), Lb(e), _C(e)), a = i == null ? -1 : Number(i), o = !Number.isFinite(a) || a < 0, s = SC(e), c = cC(e), l = lS(e, e.tooltip.settings.shared);
				if (r === "Enter") {
					if (o) return;
					var u = aw(e, l, "hover", String(n.index));
					t.dispatch(DS({
						active: !n.active,
						activeIndex: n.index,
						activeCoordinate: u
					}));
					return;
				}
				var d = aS(e) === "left-to-right" ? 1 : -1, f = r === "ArrowRight" ? 1 : -1, p;
				if (o) {
					var m = Lb(e), h = _C(e), g = f * d, _ = (e) => ({
						active: !1,
						index: String(e),
						dataKey: void 0,
						graphicalItemId: void 0,
						coordinate: void 0
					});
					if (p = -1, g > 0) {
						for (var v = 0; v < c.length; v++) if (BS(_(v), c, m, h) != null) {
							p = v;
							break;
						}
					} else for (var y = c.length - 1; y >= 0; y--) if (BS(_(y), c, m, h) != null) {
						p = y;
						break;
					}
					if (p < 0) return;
				} else {
					p = a + f * d;
					var b = (s == null ? void 0 : s.length) || c.length;
					if (b === 0 || p >= b || p < 0) return;
				}
				var x = aw(e, l, "hover", String(p));
				t.dispatch(DS({
					active: !0,
					activeIndex: p.toString(),
					activeCoordinate: x
				}));
			} finally {
				uN = null, dN = null;
			}
		};
		if (!a) {
			o();
			return;
		}
		r === "raf" ? uN = requestAnimationFrame(o) : typeof r == "number" && dN === null && (o(), fN = null, dN = setTimeout(() => {
			fN ? o() : (dN = null, uN = null);
		}, r));
	}
}), lN.startListening({
	actionCreator: sN,
	effect: (e, t) => {
		var n = t.getState();
		if (n.rootProps.accessibilityLayer !== !1) {
			var r = n.tooltip.keyboardInteraction;
			if (!r.active && r.index == null) {
				var i = "0", a = aw(n, lS(n, n.tooltip.settings.shared), "hover", String(i));
				t.dispatch(DS({
					active: !0,
					activeIndex: i,
					activeCoordinate: a
				}));
			}
		}
	}
}), lN.startListening({
	actionCreator: cN,
	effect: (e, t) => {
		var n = t.getState();
		if (n.rootProps.accessibilityLayer !== !1) {
			var r = n.tooltip.keyboardInteraction;
			r.active && t.dispatch(DS({
				active: !1,
				activeIndex: r.index,
				activeCoordinate: r.coordinate
			}));
		}
	}
});
//#endregion
//#region node_modules/recharts/es6/util/createEventProxy.js
function pN(e) {
	e.persist();
	var t = e.currentTarget;
	return new Proxy(e, { get: (e, n) => {
		if (n === "currentTarget") return t;
		var r = Reflect.get(e, n);
		return typeof r == "function" ? r.bind(e) : r;
	} });
}
//#endregion
//#region node_modules/recharts/es6/state/externalEventsMiddleware.js
var mN = Qa("externalEvent"), hN = ss(), gN = /* @__PURE__ */ new Map(), _N = /* @__PURE__ */ new Map(), vN = /* @__PURE__ */ new Map();
hN.startListening({
	actionCreator: mN,
	effect: (e, t) => {
		var n = e.payload, r = n.handler, i = n.reactEvent;
		if (r != null) {
			var a = i.type, o = pN(i);
			vN.set(a, {
				handler: r,
				reactEvent: o
			});
			var s = gN.get(a);
			s !== void 0 && (cancelAnimationFrame(s), gN.delete(a));
			var c = t.getState().eventSettings, l = c.throttleDelay, u = c.throttledEvents, d = u === "all" || (u == null ? void 0 : u.includes(a)), f = _N.get(a);
			f !== void 0 && (typeof l != "number" || !d) && (clearTimeout(f), _N.delete(a));
			var p = () => {
				var e = vN.get(a);
				try {
					if (!e) return;
					var n = e.handler, r = e.reactEvent, i = t.getState(), o = {
						activeCoordinate: MC(i),
						activeDataKey: kC(i),
						activeIndex: DC(i),
						activeLabel: OC(i),
						activeTooltipIndex: DC(i),
						isTooltipActive: NC(i)
					};
					n && n(o, r);
				} finally {
					gN.delete(a), _N.delete(a), vN.delete(a);
				}
			};
			if (!d) {
				p();
				return;
			}
			if (l === "raf") {
				var m = requestAnimationFrame(p);
				gN.set(a, m);
			} else if (typeof l == "number") {
				if (!_N.has(a)) {
					p();
					var h = setTimeout(p, l);
					_N.set(a, h);
				}
			} else p();
		}
	}
});
var yN = R([
	R([WS], (e) => e.tooltipItemPayloads),
	(e, t) => t,
	(e, t, n) => n
], (e, t, n) => {
	if (t != null) {
		var r = e.find((e) => e.settings.graphicalItemId === n);
		if (r != null) {
			var i = r.getPosition;
			if (i != null) return i(t);
		}
	}
}), bN = Qa("touchMove"), xN = ss(), SN = null, CN = null, wN = null, TN = null;
xN.startListening({
	actionCreator: bN,
	effect: (e, t) => {
		var n = e.payload;
		if (!(n.touches == null || n.touches.length === 0)) {
			TN = pN(n);
			var r = t.getState().eventSettings, i = r.throttleDelay, a = r.throttledEvents, o = a === "all" || a.includes("touchmove");
			SN !== null && (cancelAnimationFrame(SN), SN = null), CN !== null && (typeof i != "number" || !o) && (clearTimeout(CN), CN = null), wN = Array.from(n.touches).map((e) => GM({
				clientX: e.clientX,
				clientY: e.clientY,
				currentTarget: n.currentTarget
			}));
			var s = () => {
				if (TN != null) {
					var e = t.getState(), n = lS(e, e.tooltip.settings.shared);
					if (n === "axis") {
						var r, i = (r = wN) == null ? void 0 : r[0];
						if (i == null) {
							SN = null, CN = null;
							return;
						}
						var a = UM(e, i);
						(a == null ? void 0 : a.activeIndex) != null && t.dispatch(wS({
							activeIndex: a.activeIndex,
							activeDataKey: void 0,
							activeCoordinate: a.activeCoordinate
						}));
					} else if (n === "item") {
						var o, s = TN.touches[0];
						if (document.elementFromPoint == null || s == null) return;
						var c = document.elementFromPoint(s.clientX, s.clientY);
						if (!c || !c.getAttribute) return;
						var l = c.getAttribute(qs), u = (o = c.getAttribute("data-recharts-item-id")) == null ? void 0 : o, d = iC(e).find((e) => e.id === u);
						if (l == null || d == null || u == null) return;
						var f = d.dataKey, p = yN(e, l, u);
						t.dispatch(bS({
							activeDataKey: f,
							activeIndex: l,
							activeCoordinate: p,
							activeGraphicalItemId: u
						}));
					}
					SN = null, CN = null;
				}
			};
			if (!o) {
				s();
				return;
			}
			i === "raf" ? SN = requestAnimationFrame(s) : typeof i == "number" && CN === null && (s(), TN = null, CN = setTimeout(() => {
				TN ? s() : (CN = null, SN = null);
			}, i));
		}
	}
});
//#endregion
//#region node_modules/recharts/es6/state/eventSettingsSlice.js
var EN = {
	throttleDelay: "raf",
	throttledEvents: [
		"mousemove",
		"touchmove",
		"pointermove",
		"scroll",
		"wheel"
	]
}, DN = xo({
	name: "eventSettings",
	initialState: EN,
	reducers: { setEventSettings: (e, t) => {
		t.payload.throttleDelay != null && (e.throttleDelay = t.payload.throttleDelay), t.payload.throttledEvents != null && (e.throttledEvents = H(t.payload.throttledEvents));
	} }
}), ON = DN.actions.setEventSettings, kN = DN.reducer, AN = Ti({
	brush: Pk,
	cartesianAxis: uk,
	chartData: nT,
	errorBars: HA,
	eventSettings: kN,
	graphicalItems: JO,
	layout: hs,
	legend: il,
	options: Yw,
	polarAxis: RD,
	polarOptions: aN,
	referenceElements: zk,
	renderedTicks: mA,
	rootProps: nN,
	tooltip: OS,
	zIndex: kw
}), jN = function(e) {
	var t = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : "Chart";
	return uo({
		reducer: AN,
		preloadedState: e,
		middleware: (e) => {
			var t;
			return e({
				serializableCheck: !1,
				immutableCheck: ![
					"commonjs",
					"es6",
					"production"
				].includes((t = "es6") == null ? "" : t)
			}).concat([
				qM.middleware,
				YM.middleware,
				lN.middleware,
				hN.middleware,
				xN.middleware
			]);
		},
		enhancers: (e) => {
			var t = e;
			return typeof e == "function" && (t = e()), t.concat(co({ type: "raf" }));
		},
		devTools: Kl.devToolsEnabled && {
			serialize: { replacer: $M },
			name: `recharts-${t}`
		}
	});
};
//#endregion
//#region node_modules/recharts/es6/state/RechartsStoreProvider.js
function MN(e) {
	var t = e.preloadedState, n = e.children, r = e.reduxStoreName, i = cc(), a = (0, C.useRef)(null);
	if (i) return n;
	a.current == null && (a.current = jN(t, r));
	var o = Er;
	return /*#__PURE__*/ C.createElement(bl, {
		context: o,
		store: a.current
	}, n);
}
//#endregion
//#region node_modules/recharts/es6/state/ReportMainChartProps.js
function NN(e) {
	var t = e.layout, n = e.margin, r = kr(), i = cc();
	return (0, C.useEffect)(() => {
		i || (r(fs(t)), r(ds(n)));
	}, [
		r,
		i,
		t,
		n
	]), null;
}
var PN = /*#__PURE__*/ (0, C.memo)(NN, Cl);
//#endregion
//#region node_modules/recharts/es6/state/ReportChartProps.js
function FN(e) {
	var t = kr();
	return (0, C.useEffect)(() => {
		t(rN(e));
	}, [t, e]), null;
}
var IN = /*#__PURE__*/ (0, C.memo)((e) => {
	var t = kr();
	return (0, C.useEffect)(() => {
		t(ON(e));
	}, [t, e]), null;
}, Cl);
//#endregion
//#region node_modules/recharts/es6/zIndex/ZIndexPortal.js
function LN(e) {
	var t = e.zIndex, n = e.isPanorama, r = (0, C.useRef)(null), i = kr();
	return (0, C.useLayoutEffect)(() => (r.current && i(Dw({
		zIndex: t,
		element: r.current,
		isPanorama: n
	})), () => {
		i(Ow({
			zIndex: t,
			isPanorama: n
		}));
	}), [
		i,
		t,
		n
	]), /*#__PURE__*/ C.createElement("g", {
		tabIndex: -1,
		ref: r,
		className: `recharts-zIndex-layer_${t}`
	});
}
function RN(e) {
	var t = e.children, n = e.isPanorama, r = L(mw);
	if (!r || r.length === 0) return t;
	var i = r.filter((e) => e < 0), a = r.filter((e) => e > 0);
	return /*#__PURE__*/ C.createElement(C.Fragment, null, i.map((e) => /*#__PURE__*/ C.createElement(LN, {
		key: e,
		zIndex: e,
		isPanorama: n
	})), t, a.map((e) => /*#__PURE__*/ C.createElement(LN, {
		key: e,
		zIndex: e,
		isPanorama: n
	})));
}
//#endregion
//#region node_modules/recharts/es6/container/RootSurface.js
var zN = ["children"];
function BN(e, t) {
	if (e == null) return {};
	var n, r, i = VN(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function VN(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function HN() {
	return HN = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, HN.apply(null, arguments);
}
var UN = {
	width: "100%",
	height: "100%",
	display: "block"
}, WN = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = qc(), r = K(), i = mu();
	if (!_s(n) || !_s(r)) return null;
	var a = e.children, o = e.otherAttributes, s = e.title, c = e.desc, l, u;
	return o != null && (l = typeof o.tabIndex == "number" ? o.tabIndex : i ? 0 : void 0, u = typeof o.role == "string" ? o.role : i ? "application" : void 0), /*#__PURE__*/ C.createElement(Oe, HN({}, o, {
		title: s,
		desc: c,
		role: u,
		tabIndex: l,
		width: n,
		height: r,
		style: UN,
		ref: t
	}), a);
}), GN = (e) => {
	var t = e.children, n = L(uc);
	if (!n) return null;
	var r = n.width, i = n.height, a = n.y, o = n.x;
	return /*#__PURE__*/ C.createElement(Oe, {
		width: r,
		height: i,
		x: o,
		y: a
	}, t);
}, KN = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.children, r = BN(e, zN);
	return cc() ? /*#__PURE__*/ C.createElement(GN, null, /*#__PURE__*/ C.createElement(RN, { isPanorama: !0 }, n)) : /*#__PURE__*/ C.createElement(WN, HN({ ref: t }, r), /*#__PURE__*/ C.createElement(RN, { isPanorama: !1 }, n));
});
//#endregion
//#region node_modules/recharts/es6/util/useReportScale.js
function qN(e, t) {
	return QN(e) || ZN(e, t) || YN(e, t) || JN();
}
function JN() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function YN(e, t) {
	if (e) {
		if (typeof e == "string") return XN(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? XN(e, t) : void 0;
	}
}
function XN(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function ZN(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function QN(e) {
	if (Array.isArray(e)) return e;
}
function $N() {
	var e = kr(), t = qN((0, C.useState)(null), 2), n = t[0], r = t[1], i = L(Us);
	return (0, C.useEffect)(() => {
		if (n != null) {
			var t = n.getBoundingClientRect().width / n.offsetWidth;
			U(t) && t !== i && e(ms(t));
		}
	}, [
		n,
		e,
		i
	]), r;
}
//#endregion
//#region node_modules/recharts/es6/chart/RechartsWrapper.js
function eP(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function tP(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? eP(Object(n), !0).forEach(function(t) {
			nP(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : eP(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function nP(e, t, n) {
	return (t = rP(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function rP(e) {
	var t = iP(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function iP(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function aP() {
	return aP = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, aP.apply(null, arguments);
}
function oP(e, t) {
	return dP(e) || uP(e, t) || cP(e, t) || sP();
}
function sP() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function cP(e, t) {
	if (e) {
		if (typeof e == "string") return lP(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? lP(e, t) : void 0;
	}
}
function lP(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function uP(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function dP(e) {
	if (Array.isArray(e)) return e;
}
var fP = () => (pT(), null);
function pP(e) {
	if (typeof e == "number") return e;
	if (typeof e == "string") {
		var t = parseFloat(e);
		if (!Number.isNaN(t)) return t;
	}
	return 0;
}
var mP = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n, r, i = (0, C.useRef)(null), a = oP((0, C.useState)({
		containerWidth: pP((n = e.style) == null ? void 0 : n.width),
		containerHeight: pP((r = e.style) == null ? void 0 : r.height)
	}), 2), o = a[0], s = a[1], c = (0, C.useCallback)((e, t) => {
		s((n) => {
			var r = Math.round(e), i = Math.round(t);
			return n.containerWidth === r && n.containerHeight === i ? n : {
				containerWidth: r,
				containerHeight: i
			};
		});
	}, []), l = (0, C.useCallback)((e) => {
		if (typeof t == "function" && t(e), i.current != null && (i.current.disconnect(), i.current = null), e != null && typeof ResizeObserver < "u") {
			var n = e.getBoundingClientRect(), r = n.width, a = n.height;
			c(r, a);
			var o = new ResizeObserver((e) => {
				var t = e[0];
				if (t != null) {
					var n = t.contentRect, r = n.width, i = n.height;
					c(r, i);
				}
			});
			o.observe(e), i.current = o;
		}
	}, [t, c]);
	return (0, C.useEffect)(() => () => {
		var e = i.current;
		e != null && e.disconnect();
	}, [c]), /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(Qc, {
		width: o.containerWidth,
		height: o.containerHeight
	}), /*#__PURE__*/ C.createElement("div", aP({ ref: l }, e)));
}), hP = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.width, r = e.height, i = oP((0, C.useState)({
		containerWidth: pP(n),
		containerHeight: pP(r)
	}), 2), a = i[0], o = i[1], s = (0, C.useCallback)((e, t) => {
		o((n) => {
			var r = Math.round(e), i = Math.round(t);
			return n.containerWidth === r && n.containerHeight === i ? n : {
				containerWidth: r,
				containerHeight: i
			};
		});
	}, []), c = (0, C.useCallback)((e) => {
		if (typeof t == "function" && t(e), e != null) {
			var n = e.getBoundingClientRect(), r = n.width, i = n.height;
			s(r, i);
		}
	}, [t, s]);
	return /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(Qc, {
		width: a.containerWidth,
		height: a.containerHeight
	}), /*#__PURE__*/ C.createElement("div", aP({ ref: c }, e)));
}), gP = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.width, r = e.height;
	return /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(Qc, {
		width: n,
		height: r
	}), /*#__PURE__*/ C.createElement("div", aP({ ref: t }, e)));
}), _P = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.width, r = e.height;
	return typeof n == "string" || typeof r == "string" ? /*#__PURE__*/ C.createElement(hP, aP({}, e, { ref: t })) : typeof n == "number" && typeof r == "number" ? /*#__PURE__*/ C.createElement(gP, aP({}, e, {
		width: n,
		height: r,
		ref: t
	})) : /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(Qc, {
		width: n,
		height: r
	}), /*#__PURE__*/ C.createElement("div", aP({ ref: t }, e)));
});
function vP(e) {
	return e ? mP : _P;
}
var yP = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.children, r = e.className, i = e.height, a = e.onClick, o = e.onContextMenu, s = e.onDoubleClick, c = e.onMouseDown, l = e.onMouseEnter, u = e.onMouseLeave, d = e.onMouseMove, f = e.onMouseUp, p = e.onTouchEnd, m = e.onTouchMove, h = e.onTouchStart, g = e.style, _ = e.width, v = e.responsive, y = e.dispatchTouchEvents, b = y === void 0 || y, x = (0, C.useRef)(null), S = kr(), w = oP((0, C.useState)(null), 2), T = w[0], E = w[1], D = oP((0, C.useState)(null), 2), O = D[0], k = D[1], A = $N(), j = Bc(), M = (j == null ? void 0 : j.width) > 0 ? j.width : _, N = (j == null ? void 0 : j.height) > 0 ? j.height : i, P = (0, C.useCallback)((e) => {
		A(e), typeof t == "function" && t(e), E(e), k(e), e != null && (x.current = e);
	}, [
		A,
		t,
		E,
		k
	]), ee = (0, C.useCallback)((e) => {
		S(KM(e)), S(mN({
			handler: a,
			reactEvent: e
		}));
	}, [S, a]), te = (0, C.useCallback)((e) => {
		S(JM(e)), S(mN({
			handler: l,
			reactEvent: e
		}));
	}, [S, l]), ne = (0, C.useCallback)((e) => {
		S(SS()), S(mN({
			handler: u,
			reactEvent: e
		}));
	}, [S, u]), re = (0, C.useCallback)((e) => {
		S(JM(e)), S(mN({
			handler: d,
			reactEvent: e
		}));
	}, [S, d]), ie = (0, C.useCallback)(() => {
		S(sN());
	}, [S]), ae = (0, C.useCallback)(() => {
		S(cN());
	}, [S]), oe = (0, C.useCallback)((e) => {
		S(oN(e.key));
	}, [S]), se = (0, C.useCallback)((e) => {
		S(mN({
			handler: o,
			reactEvent: e
		}));
	}, [S, o]), ce = (0, C.useCallback)((e) => {
		S(mN({
			handler: s,
			reactEvent: e
		}));
	}, [S, s]), le = (0, C.useCallback)((e) => {
		S(mN({
			handler: c,
			reactEvent: e
		}));
	}, [S, c]), ue = (0, C.useCallback)((e) => {
		S(mN({
			handler: f,
			reactEvent: e
		}));
	}, [S, f]), de = (0, C.useCallback)((e) => {
		S(mN({
			handler: h,
			reactEvent: e
		}));
	}, [S, h]), fe = (0, C.useCallback)((e) => {
		b && S(bN(e)), S(mN({
			handler: m,
			reactEvent: e
		}));
	}, [
		S,
		b,
		m
	]), pe = (0, C.useCallback)((e) => {
		S(mN({
			handler: p,
			reactEvent: e
		}));
	}, [S, p]), me = vP(v);
	return /*#__PURE__*/ C.createElement(Vw.Provider, { value: T }, /*#__PURE__*/ C.createElement(Pe.Provider, { value: O }, /*#__PURE__*/ C.createElement(me, {
		width: M == null ? g == null ? void 0 : g.width : M,
		height: N == null ? g == null ? void 0 : g.height : N,
		className: he("recharts-wrapper", r),
		style: tP({
			position: "relative",
			cursor: "default",
			width: M,
			height: N
		}, g),
		onClick: ee,
		onContextMenu: se,
		onDoubleClick: ce,
		onFocus: ie,
		onBlur: ae,
		onKeyDown: oe,
		onMouseDown: le,
		onMouseEnter: te,
		onMouseLeave: ne,
		onMouseMove: re,
		onMouseUp: ue,
		onTouchEnd: pe,
		onTouchMove: fe,
		onTouchStart: de,
		ref: P
	}, /*#__PURE__*/ C.createElement(fP, null), n)));
}), bP = [
	"width",
	"height",
	"responsive",
	"children",
	"className",
	"style",
	"compact",
	"title",
	"desc"
];
function xP(e, t) {
	if (e == null) return {};
	var n, r, i = SP(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function SP(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var CP = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.width, r = e.height, i = e.responsive, a = e.children, o = e.className, s = e.style, c = e.compact, l = e.title, u = e.desc, d = xe(xP(e, bP));
	return c ? /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(Qc, {
		width: n,
		height: r
	}), /*#__PURE__*/ C.createElement(KN, {
		otherAttributes: d,
		title: l,
		desc: u
	}, a)) : /*#__PURE__*/ C.createElement(yP, {
		className: o,
		style: s,
		width: n,
		height: r,
		responsive: i != null && i,
		onClick: e.onClick,
		onMouseLeave: e.onMouseLeave,
		onMouseEnter: e.onMouseEnter,
		onMouseMove: e.onMouseMove,
		onMouseDown: e.onMouseDown,
		onMouseUp: e.onMouseUp,
		onContextMenu: e.onContextMenu,
		onDoubleClick: e.onDoubleClick,
		onTouchStart: e.onTouchStart,
		onTouchMove: e.onTouchMove,
		onTouchEnd: e.onTouchEnd
	}, /*#__PURE__*/ C.createElement(KN, {
		otherAttributes: d,
		title: l,
		desc: u,
		ref: t
	}, /*#__PURE__*/ C.createElement(qk, null, a)));
});
//#endregion
//#region node_modules/recharts/es6/chart/CartesianChart.js
function wP() {
	return wP = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, wP.apply(null, arguments);
}
function TP(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function EP(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? TP(Object(n), !0).forEach(function(t) {
			DP(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : TP(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function DP(e, t, n) {
	return (t = OP(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function OP(e) {
	var t = kP(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function kP(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var AP = EP({
	accessibilityLayer: !0,
	barCategoryGap: "10%",
	barGap: 4,
	layout: "horizontal",
	margin: {
		top: 5,
		right: 5,
		bottom: 5,
		left: 5
	},
	responsive: !1,
	reverseStackOrder: !1,
	stackOffset: "none",
	syncMethod: "index"
}, EN), jP = /*#__PURE__*/ (0, C.forwardRef)(function(e, t) {
	var n, r = mn(e.categoricalChartProps, AP), i = e.chartName, a = e.defaultTooltipEventType, o = e.validateTooltipEventTypes, s = e.tooltipPayloadSearcher, c = e.categoricalChartProps, l = {
		chartName: i,
		defaultTooltipEventType: a,
		validateTooltipEventTypes: o,
		tooltipPayloadSearcher: s,
		eventEmitter: void 0
	};
	return /*#__PURE__*/ C.createElement(MN, {
		preloadedState: { options: l },
		reduxStoreName: (n = c.id) == null ? i : n
	}, /*#__PURE__*/ C.createElement(jk, { chartData: c.data }), /*#__PURE__*/ C.createElement(PN, {
		layout: r.layout,
		margin: r.margin
	}), /*#__PURE__*/ C.createElement(IN, {
		throttleDelay: r.throttleDelay,
		throttledEvents: r.throttledEvents
	}), /*#__PURE__*/ C.createElement(FN, {
		baseValue: r.baseValue,
		accessibilityLayer: r.accessibilityLayer,
		barCategoryGap: r.barCategoryGap,
		maxBarSize: r.maxBarSize,
		stackOffset: r.stackOffset,
		barGap: r.barGap,
		barSize: r.barSize,
		syncId: r.syncId,
		syncMethod: r.syncMethod,
		className: r.className,
		reverseStackOrder: r.reverseStackOrder
	}), /*#__PURE__*/ C.createElement(CP, wP({}, r, { ref: t })));
}), MP = ["axis", "item"], NP = /*#__PURE__*/ (0, C.forwardRef)((e, t) => /*#__PURE__*/ C.createElement(jP, {
	chartName: "BarChart",
	defaultTooltipEventType: "axis",
	validateTooltipEventTypes: MP,
	tooltipPayloadSearcher: qw,
	categoricalChartProps: e,
	ref: t
})), PP = /* @__PURE__ */ o(((e) => {
	var t = d(), n = Symbol.for("react.element"), r = Object.prototype.hasOwnProperty, i = t.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED.ReactCurrentOwner, a = {
		key: !0,
		ref: !0,
		__self: !0,
		__source: !0
	};
	function o(e, t, o) {
		var s, c = {}, l = null, u = null;
		for (s in o !== void 0 && (l = "" + o), t.key !== void 0 && (l = "" + t.key), t.ref !== void 0 && (u = t.ref), t) r.call(t, s) && !a.hasOwnProperty(s) && (c[s] = t[s]);
		if (e && e.defaultProps) for (s in t = e.defaultProps, t) c[s] === void 0 && (c[s] = t[s]);
		return {
			$$typeof: n,
			type: e,
			key: l,
			ref: u,
			props: c,
			_owner: i.current
		};
	}
	e.jsx = o, e.jsxs = o;
})), FP = /* @__PURE__ */ o(((e, t) => {
	t.exports = PP();
})), IP = g(), X = FP(), LP = [
	{
		key: "queueRows",
		label: "Queue Rows",
		icon: ce,
		tone: "blue"
	},
	{
		key: "nextSteps",
		label: "Next Steps",
		icon: re,
		tone: "green"
	},
	{
		key: "undecidedJobReviews",
		label: "Undecided Job Reviews",
		icon: ie,
		tone: "violet"
	},
	{
		key: "undecidedMaybeTailor",
		label: "Undecided Maybe Tailor",
		icon: pe,
		tone: "cyan"
	}
], RP = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
function zP(e) {
	return Number.isFinite(e) ? Math.max(0, Number(e)) : 0;
}
function BP(e) {
	return Number.isFinite(e) ? RP.format(Number(e)) : "—";
}
function VP({ active: e, payload: t }) {
	var n;
	if (!e || !(t != null && t.length)) return null;
	let r = (n = t[0]) == null ? void 0 : n.payload;
	return r ? /* @__PURE__ */ (0, X.jsxs)("div", {
		className: "executive-kpi-tooltip",
		children: [
			/* @__PURE__ */ (0, X.jsx)("span", { children: "Current" }),
			/* @__PURE__ */ (0, X.jsx)("strong", { children: BP(r.current) }),
			Number(r.baseline) > 0 ? /* @__PURE__ */ (0, X.jsxs)("small", { children: ["Queue baseline: ", BP(r.baseline)] }) : null
		]
	}) : null;
}
function HP({ value: e, queueRows: t, label: n }) {
	let r = Math.max(t, e, 1), i = [{
		name: "Current snapshot",
		current: e,
		remaining: Math.max(0, r - e),
		baseline: t
	}];
	return /* @__PURE__ */ (0, X.jsx)("div", {
		className: "executive-kpi-chart",
		role: "img",
		"aria-label": t > 0 ? `${n}: ${BP(e)} against a current queue baseline of ${BP(t)}` : `${n}: ${BP(e)} in the current snapshot`,
		children: /* @__PURE__ */ (0, X.jsx)(Hc, {
			width: "100%",
			height: "100%",
			children: /* @__PURE__ */ (0, X.jsxs)(NP, {
				data: i,
				layout: "vertical",
				margin: {
					top: 6,
					right: 0,
					bottom: 6,
					left: 0
				},
				children: [
					/* @__PURE__ */ (0, X.jsx)(DM, {
						type: "number",
						domain: [0, r],
						hide: !0
					}),
					/* @__PURE__ */ (0, X.jsx)(HM, {
						type: "category",
						dataKey: "name",
						hide: !0
					}),
					/* @__PURE__ */ (0, X.jsx)(AT, {
						allowEscapeViewBox: {
							x: !1,
							y: !0
						},
						content: /* @__PURE__ */ (0, X.jsx)(VP, {}),
						cursor: !1,
						wrapperStyle: {
							zIndex: 30,
							pointerEvents: "none"
						}
					}),
					/* @__PURE__ */ (0, X.jsx)(oM, {
						dataKey: "current",
						stackId: "snapshot",
						fill: "var(--executive-kpi-accent)",
						radius: [
							4,
							0,
							0,
							4
						],
						isAnimationActive: !1
					}),
					/* @__PURE__ */ (0, X.jsx)(oM, {
						dataKey: "remaining",
						stackId: "snapshot",
						fill: "var(--executive-kpi-track)",
						radius: [
							0,
							4,
							4,
							0
						],
						isAnimationActive: !1
					})
				]
			})
		})
	});
}
function UP({ metric: e }) {
	let t = e.icon;
	return /* @__PURE__ */ (0, X.jsxs)("article", {
		className: `executive-kpi-card executive-kpi-card--${e.tone}`,
		"aria-busy": "true",
		children: [
			/* @__PURE__ */ (0, X.jsxs)("div", {
				className: "executive-kpi-card-header",
				children: [/* @__PURE__ */ (0, X.jsx)("span", {
					className: "executive-kpi-label",
					children: e.label
				}), /* @__PURE__ */ (0, X.jsx)("span", {
					className: "executive-kpi-icon",
					"aria-hidden": "true",
					children: /* @__PURE__ */ (0, X.jsx)(t, {
						size: 17,
						strokeWidth: 2
					})
				})]
			}),
			/* @__PURE__ */ (0, X.jsx)("div", { className: "executive-kpi-skeleton executive-kpi-skeleton--value" }),
			/* @__PURE__ */ (0, X.jsx)("div", { className: "executive-kpi-skeleton executive-kpi-skeleton--caption" }),
			/* @__PURE__ */ (0, X.jsx)("div", { className: "executive-kpi-skeleton executive-kpi-skeleton--chart" })
		]
	});
}
function WP({ state: e }) {
	if (e.status === "loading") return /* @__PURE__ */ (0, X.jsx)("div", {
		className: "executive-kpi-dashboard kpi-grid kpi-grid-cols-1 sm:kpi-grid-cols-2 xl:kpi-grid-cols-4 kpi-gap-3",
		"aria-label": "Loading executive queue metrics",
		children: LP.map((e) => /* @__PURE__ */ (0, X.jsx)(UP, { metric: e }, e.key))
	});
	let t = e.status === "error", n = t ? {
		queueRows: null,
		nextSteps: null,
		undecidedJobReviews: null,
		undecidedMaybeTailor: null
	} : e.metrics, r = zP(n.queueRows);
	return /* @__PURE__ */ (0, X.jsx)("div", {
		className: "executive-kpi-dashboard kpi-grid kpi-grid-cols-1 sm:kpi-grid-cols-2 xl:kpi-grid-cols-4 kpi-gap-3",
		"aria-label": "Executive queue metrics",
		children: LP.map((e) => {
			let i = e.icon, a = n[e.key], o = zP(a);
			return /* @__PURE__ */ (0, X.jsxs)("article", {
				className: `executive-kpi-card executive-kpi-card--${e.tone}`,
				children: [
					/* @__PURE__ */ (0, X.jsxs)("div", {
						className: "executive-kpi-card-header",
						children: [/* @__PURE__ */ (0, X.jsx)("span", {
							className: "executive-kpi-label",
							children: e.label
						}), /* @__PURE__ */ (0, X.jsx)("span", {
							className: "executive-kpi-icon",
							"aria-hidden": "true",
							children: /* @__PURE__ */ (0, X.jsx)(i, {
								size: 17,
								strokeWidth: 2
							})
						})]
					}),
					/* @__PURE__ */ (0, X.jsx)("strong", {
						className: "executive-kpi-value",
						children: t ? "Unavailable" : BP(a)
					}),
					/* @__PURE__ */ (0, X.jsx)("span", {
						className: "executive-kpi-caption",
						children: t ? "Status data could not be loaded" : "Current snapshot"
					}),
					t ? /* @__PURE__ */ (0, X.jsx)("div", {
						className: "executive-kpi-error",
						role: "status",
						children: "Refresh Status to try again."
					}) : /* @__PURE__ */ (0, X.jsx)(HP, {
						value: o,
						queueRows: r,
						label: e.label
					})
				]
			}, e.key);
		})
	});
}
//#endregion
//#region node_modules/@tanstack/table-core/build/lib/index.mjs
function GP(e, t) {
	return typeof e == "function" ? e(t) : e;
}
function KP(e, t) {
	return (n) => {
		t.setState((t) => ({
			...t,
			[e]: GP(n, t[e])
		}));
	};
}
function qP(e) {
	return e instanceof Function;
}
function JP(e) {
	return Array.isArray(e) && e.every((e) => typeof e == "number");
}
function YP(e, t) {
	let n = [], r = (e) => {
		e.forEach((e) => {
			n.push(e);
			let i = t(e);
			i != null && i.length && r(i);
		});
	};
	return r(e), n;
}
function Z(e, t, n) {
	let r = [], i;
	return (a) => {
		let o;
		n.key && n.debug && (o = Date.now());
		let s = e(a);
		if (!(s.length !== r.length || s.some((e, t) => r[t] !== e))) return i;
		r = s;
		let c;
		if (n.key && n.debug && (c = Date.now()), i = t(...s), n == null || n.onChange == null || n.onChange(i), n.key && n.debug && n != null && n.debug()) {
			let e = Math.round((Date.now() - o) * 100) / 100, t = Math.round((Date.now() - c) * 100) / 100, r = t / 16, i = (e, t) => {
				for (e = String(e); e.length < t;) e = " " + e;
				return e;
			};
			console.info(`%c⏱ ${i(t, 5)} /${i(e, 5)} ms`, `
            font-size: .6rem;
            font-weight: bold;
            color: hsl(${Math.max(0, Math.min(120 - 120 * r, 120))}deg 100% 31%);`, n == null ? void 0 : n.key);
		}
		return i;
	};
}
function Q(e, t, n, r) {
	return {
		debug: () => {
			var n;
			return (n = e == null ? void 0 : e.debugAll) == null ? e[t] : n;
		},
		key: !1,
		onChange: r
	};
}
function XP(e, t, n, r) {
	let i = {
		id: `${t.id}_${n.id}`,
		row: t,
		column: n,
		getValue: () => t.getValue(r),
		renderValue: () => {
			var t;
			return (t = i.getValue()) == null ? e.options.renderFallbackValue : t;
		},
		getContext: Z(() => [
			e,
			n,
			t,
			i
		], (e, t, n, r) => ({
			table: e,
			column: t,
			row: n,
			cell: r,
			getValue: r.getValue,
			renderValue: r.renderValue
		}), Q(e.options, "debugCells", "cell.getContext"))
	};
	return e._features.forEach((r) => {
		r.createCell == null || r.createCell(i, n, t, e);
	}, {}), i;
}
function ZP(e, t, n, r) {
	var i, a;
	let o = {
		...e._getDefaultColumnDef(),
		...t
	}, s = o.accessorKey, c = (i = (a = o.id) == null ? s ? typeof String.prototype.replaceAll == "function" ? s.replaceAll(".", "_") : s.replace(/\./g, "_") : void 0 : a) == null ? typeof o.header == "string" ? o.header : void 0 : i, l;
	if (o.accessorFn ? l = o.accessorFn : s && (l = s.includes(".") ? (e) => {
		let t = e;
		for (let e of s.split(".")) {
			var n;
			t = (n = t) == null ? void 0 : n[e];
		}
		return t;
	} : (e) => e[o.accessorKey]), !c) throw Error();
	let u = {
		id: `${String(c)}`,
		accessorFn: l,
		parent: r,
		depth: n,
		columnDef: o,
		columns: [],
		getFlatColumns: Z(() => [!0], () => {
			var e;
			return [u, ...(e = u.columns) == null ? void 0 : e.flatMap((e) => e.getFlatColumns())];
		}, Q(e.options, "debugColumns", "column.getFlatColumns")),
		getLeafColumns: Z(() => [e._getOrderColumnsFn()], (e) => {
			var t;
			return (t = u.columns) != null && t.length ? e(u.columns.flatMap((e) => e.getLeafColumns())) : [u];
		}, Q(e.options, "debugColumns", "column.getLeafColumns"))
	};
	for (let t of e._features) t.createColumn == null || t.createColumn(u, e);
	return u;
}
var QP = "debugHeaders";
function $P(e, t, n) {
	var r;
	let i = {
		id: (r = n.id) == null ? t.id : r,
		column: t,
		index: n.index,
		isPlaceholder: !!n.isPlaceholder,
		placeholderId: n.placeholderId,
		depth: n.depth,
		subHeaders: [],
		colSpan: 0,
		rowSpan: 0,
		headerGroup: null,
		getLeafHeaders: () => {
			let e = [], t = (n) => {
				n.subHeaders && n.subHeaders.length && n.subHeaders.map(t), e.push(n);
			};
			return t(i), e;
		},
		getContext: () => ({
			table: e,
			header: i,
			column: t
		})
	};
	return e._features.forEach((t) => {
		t.createHeader == null || t.createHeader(i, e);
	}), i;
}
var eF = { createTable: (e) => {
	e.getHeaderGroups = Z(() => [
		e.getAllColumns(),
		e.getVisibleLeafColumns(),
		e.getState().columnPinning.left,
		e.getState().columnPinning.right
	], (t, n, r, i) => {
		var a, o;
		let s = (a = r == null ? void 0 : r.map((e) => n.find((t) => t.id === e)).filter(Boolean)) == null ? [] : a, c = (o = i == null ? void 0 : i.map((e) => n.find((t) => t.id === e)).filter(Boolean)) == null ? [] : o, l = n.filter((e) => !(r != null && r.includes(e.id)) && !(i != null && i.includes(e.id)));
		return tF(t, [
			...s,
			...l,
			...c
		], e);
	}, Q(e.options, QP, "getHeaderGroups")), e.getCenterHeaderGroups = Z(() => [
		e.getAllColumns(),
		e.getVisibleLeafColumns(),
		e.getState().columnPinning.left,
		e.getState().columnPinning.right
	], (t, n, r, i) => (n = n.filter((e) => !(r != null && r.includes(e.id)) && !(i != null && i.includes(e.id))), tF(t, n, e, "center")), Q(e.options, QP, "getCenterHeaderGroups")), e.getLeftHeaderGroups = Z(() => [
		e.getAllColumns(),
		e.getVisibleLeafColumns(),
		e.getState().columnPinning.left
	], (t, n, r) => {
		var i;
		return tF(t, (i = r == null ? void 0 : r.map((e) => n.find((t) => t.id === e)).filter(Boolean)) == null ? [] : i, e, "left");
	}, Q(e.options, QP, "getLeftHeaderGroups")), e.getRightHeaderGroups = Z(() => [
		e.getAllColumns(),
		e.getVisibleLeafColumns(),
		e.getState().columnPinning.right
	], (t, n, r) => {
		var i;
		return tF(t, (i = r == null ? void 0 : r.map((e) => n.find((t) => t.id === e)).filter(Boolean)) == null ? [] : i, e, "right");
	}, Q(e.options, QP, "getRightHeaderGroups")), e.getFooterGroups = Z(() => [e.getHeaderGroups()], (e) => [...e].reverse(), Q(e.options, QP, "getFooterGroups")), e.getLeftFooterGroups = Z(() => [e.getLeftHeaderGroups()], (e) => [...e].reverse(), Q(e.options, QP, "getLeftFooterGroups")), e.getCenterFooterGroups = Z(() => [e.getCenterHeaderGroups()], (e) => [...e].reverse(), Q(e.options, QP, "getCenterFooterGroups")), e.getRightFooterGroups = Z(() => [e.getRightHeaderGroups()], (e) => [...e].reverse(), Q(e.options, QP, "getRightFooterGroups")), e.getFlatHeaders = Z(() => [e.getHeaderGroups()], (e) => e.map((e) => e.headers).flat(), Q(e.options, QP, "getFlatHeaders")), e.getLeftFlatHeaders = Z(() => [e.getLeftHeaderGroups()], (e) => e.map((e) => e.headers).flat(), Q(e.options, QP, "getLeftFlatHeaders")), e.getCenterFlatHeaders = Z(() => [e.getCenterHeaderGroups()], (e) => e.map((e) => e.headers).flat(), Q(e.options, QP, "getCenterFlatHeaders")), e.getRightFlatHeaders = Z(() => [e.getRightHeaderGroups()], (e) => e.map((e) => e.headers).flat(), Q(e.options, QP, "getRightFlatHeaders")), e.getCenterLeafHeaders = Z(() => [e.getCenterFlatHeaders()], (e) => e.filter((e) => {
		var t;
		return !((t = e.subHeaders) != null && t.length);
	}), Q(e.options, QP, "getCenterLeafHeaders")), e.getLeftLeafHeaders = Z(() => [e.getLeftFlatHeaders()], (e) => e.filter((e) => {
		var t;
		return !((t = e.subHeaders) != null && t.length);
	}), Q(e.options, QP, "getLeftLeafHeaders")), e.getRightLeafHeaders = Z(() => [e.getRightFlatHeaders()], (e) => e.filter((e) => {
		var t;
		return !((t = e.subHeaders) != null && t.length);
	}), Q(e.options, QP, "getRightLeafHeaders")), e.getLeafHeaders = Z(() => [
		e.getLeftHeaderGroups(),
		e.getCenterHeaderGroups(),
		e.getRightHeaderGroups()
	], (e, t, n) => {
		var r, i, a, o, s, c;
		return [
			...(r = (i = e[0]) == null ? void 0 : i.headers) == null ? [] : r,
			...(a = (o = t[0]) == null ? void 0 : o.headers) == null ? [] : a,
			...(s = (c = n[0]) == null ? void 0 : c.headers) == null ? [] : s
		].map((e) => e.getLeafHeaders()).flat();
	}, Q(e.options, QP, "getLeafHeaders"));
} };
function tF(e, t, n, r) {
	var i, a;
	let o = 0, s = function(e, t) {
		t === void 0 && (t = 1), o = Math.max(o, t), e.filter((e) => e.getIsVisible()).forEach((e) => {
			var n;
			(n = e.columns) != null && n.length && s(e.columns, t + 1);
		}, 0);
	};
	s(e);
	let c = [], l = (e, t) => {
		let i = {
			depth: t,
			id: [r, `${t}`].filter(Boolean).join("_"),
			headers: []
		}, a = [];
		e.forEach((e) => {
			let o = [...a].reverse()[0], s = e.column.depth === i.depth, c, l = !1;
			if (s && e.column.parent ? c = e.column.parent : (c = e.column, l = !0), o && (o == null ? void 0 : o.column) === c) o.subHeaders.push(e);
			else {
				let i = $P(n, c, {
					id: [
						r,
						t,
						c.id,
						e == null ? void 0 : e.id
					].filter(Boolean).join("_"),
					isPlaceholder: l,
					placeholderId: l ? `${a.filter((e) => e.column === c).length}` : void 0,
					depth: t,
					index: a.length
				});
				i.subHeaders.push(e), a.push(i);
			}
			i.headers.push(e), e.headerGroup = i;
		}), c.push(i), t > 0 && l(a, t - 1);
	};
	l(t.map((e, t) => $P(n, e, {
		depth: o,
		index: t
	})), o - 1), c.reverse();
	let u = (e) => e.filter((e) => e.column.getIsVisible()).map((e) => {
		let t = 0, n = 0, r = [0];
		e.subHeaders && e.subHeaders.length ? (r = [], u(e.subHeaders).forEach((e) => {
			let { colSpan: n, rowSpan: i } = e;
			t += n, r.push(i);
		})) : t = 1;
		let i = Math.min(...r);
		return n += i, e.colSpan = t, e.rowSpan = n, {
			colSpan: t,
			rowSpan: n
		};
	});
	return u((i = (a = c[0]) == null ? void 0 : a.headers) == null ? [] : i), c;
}
var nF = (e, t, n, r, i, a, o) => {
	let s = {
		id: t,
		index: r,
		original: n,
		depth: i,
		parentId: o,
		_valuesCache: {},
		_uniqueValuesCache: {},
		getValue: (t) => {
			if (s._valuesCache.hasOwnProperty(t)) return s._valuesCache[t];
			let n = e.getColumn(t);
			if (n != null && n.accessorFn) return s._valuesCache[t] = n.accessorFn(s.original, r), s._valuesCache[t];
		},
		getUniqueValues: (t) => {
			if (s._uniqueValuesCache.hasOwnProperty(t)) return s._uniqueValuesCache[t];
			let n = e.getColumn(t);
			if (n != null && n.accessorFn) return n.columnDef.getUniqueValues ? (s._uniqueValuesCache[t] = n.columnDef.getUniqueValues(s.original, r), s._uniqueValuesCache[t]) : (s._uniqueValuesCache[t] = [s.getValue(t)], s._uniqueValuesCache[t]);
		},
		renderValue: (t) => {
			var n;
			return (n = s.getValue(t)) == null ? e.options.renderFallbackValue : n;
		},
		subRows: a == null ? [] : a,
		getLeafRows: () => YP(s.subRows, (e) => e.subRows),
		getParentRow: () => s.parentId ? e.getRow(s.parentId, !0) : void 0,
		getParentRows: () => {
			let e = [], t = s;
			for (;;) {
				let n = t.getParentRow();
				if (!n) break;
				e.push(n), t = n;
			}
			return e.reverse();
		},
		getAllCells: Z(() => [e.getAllLeafColumns()], (t) => t.map((t) => XP(e, s, t, t.id)), Q(e.options, "debugRows", "getAllCells")),
		_getAllCellsByColumnId: Z(() => [s.getAllCells()], (e) => e.reduce((e, t) => (e[t.column.id] = t, e), {}), Q(e.options, "debugRows", "getAllCellsByColumnId"))
	};
	for (let t = 0; t < e._features.length; t++) {
		let n = e._features[t];
		n == null || n.createRow == null || n.createRow(s, e);
	}
	return s;
}, rF = { createColumn: (e, t) => {
	e._getFacetedRowModel = t.options.getFacetedRowModel && t.options.getFacetedRowModel(t, e.id), e.getFacetedRowModel = () => e._getFacetedRowModel ? e._getFacetedRowModel() : t.getPreFilteredRowModel(), e._getFacetedUniqueValues = t.options.getFacetedUniqueValues && t.options.getFacetedUniqueValues(t, e.id), e.getFacetedUniqueValues = () => e._getFacetedUniqueValues ? e._getFacetedUniqueValues() : /* @__PURE__ */ new Map(), e._getFacetedMinMaxValues = t.options.getFacetedMinMaxValues && t.options.getFacetedMinMaxValues(t, e.id), e.getFacetedMinMaxValues = () => {
		if (e._getFacetedMinMaxValues) return e._getFacetedMinMaxValues();
	};
} }, iF = (e, t, n) => {
	var r, i;
	let a = n == null || (r = n.toString()) == null ? void 0 : r.toLowerCase();
	return !!(!((i = e.getValue(t)) == null || (i = i.toString()) == null || (i = i.toLowerCase()) == null) && i.includes(a));
};
iF.autoRemove = (e) => mF(e);
var aF = (e, t, n) => {
	var r;
	return !!(!((r = e.getValue(t)) == null || (r = r.toString()) == null) && r.includes(n));
};
aF.autoRemove = (e) => mF(e);
var oF = (e, t, n) => {
	var r;
	return ((r = e.getValue(t)) == null || (r = r.toString()) == null ? void 0 : r.toLowerCase()) === (n == null ? void 0 : n.toLowerCase());
};
oF.autoRemove = (e) => mF(e);
var sF = (e, t, n) => {
	var r;
	return (r = e.getValue(t)) == null ? void 0 : r.includes(n);
};
sF.autoRemove = (e) => mF(e);
var cF = (e, t, n) => !n.some((n) => {
	var r;
	return !((r = e.getValue(t)) != null && r.includes(n));
});
cF.autoRemove = (e) => mF(e) || !(e != null && e.length);
var lF = (e, t, n) => n.some((n) => {
	var r;
	return (r = e.getValue(t)) == null ? void 0 : r.includes(n);
});
lF.autoRemove = (e) => mF(e) || !(e != null && e.length);
var uF = (e, t, n) => e.getValue(t) === n;
uF.autoRemove = (e) => mF(e);
var dF = (e, t, n) => e.getValue(t) == n;
dF.autoRemove = (e) => mF(e);
var fF = (e, t, n) => {
	let [r, i] = n, a = e.getValue(t);
	return a >= r && a <= i;
};
fF.resolveFilterValue = (e) => {
	let [t, n] = e, r = typeof t == "number" ? t : parseFloat(t), i = typeof n == "number" ? n : parseFloat(n), a = t === null || Number.isNaN(r) ? -Infinity : r, o = n === null || Number.isNaN(i) ? Infinity : i;
	if (a > o) {
		let e = a;
		a = o, o = e;
	}
	return [a, o];
}, fF.autoRemove = (e) => mF(e) || mF(e[0]) && mF(e[1]);
var pF = {
	includesString: iF,
	includesStringSensitive: aF,
	equalsString: oF,
	arrIncludes: sF,
	arrIncludesAll: cF,
	arrIncludesSome: lF,
	equals: uF,
	weakEquals: dF,
	inNumberRange: fF
};
function mF(e) {
	return e == null || e === "";
}
var hF = {
	getDefaultColumnDef: () => ({ filterFn: "auto" }),
	getInitialState: (e) => ({
		columnFilters: [],
		...e
	}),
	getDefaultOptions: (e) => ({
		onColumnFiltersChange: KP("columnFilters", e),
		filterFromLeafRows: !1,
		maxLeafRowFilterDepth: 100
	}),
	createColumn: (e, t) => {
		e.getAutoFilterFn = () => {
			let n = t.getCoreRowModel().flatRows[0], r = n == null ? void 0 : n.getValue(e.id);
			return typeof r == "string" ? pF.includesString : typeof r == "number" ? pF.inNumberRange : typeof r == "boolean" || typeof r == "object" && r ? pF.equals : Array.isArray(r) ? pF.arrIncludes : pF.weakEquals;
		}, e.getFilterFn = () => {
			var n, r;
			return qP(e.columnDef.filterFn) ? e.columnDef.filterFn : e.columnDef.filterFn === "auto" ? e.getAutoFilterFn() : (n = (r = t.options.filterFns) == null ? void 0 : r[e.columnDef.filterFn]) == null ? pF[e.columnDef.filterFn] : n;
		}, e.getCanFilter = () => {
			var n, r, i;
			return ((n = e.columnDef.enableColumnFilter) == null || n) && ((r = t.options.enableColumnFilters) == null || r) && ((i = t.options.enableFilters) == null || i) && !!e.accessorFn;
		}, e.getIsFiltered = () => e.getFilterIndex() > -1, e.getFilterValue = () => {
			var n;
			return (n = t.getState().columnFilters) == null || (n = n.find((t) => t.id === e.id)) == null ? void 0 : n.value;
		}, e.getFilterIndex = () => {
			var n, r;
			return (n = (r = t.getState().columnFilters) == null ? void 0 : r.findIndex((t) => t.id === e.id)) == null ? -1 : n;
		}, e.setFilterValue = (n) => {
			t.setColumnFilters((t) => {
				let r = e.getFilterFn(), i = t == null ? void 0 : t.find((t) => t.id === e.id), a = GP(n, i ? i.value : void 0);
				if (gF(r, a, e)) {
					var o;
					return (o = t == null ? void 0 : t.filter((t) => t.id !== e.id)) == null ? [] : o;
				}
				let s = {
					id: e.id,
					value: a
				};
				if (i) {
					var c;
					return (c = t == null ? void 0 : t.map((t) => t.id === e.id ? s : t)) == null ? [] : c;
				}
				return t != null && t.length ? [...t, s] : [s];
			});
		};
	},
	createRow: (e, t) => {
		e.columnFilters = {}, e.columnFiltersMeta = {};
	},
	createTable: (e) => {
		e.setColumnFilters = (t) => {
			let n = e.getAllLeafColumns();
			e.options.onColumnFiltersChange == null || e.options.onColumnFiltersChange((e) => {
				var r;
				return (r = GP(t, e)) == null ? void 0 : r.filter((e) => {
					let t = n.find((t) => t.id === e.id);
					return !(t && gF(t.getFilterFn(), e.value, t));
				});
			});
		}, e.resetColumnFilters = (t) => {
			var n, r;
			e.setColumnFilters(t || (n = (r = e.initialState) == null ? void 0 : r.columnFilters) == null ? [] : n);
		}, e.getPreFilteredRowModel = () => e.getCoreRowModel(), e.getFilteredRowModel = () => (!e._getFilteredRowModel && e.options.getFilteredRowModel && (e._getFilteredRowModel = e.options.getFilteredRowModel(e)), e.options.manualFiltering || !e._getFilteredRowModel ? e.getPreFilteredRowModel() : e._getFilteredRowModel());
	}
};
function gF(e, t, n) {
	return (e && e.autoRemove ? e.autoRemove(t, n) : !1) || t === void 0 || typeof t == "string" && !t;
}
var _F = {
	sum: (e, t, n) => n.reduce((t, n) => {
		let r = n.getValue(e);
		return t + (typeof r == "number" ? r : 0);
	}, 0),
	min: (e, t, n) => {
		let r;
		return n.forEach((t) => {
			let n = t.getValue(e);
			n != null && (r > n || r === void 0 && n >= n) && (r = n);
		}), r;
	},
	max: (e, t, n) => {
		let r;
		return n.forEach((t) => {
			let n = t.getValue(e);
			n != null && (r < n || r === void 0 && n >= n) && (r = n);
		}), r;
	},
	extent: (e, t, n) => {
		let r, i;
		return n.forEach((t) => {
			let n = t.getValue(e);
			n != null && (r === void 0 ? n >= n && (r = i = n) : (r > n && (r = n), i < n && (i = n)));
		}), [r, i];
	},
	mean: (e, t) => {
		let n = 0, r = 0;
		if (t.forEach((t) => {
			let i = t.getValue(e);
			i != null && (i = +i) >= i && (++n, r += i);
		}), n) return r / n;
	},
	median: (e, t) => {
		if (!t.length) return;
		let n = t.map((t) => t.getValue(e));
		if (!JP(n)) return;
		if (n.length === 1) return n[0];
		let r = Math.floor(n.length / 2), i = n.sort((e, t) => e - t);
		return n.length % 2 == 0 ? (i[r - 1] + i[r]) / 2 : i[r];
	},
	unique: (e, t) => Array.from(new Set(t.map((t) => t.getValue(e))).values()),
	uniqueCount: (e, t) => new Set(t.map((t) => t.getValue(e))).size,
	count: (e, t) => t.length
}, vF = {
	getDefaultColumnDef: () => ({
		aggregatedCell: (e) => {
			var t, n;
			return (t = (n = e.getValue()) == null || n.toString == null ? void 0 : n.toString()) == null ? null : t;
		},
		aggregationFn: "auto"
	}),
	getInitialState: (e) => ({
		grouping: [],
		...e
	}),
	getDefaultOptions: (e) => ({
		onGroupingChange: KP("grouping", e),
		groupedColumnMode: "reorder"
	}),
	createColumn: (e, t) => {
		e.toggleGrouping = () => {
			t.setGrouping((t) => t != null && t.includes(e.id) ? t.filter((t) => t !== e.id) : [...t == null ? [] : t, e.id]);
		}, e.getCanGroup = () => {
			var n, r;
			return ((n = e.columnDef.enableGrouping) == null || n) && ((r = t.options.enableGrouping) == null || r) && (!!e.accessorFn || !!e.columnDef.getGroupingValue);
		}, e.getIsGrouped = () => {
			var n;
			return (n = t.getState().grouping) == null ? void 0 : n.includes(e.id);
		}, e.getGroupedIndex = () => {
			var n;
			return (n = t.getState().grouping) == null ? void 0 : n.indexOf(e.id);
		}, e.getToggleGroupingHandler = () => {
			let t = e.getCanGroup();
			return () => {
				t && e.toggleGrouping();
			};
		}, e.getAutoAggregationFn = () => {
			let n = t.getCoreRowModel().flatRows[0], r = n == null ? void 0 : n.getValue(e.id);
			if (typeof r == "number") return _F.sum;
			if (Object.prototype.toString.call(r) === "[object Date]") return _F.extent;
		}, e.getAggregationFn = () => {
			var n, r;
			if (!e) throw Error();
			return qP(e.columnDef.aggregationFn) ? e.columnDef.aggregationFn : e.columnDef.aggregationFn === "auto" ? e.getAutoAggregationFn() : (n = (r = t.options.aggregationFns) == null ? void 0 : r[e.columnDef.aggregationFn]) == null ? _F[e.columnDef.aggregationFn] : n;
		};
	},
	createTable: (e) => {
		e.setGrouping = (t) => e.options.onGroupingChange == null ? void 0 : e.options.onGroupingChange(t), e.resetGrouping = (t) => {
			var n, r;
			e.setGrouping(t || (n = (r = e.initialState) == null ? void 0 : r.grouping) == null ? [] : n);
		}, e.getPreGroupedRowModel = () => e.getFilteredRowModel(), e.getGroupedRowModel = () => (!e._getGroupedRowModel && e.options.getGroupedRowModel && (e._getGroupedRowModel = e.options.getGroupedRowModel(e)), e.options.manualGrouping || !e._getGroupedRowModel ? e.getPreGroupedRowModel() : e._getGroupedRowModel());
	},
	createRow: (e, t) => {
		e.getIsGrouped = () => !!e.groupingColumnId, e.getGroupingValue = (n) => {
			if (e._groupingValuesCache.hasOwnProperty(n)) return e._groupingValuesCache[n];
			let r = t.getColumn(n);
			return r != null && r.columnDef.getGroupingValue ? (e._groupingValuesCache[n] = r.columnDef.getGroupingValue(e.original), e._groupingValuesCache[n]) : e.getValue(n);
		}, e._groupingValuesCache = {};
	},
	createCell: (e, t, n, r) => {
		e.getIsGrouped = () => t.getIsGrouped() && t.id === n.groupingColumnId, e.getIsPlaceholder = () => !e.getIsGrouped() && t.getIsGrouped(), e.getIsAggregated = () => {
			var t;
			return !e.getIsGrouped() && !e.getIsPlaceholder() && !!((t = n.subRows) != null && t.length);
		};
	}
};
function yF(e, t, n) {
	if (!(t != null && t.length) || !n) return e;
	let r = e.filter((e) => !t.includes(e.id));
	return n === "remove" ? r : [...t.map((t) => e.find((e) => e.id === t)).filter(Boolean), ...r];
}
var bF = {
	getInitialState: (e) => ({
		columnOrder: [],
		...e
	}),
	getDefaultOptions: (e) => ({ onColumnOrderChange: KP("columnOrder", e) }),
	createColumn: (e, t) => {
		e.getIndex = Z((e) => [jF(t, e)], (t) => t.findIndex((t) => t.id === e.id), Q(t.options, "debugColumns", "getIndex")), e.getIsFirstColumn = (n) => {
			var r;
			return ((r = jF(t, n)[0]) == null ? void 0 : r.id) === e.id;
		}, e.getIsLastColumn = (n) => {
			var r;
			let i = jF(t, n);
			return ((r = i[i.length - 1]) == null ? void 0 : r.id) === e.id;
		};
	},
	createTable: (e) => {
		e.setColumnOrder = (t) => e.options.onColumnOrderChange == null ? void 0 : e.options.onColumnOrderChange(t), e.resetColumnOrder = (t) => {
			var n;
			e.setColumnOrder(t || (n = e.initialState.columnOrder) == null ? [] : n);
		}, e._getOrderColumnsFn = Z(() => [
			e.getState().columnOrder,
			e.getState().grouping,
			e.options.groupedColumnMode
		], (e, t, n) => (r) => {
			let i = [];
			if (!(e != null && e.length)) i = r;
			else {
				let t = [...e], n = [...r];
				for (; n.length && t.length;) {
					let e = t.shift(), r = n.findIndex((t) => t.id === e);
					r > -1 && i.push(n.splice(r, 1)[0]);
				}
				i = [...i, ...n];
			}
			return yF(i, t, n);
		}, Q(e.options, "debugTable", "_getOrderColumnsFn"));
	}
}, xF = () => ({
	left: [],
	right: []
}), SF = {
	getInitialState: (e) => ({
		columnPinning: xF(),
		...e
	}),
	getDefaultOptions: (e) => ({ onColumnPinningChange: KP("columnPinning", e) }),
	createColumn: (e, t) => {
		e.pin = (n) => {
			let r = e.getLeafColumns().map((e) => e.id).filter(Boolean);
			t.setColumnPinning((e) => {
				var t, i;
				if (n === "right") {
					var a, o;
					return {
						left: ((a = e == null ? void 0 : e.left) == null ? [] : a).filter((e) => !(r != null && r.includes(e))),
						right: [...((o = e == null ? void 0 : e.right) == null ? [] : o).filter((e) => !(r != null && r.includes(e))), ...r]
					};
				}
				if (n === "left") {
					var s, c;
					return {
						left: [...((s = e == null ? void 0 : e.left) == null ? [] : s).filter((e) => !(r != null && r.includes(e))), ...r],
						right: ((c = e == null ? void 0 : e.right) == null ? [] : c).filter((e) => !(r != null && r.includes(e)))
					};
				}
				return {
					left: ((t = e == null ? void 0 : e.left) == null ? [] : t).filter((e) => !(r != null && r.includes(e))),
					right: ((i = e == null ? void 0 : e.right) == null ? [] : i).filter((e) => !(r != null && r.includes(e)))
				};
			});
		}, e.getCanPin = () => e.getLeafColumns().some((e) => {
			var n, r, i;
			return ((n = e.columnDef.enablePinning) == null || n) && ((r = (i = t.options.enableColumnPinning) == null ? t.options.enablePinning : i) == null || r);
		}), e.getIsPinned = () => {
			let n = e.getLeafColumns().map((e) => e.id), { left: r, right: i } = t.getState().columnPinning, a = n.some((e) => r == null ? void 0 : r.includes(e)), o = n.some((e) => i == null ? void 0 : i.includes(e));
			return a ? "left" : o ? "right" : !1;
		}, e.getPinnedIndex = () => {
			var n, r;
			let i = e.getIsPinned();
			return i ? (n = (r = t.getState().columnPinning) == null || (r = r[i]) == null ? void 0 : r.indexOf(e.id)) == null ? -1 : n : 0;
		};
	},
	createRow: (e, t) => {
		e.getCenterVisibleCells = Z(() => [
			e._getAllVisibleCells(),
			t.getState().columnPinning.left,
			t.getState().columnPinning.right
		], (e, t, n) => {
			let r = [...t == null ? [] : t, ...n == null ? [] : n];
			return e.filter((e) => !r.includes(e.column.id));
		}, Q(t.options, "debugRows", "getCenterVisibleCells")), e.getLeftVisibleCells = Z(() => [e._getAllVisibleCells(), t.getState().columnPinning.left], (e, t) => (t == null ? [] : t).map((t) => e.find((e) => e.column.id === t)).filter(Boolean).map((e) => ({
			...e,
			position: "left"
		})), Q(t.options, "debugRows", "getLeftVisibleCells")), e.getRightVisibleCells = Z(() => [e._getAllVisibleCells(), t.getState().columnPinning.right], (e, t) => (t == null ? [] : t).map((t) => e.find((e) => e.column.id === t)).filter(Boolean).map((e) => ({
			...e,
			position: "right"
		})), Q(t.options, "debugRows", "getRightVisibleCells"));
	},
	createTable: (e) => {
		e.setColumnPinning = (t) => e.options.onColumnPinningChange == null ? void 0 : e.options.onColumnPinningChange(t), e.resetColumnPinning = (t) => {
			var n, r;
			return e.setColumnPinning(t || (n = (r = e.initialState) == null ? void 0 : r.columnPinning) == null ? xF() : n);
		}, e.getIsSomeColumnsPinned = (t) => {
			var n;
			let r = e.getState().columnPinning;
			if (!t) {
				var i, a;
				return !!((i = r.left) != null && i.length || (a = r.right) != null && a.length);
			}
			return !!((n = r[t]) != null && n.length);
		}, e.getLeftLeafColumns = Z(() => [e.getAllLeafColumns(), e.getState().columnPinning.left], (e, t) => (t == null ? [] : t).map((t) => e.find((e) => e.id === t)).filter(Boolean), Q(e.options, "debugColumns", "getLeftLeafColumns")), e.getRightLeafColumns = Z(() => [e.getAllLeafColumns(), e.getState().columnPinning.right], (e, t) => (t == null ? [] : t).map((t) => e.find((e) => e.id === t)).filter(Boolean), Q(e.options, "debugColumns", "getRightLeafColumns")), e.getCenterLeafColumns = Z(() => [
			e.getAllLeafColumns(),
			e.getState().columnPinning.left,
			e.getState().columnPinning.right
		], (e, t, n) => {
			let r = [...t == null ? [] : t, ...n == null ? [] : n];
			return e.filter((e) => !r.includes(e.id));
		}, Q(e.options, "debugColumns", "getCenterLeafColumns"));
	}
};
function CF(e) {
	return e || (typeof document < "u" ? document : null);
}
var wF = {
	size: 150,
	minSize: 20,
	maxSize: 2 ** 53 - 1
}, TF = () => ({
	startOffset: null,
	startSize: null,
	deltaOffset: null,
	deltaPercentage: null,
	isResizingColumn: !1,
	columnSizingStart: []
}), EF = {
	getDefaultColumnDef: () => wF,
	getInitialState: (e) => ({
		columnSizing: {},
		columnSizingInfo: TF(),
		...e
	}),
	getDefaultOptions: (e) => ({
		columnResizeMode: "onEnd",
		columnResizeDirection: "ltr",
		onColumnSizingChange: KP("columnSizing", e),
		onColumnSizingInfoChange: KP("columnSizingInfo", e)
	}),
	createColumn: (e, t) => {
		e.getSize = () => {
			var n, r, i;
			let a = t.getState().columnSizing[e.id];
			return Math.min(Math.max((n = e.columnDef.minSize) == null ? wF.minSize : n, (r = a == null ? e.columnDef.size : a) == null ? wF.size : r), (i = e.columnDef.maxSize) == null ? wF.maxSize : i);
		}, e.getStart = Z((e) => [
			e,
			jF(t, e),
			t.getState().columnSizing
		], (t, n) => n.slice(0, e.getIndex(t)).reduce((e, t) => e + t.getSize(), 0), Q(t.options, "debugColumns", "getStart")), e.getAfter = Z((e) => [
			e,
			jF(t, e),
			t.getState().columnSizing
		], (t, n) => n.slice(e.getIndex(t) + 1).reduce((e, t) => e + t.getSize(), 0), Q(t.options, "debugColumns", "getAfter")), e.resetSize = () => {
			t.setColumnSizing((t) => {
				let { [e.id]: n, ...r } = t;
				return r;
			});
		}, e.getCanResize = () => {
			var n, r;
			return ((n = e.columnDef.enableResizing) == null || n) && ((r = t.options.enableColumnResizing) == null || r);
		}, e.getIsResizing = () => t.getState().columnSizingInfo.isResizingColumn === e.id;
	},
	createHeader: (e, t) => {
		e.getSize = () => {
			let t = 0, n = (e) => {
				if (e.subHeaders.length) e.subHeaders.forEach(n);
				else {
					var r;
					t += (r = e.column.getSize()) == null ? 0 : r;
				}
			};
			return n(e), t;
		}, e.getStart = () => {
			if (e.index > 0) {
				let t = e.headerGroup.headers[e.index - 1];
				return t.getStart() + t.getSize();
			}
			return 0;
		}, e.getResizeHandler = (n) => {
			let r = t.getColumn(e.column.id), i = r == null ? void 0 : r.getCanResize();
			return (a) => {
				if (!r || !i || (a.persist == null || a.persist(), kF(a) && a.touches && a.touches.length > 1)) return;
				let o = e.getSize(), s = e ? e.getLeafHeaders().map((e) => [e.column.id, e.column.getSize()]) : [[r.id, r.getSize()]], c = kF(a) ? Math.round(a.touches[0].clientX) : a.clientX, l = {}, u = (e, n) => {
					typeof n == "number" && (t.setColumnSizingInfo((e) => {
						var r, i;
						let a = t.options.columnResizeDirection === "rtl" ? -1 : 1, o = (n - ((r = e == null ? void 0 : e.startOffset) == null ? 0 : r)) * a, s = Math.max(o / ((i = e == null ? void 0 : e.startSize) == null ? 0 : i), -.999999);
						return e.columnSizingStart.forEach((e) => {
							let [t, n] = e;
							l[t] = Math.round(Math.max(n + n * s, 0) * 100) / 100;
						}), {
							...e,
							deltaOffset: o,
							deltaPercentage: s
						};
					}), (t.options.columnResizeMode === "onChange" || e === "end") && t.setColumnSizing((e) => ({
						...e,
						...l
					})));
				}, d = (e) => u("move", e), f = (e) => {
					u("end", e), t.setColumnSizingInfo((e) => ({
						...e,
						isResizingColumn: !1,
						startOffset: null,
						startSize: null,
						deltaOffset: null,
						deltaPercentage: null,
						columnSizingStart: []
					}));
				}, p = CF(n), m = {
					moveHandler: (e) => d(e.clientX),
					upHandler: (e) => {
						p == null || p.removeEventListener("mousemove", m.moveHandler), p == null || p.removeEventListener("mouseup", m.upHandler), f(e.clientX);
					}
				}, h = {
					moveHandler: (e) => (e.cancelable && (e.preventDefault(), e.stopPropagation()), d(e.touches[0].clientX), !1),
					upHandler: (e) => {
						var t;
						p == null || p.removeEventListener("touchmove", h.moveHandler), p == null || p.removeEventListener("touchend", h.upHandler), e.cancelable && (e.preventDefault(), e.stopPropagation()), f((t = e.touches[0]) == null ? void 0 : t.clientX);
					}
				}, g = OF() ? { passive: !1 } : !1;
				kF(a) ? (p == null || p.addEventListener("touchmove", h.moveHandler, g), p == null || p.addEventListener("touchend", h.upHandler, g)) : (p == null || p.addEventListener("mousemove", m.moveHandler, g), p == null || p.addEventListener("mouseup", m.upHandler, g)), t.setColumnSizingInfo((e) => ({
					...e,
					startOffset: c,
					startSize: o,
					deltaOffset: 0,
					deltaPercentage: 0,
					columnSizingStart: s,
					isResizingColumn: r.id
				}));
			};
		};
	},
	createTable: (e) => {
		e.setColumnSizing = (t) => e.options.onColumnSizingChange == null ? void 0 : e.options.onColumnSizingChange(t), e.setColumnSizingInfo = (t) => e.options.onColumnSizingInfoChange == null ? void 0 : e.options.onColumnSizingInfoChange(t), e.resetColumnSizing = (t) => {
			var n;
			e.setColumnSizing(t || (n = e.initialState.columnSizing) == null ? {} : n);
		}, e.resetHeaderSizeInfo = (t) => {
			var n;
			e.setColumnSizingInfo(t || (n = e.initialState.columnSizingInfo) == null ? TF() : n);
		}, e.getTotalSize = () => {
			var t, n;
			return (t = (n = e.getHeaderGroups()[0]) == null ? void 0 : n.headers.reduce((e, t) => e + t.getSize(), 0)) == null ? 0 : t;
		}, e.getLeftTotalSize = () => {
			var t, n;
			return (t = (n = e.getLeftHeaderGroups()[0]) == null ? void 0 : n.headers.reduce((e, t) => e + t.getSize(), 0)) == null ? 0 : t;
		}, e.getCenterTotalSize = () => {
			var t, n;
			return (t = (n = e.getCenterHeaderGroups()[0]) == null ? void 0 : n.headers.reduce((e, t) => e + t.getSize(), 0)) == null ? 0 : t;
		}, e.getRightTotalSize = () => {
			var t, n;
			return (t = (n = e.getRightHeaderGroups()[0]) == null ? void 0 : n.headers.reduce((e, t) => e + t.getSize(), 0)) == null ? 0 : t;
		};
	}
}, DF = null;
function OF() {
	if (typeof DF == "boolean") return DF;
	let e = !1;
	try {
		let t = { get passive() {
			return e = !0, !1;
		} }, n = () => {};
		window.addEventListener("test", n, t), window.removeEventListener("test", n);
	} catch (t) {
		e = !1;
	}
	return DF = e, DF;
}
function kF(e) {
	return e.type === "touchstart";
}
var AF = {
	getInitialState: (e) => ({
		columnVisibility: {},
		...e
	}),
	getDefaultOptions: (e) => ({ onColumnVisibilityChange: KP("columnVisibility", e) }),
	createColumn: (e, t) => {
		e.toggleVisibility = (n) => {
			e.getCanHide() && t.setColumnVisibility((t) => ({
				...t,
				[e.id]: n == null ? !e.getIsVisible() : n
			}));
		}, e.getIsVisible = () => {
			var n, r;
			let i = e.columns;
			return (n = i.length ? i.some((e) => e.getIsVisible()) : (r = t.getState().columnVisibility) == null ? void 0 : r[e.id]) == null || n;
		}, e.getCanHide = () => {
			var n, r;
			return ((n = e.columnDef.enableHiding) == null || n) && ((r = t.options.enableHiding) == null || r);
		}, e.getToggleVisibilityHandler = () => (t) => {
			e.toggleVisibility == null || e.toggleVisibility(t.target.checked);
		};
	},
	createRow: (e, t) => {
		e._getAllVisibleCells = Z(() => [e.getAllCells(), t.getState().columnVisibility], (e) => e.filter((e) => e.column.getIsVisible()), Q(t.options, "debugRows", "_getAllVisibleCells")), e.getVisibleCells = Z(() => [
			e.getLeftVisibleCells(),
			e.getCenterVisibleCells(),
			e.getRightVisibleCells()
		], (e, t, n) => [
			...e,
			...t,
			...n
		], Q(t.options, "debugRows", "getVisibleCells"));
	},
	createTable: (e) => {
		let t = (t, n) => Z(() => [n(), n().filter((e) => e.getIsVisible()).map((e) => e.id).join("_")], (e) => e.filter((e) => e.getIsVisible == null ? void 0 : e.getIsVisible()), Q(e.options, "debugColumns", t));
		e.getVisibleFlatColumns = t("getVisibleFlatColumns", () => e.getAllFlatColumns()), e.getVisibleLeafColumns = t("getVisibleLeafColumns", () => e.getAllLeafColumns()), e.getLeftVisibleLeafColumns = t("getLeftVisibleLeafColumns", () => e.getLeftLeafColumns()), e.getRightVisibleLeafColumns = t("getRightVisibleLeafColumns", () => e.getRightLeafColumns()), e.getCenterVisibleLeafColumns = t("getCenterVisibleLeafColumns", () => e.getCenterLeafColumns()), e.setColumnVisibility = (t) => e.options.onColumnVisibilityChange == null ? void 0 : e.options.onColumnVisibilityChange(t), e.resetColumnVisibility = (t) => {
			var n;
			e.setColumnVisibility(t || (n = e.initialState.columnVisibility) == null ? {} : n);
		}, e.toggleAllColumnsVisible = (t) => {
			var n;
			t = (n = t) == null ? !e.getIsAllColumnsVisible() : n, e.setColumnVisibility(e.getAllLeafColumns().reduce((e, n) => ({
				...e,
				[n.id]: t || !(n.getCanHide != null && n.getCanHide())
			}), {}));
		}, e.getIsAllColumnsVisible = () => !e.getAllLeafColumns().some((e) => !(e.getIsVisible != null && e.getIsVisible())), e.getIsSomeColumnsVisible = () => e.getAllLeafColumns().some((e) => e.getIsVisible == null ? void 0 : e.getIsVisible()), e.getToggleAllColumnsVisibilityHandler = () => (t) => {
			var n;
			e.toggleAllColumnsVisible((n = t.target) == null ? void 0 : n.checked);
		};
	}
};
function jF(e, t) {
	return t ? t === "center" ? e.getCenterVisibleLeafColumns() : t === "left" ? e.getLeftVisibleLeafColumns() : e.getRightVisibleLeafColumns() : e.getVisibleLeafColumns();
}
var MF = { createTable: (e) => {
	e._getGlobalFacetedRowModel = e.options.getFacetedRowModel && e.options.getFacetedRowModel(e, "__global__"), e.getGlobalFacetedRowModel = () => e.options.manualFiltering || !e._getGlobalFacetedRowModel ? e.getPreFilteredRowModel() : e._getGlobalFacetedRowModel(), e._getGlobalFacetedUniqueValues = e.options.getFacetedUniqueValues && e.options.getFacetedUniqueValues(e, "__global__"), e.getGlobalFacetedUniqueValues = () => e._getGlobalFacetedUniqueValues ? e._getGlobalFacetedUniqueValues() : /* @__PURE__ */ new Map(), e._getGlobalFacetedMinMaxValues = e.options.getFacetedMinMaxValues && e.options.getFacetedMinMaxValues(e, "__global__"), e.getGlobalFacetedMinMaxValues = () => {
		if (e._getGlobalFacetedMinMaxValues) return e._getGlobalFacetedMinMaxValues();
	};
} }, NF = {
	getInitialState: (e) => ({
		globalFilter: void 0,
		...e
	}),
	getDefaultOptions: (e) => ({
		onGlobalFilterChange: KP("globalFilter", e),
		globalFilterFn: "auto",
		getColumnCanGlobalFilter: (t) => {
			var n;
			let r = (n = e.getCoreRowModel().flatRows[0]) == null || (n = n._getAllCellsByColumnId()[t.id]) == null ? void 0 : n.getValue();
			return typeof r == "string" || typeof r == "number";
		}
	}),
	createColumn: (e, t) => {
		e.getCanGlobalFilter = () => {
			var n, r, i, a;
			return ((n = e.columnDef.enableGlobalFilter) == null || n) && ((r = t.options.enableGlobalFilter) == null || r) && ((i = t.options.enableFilters) == null || i) && ((a = t.options.getColumnCanGlobalFilter == null ? void 0 : t.options.getColumnCanGlobalFilter(e)) == null || a) && !!e.accessorFn;
		};
	},
	createTable: (e) => {
		e.getGlobalAutoFilterFn = () => pF.includesString, e.getGlobalFilterFn = () => {
			var t, n;
			let { globalFilterFn: r } = e.options;
			return qP(r) ? r : r === "auto" ? e.getGlobalAutoFilterFn() : (t = (n = e.options.filterFns) == null ? void 0 : n[r]) == null ? pF[r] : t;
		}, e.setGlobalFilter = (t) => {
			e.options.onGlobalFilterChange == null || e.options.onGlobalFilterChange(t);
		}, e.resetGlobalFilter = (t) => {
			e.setGlobalFilter(t ? void 0 : e.initialState.globalFilter);
		};
	}
}, PF = {
	getInitialState: (e) => ({
		expanded: {},
		...e
	}),
	getDefaultOptions: (e) => ({
		onExpandedChange: KP("expanded", e),
		paginateExpandedRows: !0
	}),
	createTable: (e) => {
		let t = !1, n = !1;
		e._autoResetExpanded = () => {
			var r, i;
			if (!t) {
				e._queue(() => {
					t = !0;
				});
				return;
			}
			if ((r = (i = e.options.autoResetAll) == null ? e.options.autoResetExpanded : i) == null ? !e.options.manualExpanding : r) {
				if (n) return;
				n = !0, e._queue(() => {
					e.resetExpanded(), n = !1;
				});
			}
		}, e.setExpanded = (t) => e.options.onExpandedChange == null ? void 0 : e.options.onExpandedChange(t), e.toggleAllRowsExpanded = (t) => {
			(t == null ? !e.getIsAllRowsExpanded() : t) ? e.setExpanded(!0) : e.setExpanded({});
		}, e.resetExpanded = (t) => {
			var n, r;
			e.setExpanded(t || (n = (r = e.initialState) == null ? void 0 : r.expanded) == null ? {} : n);
		}, e.getCanSomeRowsExpand = () => e.getPrePaginationRowModel().flatRows.some((e) => e.getCanExpand()), e.getToggleAllRowsExpandedHandler = () => (t) => {
			t.persist == null || t.persist(), e.toggleAllRowsExpanded();
		}, e.getIsSomeRowsExpanded = () => {
			let t = e.getState().expanded;
			return t === !0 || Object.values(t).some(Boolean);
		}, e.getIsAllRowsExpanded = () => {
			let t = e.getState().expanded;
			return typeof t == "boolean" ? t === !0 : !(!Object.keys(t).length || e.getRowModel().flatRows.some((e) => !e.getIsExpanded()));
		}, e.getExpandedDepth = () => {
			let t = 0;
			return (e.getState().expanded === !0 ? Object.keys(e.getRowModel().rowsById) : Object.keys(e.getState().expanded)).forEach((e) => {
				let n = e.split(".");
				t = Math.max(t, n.length);
			}), t;
		}, e.getPreExpandedRowModel = () => e.getSortedRowModel(), e.getExpandedRowModel = () => (!e._getExpandedRowModel && e.options.getExpandedRowModel && (e._getExpandedRowModel = e.options.getExpandedRowModel(e)), e.options.manualExpanding || !e._getExpandedRowModel ? e.getPreExpandedRowModel() : e._getExpandedRowModel());
	},
	createRow: (e, t) => {
		e.toggleExpanded = (n) => {
			t.setExpanded((r) => {
				var i;
				let a = r === !0 || !!(r != null && r[e.id]), o = {};
				if (r === !0 ? Object.keys(t.getRowModel().rowsById).forEach((e) => {
					o[e] = !0;
				}) : o = r, n = (i = n) == null ? !a : i, !a && n) return {
					...o,
					[e.id]: !0
				};
				if (a && !n) {
					let { [e.id]: t, ...n } = o;
					return n;
				}
				return r;
			});
		}, e.getIsExpanded = () => {
			var n;
			let r = t.getState().expanded;
			return !!((n = t.options.getIsRowExpanded == null ? void 0 : t.options.getIsRowExpanded(e)) == null ? r === !0 || r != null && r[e.id] : n);
		}, e.getCanExpand = () => {
			var n, r, i;
			return (n = t.options.getRowCanExpand == null ? void 0 : t.options.getRowCanExpand(e)) == null ? ((r = t.options.enableExpanding) == null || r) && !!((i = e.subRows) != null && i.length) : n;
		}, e.getIsAllParentsExpanded = () => {
			let n = !0, r = e;
			for (; n && r.parentId;) r = t.getRow(r.parentId, !0), n = r.getIsExpanded();
			return n;
		}, e.getToggleExpandedHandler = () => {
			let t = e.getCanExpand();
			return () => {
				t && e.toggleExpanded();
			};
		};
	}
}, FF = 0, IF = 10, LF = () => ({
	pageIndex: FF,
	pageSize: IF
}), RF = {
	getInitialState: (e) => ({
		...e,
		pagination: {
			...LF(),
			...e == null ? void 0 : e.pagination
		}
	}),
	getDefaultOptions: (e) => ({ onPaginationChange: KP("pagination", e) }),
	createTable: (e) => {
		let t = !1, n = !1;
		e._autoResetPageIndex = () => {
			var r, i;
			if (!t) {
				e._queue(() => {
					t = !0;
				});
				return;
			}
			if ((r = (i = e.options.autoResetAll) == null ? e.options.autoResetPageIndex : i) == null ? !e.options.manualPagination : r) {
				if (n) return;
				n = !0, e._queue(() => {
					e.resetPageIndex(), n = !1;
				});
			}
		}, e.setPagination = (t) => e.options.onPaginationChange == null ? void 0 : e.options.onPaginationChange((e) => GP(t, e)), e.resetPagination = (t) => {
			var n;
			e.setPagination(t || (n = e.initialState.pagination) == null ? LF() : n);
		}, e.setPageIndex = (t) => {
			e.setPagination((n) => {
				let r = GP(t, n.pageIndex), i = e.options.pageCount === void 0 || e.options.pageCount === -1 ? 2 ** 53 - 1 : e.options.pageCount - 1;
				return r = Math.max(0, Math.min(r, i)), {
					...n,
					pageIndex: r
				};
			});
		}, e.resetPageIndex = (t) => {
			var n, r;
			e.setPageIndex(t || (n = (r = e.initialState) == null || (r = r.pagination) == null ? void 0 : r.pageIndex) == null ? FF : n);
		}, e.resetPageSize = (t) => {
			var n, r;
			e.setPageSize(t || (n = (r = e.initialState) == null || (r = r.pagination) == null ? void 0 : r.pageSize) == null ? IF : n);
		}, e.setPageSize = (t) => {
			e.setPagination((e) => {
				let n = Math.max(1, GP(t, e.pageSize)), r = e.pageSize * e.pageIndex, i = Math.floor(r / n);
				return {
					...e,
					pageIndex: i,
					pageSize: n
				};
			});
		}, e.setPageCount = (t) => e.setPagination((n) => {
			var r;
			let i = GP(t, (r = e.options.pageCount) == null ? -1 : r);
			return typeof i == "number" && (i = Math.max(-1, i)), {
				...n,
				pageCount: i
			};
		}), e.getPageOptions = Z(() => [e.getPageCount()], (e) => {
			let t = [];
			return e && e > 0 && (t = [...Array(e)].fill(null).map((e, t) => t)), t;
		}, Q(e.options, "debugTable", "getPageOptions")), e.getCanPreviousPage = () => e.getState().pagination.pageIndex > 0, e.getCanNextPage = () => {
			let { pageIndex: t } = e.getState().pagination, n = e.getPageCount();
			return n === -1 || n !== 0 && t < n - 1;
		}, e.previousPage = () => e.setPageIndex((e) => e - 1), e.nextPage = () => e.setPageIndex((e) => e + 1), e.firstPage = () => e.setPageIndex(0), e.lastPage = () => e.setPageIndex(e.getPageCount() - 1), e.getPrePaginationRowModel = () => e.getExpandedRowModel(), e.getPaginationRowModel = () => (!e._getPaginationRowModel && e.options.getPaginationRowModel && (e._getPaginationRowModel = e.options.getPaginationRowModel(e)), e.options.manualPagination || !e._getPaginationRowModel ? e.getPrePaginationRowModel() : e._getPaginationRowModel()), e.getPageCount = () => {
			var t;
			return (t = e.options.pageCount) == null ? Math.ceil(e.getRowCount() / e.getState().pagination.pageSize) : t;
		}, e.getRowCount = () => {
			var t;
			return (t = e.options.rowCount) == null ? e.getPrePaginationRowModel().rows.length : t;
		};
	}
}, zF = () => ({
	top: [],
	bottom: []
}), BF = {
	getInitialState: (e) => ({
		rowPinning: zF(),
		...e
	}),
	getDefaultOptions: (e) => ({ onRowPinningChange: KP("rowPinning", e) }),
	createRow: (e, t) => {
		e.pin = (n, r, i) => {
			let a = r ? e.getLeafRows().map((e) => {
				let { id: t } = e;
				return t;
			}) : [], o = i ? e.getParentRows().map((e) => {
				let { id: t } = e;
				return t;
			}) : [], s = /* @__PURE__ */ new Set([
				...o,
				e.id,
				...a
			]);
			t.setRowPinning((e) => {
				var t, r;
				if (n === "bottom") {
					var i, a;
					return {
						top: ((i = e == null ? void 0 : e.top) == null ? [] : i).filter((e) => !(s != null && s.has(e))),
						bottom: [...((a = e == null ? void 0 : e.bottom) == null ? [] : a).filter((e) => !(s != null && s.has(e))), ...Array.from(s)]
					};
				}
				if (n === "top") {
					var o, c;
					return {
						top: [...((o = e == null ? void 0 : e.top) == null ? [] : o).filter((e) => !(s != null && s.has(e))), ...Array.from(s)],
						bottom: ((c = e == null ? void 0 : e.bottom) == null ? [] : c).filter((e) => !(s != null && s.has(e)))
					};
				}
				return {
					top: ((t = e == null ? void 0 : e.top) == null ? [] : t).filter((e) => !(s != null && s.has(e))),
					bottom: ((r = e == null ? void 0 : e.bottom) == null ? [] : r).filter((e) => !(s != null && s.has(e)))
				};
			});
		}, e.getCanPin = () => {
			var n;
			let { enableRowPinning: r, enablePinning: i } = t.options;
			return typeof r == "function" ? r(e) : (n = r == null ? i : r) == null || n;
		}, e.getIsPinned = () => {
			let n = [e.id], { top: r, bottom: i } = t.getState().rowPinning, a = n.some((e) => r == null ? void 0 : r.includes(e)), o = n.some((e) => i == null ? void 0 : i.includes(e));
			return a ? "top" : o ? "bottom" : !1;
		}, e.getPinnedIndex = () => {
			var n, r;
			let i = e.getIsPinned();
			if (!i) return -1;
			let a = (n = i === "top" ? t.getTopRows() : t.getBottomRows()) == null ? void 0 : n.map((e) => {
				let { id: t } = e;
				return t;
			});
			return (r = a == null ? void 0 : a.indexOf(e.id)) == null ? -1 : r;
		};
	},
	createTable: (e) => {
		e.setRowPinning = (t) => e.options.onRowPinningChange == null ? void 0 : e.options.onRowPinningChange(t), e.resetRowPinning = (t) => {
			var n, r;
			return e.setRowPinning(t || (n = (r = e.initialState) == null ? void 0 : r.rowPinning) == null ? zF() : n);
		}, e.getIsSomeRowsPinned = (t) => {
			var n;
			let r = e.getState().rowPinning;
			if (!t) {
				var i, a;
				return !!((i = r.top) != null && i.length || (a = r.bottom) != null && a.length);
			}
			return !!((n = r[t]) != null && n.length);
		}, e._getPinnedRows = (t, n, r) => {
			var i;
			return ((i = e.options.keepPinnedRows) == null || i ? (n == null ? [] : n).map((t) => {
				let n = e.getRow(t, !0);
				return n.getIsAllParentsExpanded() ? n : null;
			}) : (n == null ? [] : n).map((e) => t.find((t) => t.id === e))).filter(Boolean).map((e) => ({
				...e,
				position: r
			}));
		}, e.getTopRows = Z(() => [e.getRowModel().rows, e.getState().rowPinning.top], (t, n) => e._getPinnedRows(t, n, "top"), Q(e.options, "debugRows", "getTopRows")), e.getBottomRows = Z(() => [e.getRowModel().rows, e.getState().rowPinning.bottom], (t, n) => e._getPinnedRows(t, n, "bottom"), Q(e.options, "debugRows", "getBottomRows")), e.getCenterRows = Z(() => [
			e.getRowModel().rows,
			e.getState().rowPinning.top,
			e.getState().rowPinning.bottom
		], (e, t, n) => {
			let r = /* @__PURE__ */ new Set([...t == null ? [] : t, ...n == null ? [] : n]);
			return e.filter((e) => !r.has(e.id));
		}, Q(e.options, "debugRows", "getCenterRows"));
	}
}, VF = {
	getInitialState: (e) => ({
		rowSelection: {},
		...e
	}),
	getDefaultOptions: (e) => ({
		onRowSelectionChange: KP("rowSelection", e),
		enableRowSelection: !0,
		enableMultiRowSelection: !0,
		enableSubRowSelection: !0
	}),
	createTable: (e) => {
		e.setRowSelection = (t) => e.options.onRowSelectionChange == null ? void 0 : e.options.onRowSelectionChange(t), e.resetRowSelection = (t) => {
			var n;
			return e.setRowSelection(t || (n = e.initialState.rowSelection) == null ? {} : n);
		}, e.toggleAllRowsSelected = (t) => {
			e.setRowSelection((n) => {
				t = t === void 0 ? !e.getIsAllRowsSelected() : t;
				let r = { ...n }, i = e.getPreGroupedRowModel().flatRows;
				return t ? i.forEach((e) => {
					e.getCanSelect() && (r[e.id] = !0);
				}) : i.forEach((e) => {
					delete r[e.id];
				}), r;
			});
		}, e.toggleAllPageRowsSelected = (t) => e.setRowSelection((n) => {
			let r = t === void 0 ? !e.getIsAllPageRowsSelected() : t, i = { ...n };
			return e.getRowModel().rows.forEach((t) => {
				HF(i, t.id, r, !0, e);
			}), i;
		}), e.getPreSelectedRowModel = () => e.getCoreRowModel(), e.getSelectedRowModel = Z(() => [e.getState().rowSelection, e.getCoreRowModel()], (t, n) => Object.keys(t).length ? UF(e, n) : {
			rows: [],
			flatRows: [],
			rowsById: {}
		}, Q(e.options, "debugTable", "getSelectedRowModel")), e.getFilteredSelectedRowModel = Z(() => [e.getState().rowSelection, e.getFilteredRowModel()], (t, n) => Object.keys(t).length ? UF(e, n) : {
			rows: [],
			flatRows: [],
			rowsById: {}
		}, Q(e.options, "debugTable", "getFilteredSelectedRowModel")), e.getGroupedSelectedRowModel = Z(() => [e.getState().rowSelection, e.getSortedRowModel()], (t, n) => Object.keys(t).length ? UF(e, n) : {
			rows: [],
			flatRows: [],
			rowsById: {}
		}, Q(e.options, "debugTable", "getGroupedSelectedRowModel")), e.getIsAllRowsSelected = () => {
			let t = e.getFilteredRowModel().flatRows, { rowSelection: n } = e.getState(), r = !!(t.length && Object.keys(n).length);
			return r && t.some((e) => e.getCanSelect() && !n[e.id]) && (r = !1), r;
		}, e.getIsAllPageRowsSelected = () => {
			let t = e.getPaginationRowModel().flatRows.filter((e) => e.getCanSelect()), { rowSelection: n } = e.getState(), r = !!t.length;
			return r && t.some((e) => !n[e.id]) && (r = !1), r;
		}, e.getIsSomeRowsSelected = () => {
			var t;
			let n = Object.keys((t = e.getState().rowSelection) == null ? {} : t).length;
			return n > 0 && n < e.getFilteredRowModel().flatRows.length;
		}, e.getIsSomePageRowsSelected = () => {
			let t = e.getPaginationRowModel().flatRows;
			return !e.getIsAllPageRowsSelected() && t.filter((e) => e.getCanSelect()).some((e) => e.getIsSelected() || e.getIsSomeSelected());
		}, e.getToggleAllRowsSelectedHandler = () => (t) => {
			e.toggleAllRowsSelected(t.target.checked);
		}, e.getToggleAllPageRowsSelectedHandler = () => (t) => {
			e.toggleAllPageRowsSelected(t.target.checked);
		};
	},
	createRow: (e, t) => {
		e.toggleSelected = (n, r) => {
			let i = e.getIsSelected();
			t.setRowSelection((a) => {
				var o;
				if (n = n === void 0 ? !i : n, e.getCanSelect() && i === n) return a;
				let s = { ...a };
				return HF(s, e.id, n, (o = r == null ? void 0 : r.selectChildren) == null || o, t), s;
			});
		}, e.getIsSelected = () => {
			let { rowSelection: n } = t.getState();
			return WF(e, n);
		}, e.getIsSomeSelected = () => {
			let { rowSelection: n } = t.getState();
			return GF(e, n) === "some";
		}, e.getIsAllSubRowsSelected = () => {
			let { rowSelection: n } = t.getState();
			return GF(e, n) === "all";
		}, e.getCanSelect = () => {
			var n;
			return typeof t.options.enableRowSelection == "function" ? t.options.enableRowSelection(e) : (n = t.options.enableRowSelection) == null || n;
		}, e.getCanSelectSubRows = () => {
			var n;
			return typeof t.options.enableSubRowSelection == "function" ? t.options.enableSubRowSelection(e) : (n = t.options.enableSubRowSelection) == null || n;
		}, e.getCanMultiSelect = () => {
			var n;
			return typeof t.options.enableMultiRowSelection == "function" ? t.options.enableMultiRowSelection(e) : (n = t.options.enableMultiRowSelection) == null || n;
		}, e.getToggleSelectedHandler = () => {
			let t = e.getCanSelect();
			return (n) => {
				var r;
				t && e.toggleSelected((r = n.target) == null ? void 0 : r.checked);
			};
		};
	}
}, HF = (e, t, n, r, i) => {
	var a;
	let o = i.getRow(t, !0);
	n ? (o.getCanMultiSelect() || Object.keys(e).forEach((t) => delete e[t]), o.getCanSelect() && (e[t] = !0)) : delete e[t], r && (a = o.subRows) != null && a.length && o.getCanSelectSubRows() && o.subRows.forEach((t) => HF(e, t.id, n, r, i));
};
function UF(e, t) {
	let n = e.getState().rowSelection, r = [], i = {}, a = function(e, t) {
		return e.map((e) => {
			var t;
			let o = WF(e, n);
			if (o && (r.push(e), i[e.id] = e), (t = e.subRows) != null && t.length && (e = {
				...e,
				subRows: a(e.subRows)
			}), o) return e;
		}).filter(Boolean);
	};
	return {
		rows: a(t.rows),
		flatRows: r,
		rowsById: i
	};
}
function WF(e, t) {
	var n;
	return (n = t[e.id]) != null && n;
}
function GF(e, t, n) {
	var r;
	if (!((r = e.subRows) != null && r.length)) return !1;
	let i = !0, a = !1;
	return e.subRows.forEach((e) => {
		if (!(a && !i) && (e.getCanSelect() && (WF(e, t) ? a = !0 : i = !1), e.subRows && e.subRows.length)) {
			let n = GF(e, t);
			n === "all" ? a = !0 : (n === "some" && (a = !0), i = !1);
		}
	}), i ? "all" : a ? "some" : !1;
}
var KF = /([0-9]+)/gm, qF = (e, t, n) => tI(eI(e.getValue(n)).toLowerCase(), eI(t.getValue(n)).toLowerCase()), JF = (e, t, n) => tI(eI(e.getValue(n)), eI(t.getValue(n))), YF = (e, t, n) => $F(eI(e.getValue(n)).toLowerCase(), eI(t.getValue(n)).toLowerCase()), XF = (e, t, n) => $F(eI(e.getValue(n)), eI(t.getValue(n))), ZF = (e, t, n) => {
	let r = e.getValue(n), i = t.getValue(n);
	return r > i ? 1 : r < i ? -1 : 0;
}, QF = (e, t, n) => $F(e.getValue(n), t.getValue(n));
function $F(e, t) {
	return e === t ? 0 : e > t ? 1 : -1;
}
function eI(e) {
	return typeof e == "number" ? isNaN(e) || e === Infinity || e === -Infinity ? "" : String(e) : typeof e == "string" ? e : "";
}
function tI(e, t) {
	let n = e.split(KF).filter(Boolean), r = t.split(KF).filter(Boolean);
	for (; n.length && r.length;) {
		let e = n.shift(), t = r.shift(), i = parseInt(e, 10), a = parseInt(t, 10), o = [i, a].sort();
		if (isNaN(o[0])) {
			if (e > t) return 1;
			if (t > e) return -1;
			continue;
		}
		if (isNaN(o[1])) return isNaN(i) ? -1 : 1;
		if (i > a) return 1;
		if (a > i) return -1;
	}
	return n.length - r.length;
}
var nI = {
	alphanumeric: qF,
	alphanumericCaseSensitive: JF,
	text: YF,
	textCaseSensitive: XF,
	datetime: ZF,
	basic: QF
}, rI = [
	eF,
	AF,
	bF,
	SF,
	rF,
	hF,
	MF,
	NF,
	{
		getInitialState: (e) => ({
			sorting: [],
			...e
		}),
		getDefaultColumnDef: () => ({
			sortingFn: "auto",
			sortUndefined: 1
		}),
		getDefaultOptions: (e) => ({
			onSortingChange: KP("sorting", e),
			isMultiSortEvent: (e) => e.shiftKey
		}),
		createColumn: (e, t) => {
			e.getAutoSortingFn = () => {
				let n = t.getFilteredRowModel().flatRows.slice(10), r = !1;
				for (let t of n) {
					let n = t == null ? void 0 : t.getValue(e.id);
					if (Object.prototype.toString.call(n) === "[object Date]") return nI.datetime;
					if (typeof n == "string" && (r = !0, n.split(KF).length > 1)) return nI.alphanumeric;
				}
				return r ? nI.text : nI.basic;
			}, e.getAutoSortDir = () => {
				let n = t.getFilteredRowModel().flatRows[0];
				return typeof (n == null ? void 0 : n.getValue(e.id)) == "string" ? "asc" : "desc";
			}, e.getSortingFn = () => {
				var n, r;
				if (!e) throw Error();
				return qP(e.columnDef.sortingFn) ? e.columnDef.sortingFn : e.columnDef.sortingFn === "auto" ? e.getAutoSortingFn() : (n = (r = t.options.sortingFns) == null ? void 0 : r[e.columnDef.sortingFn]) == null ? nI[e.columnDef.sortingFn] : n;
			}, e.toggleSorting = (n, r) => {
				let i = e.getNextSortingOrder(), a = n != null;
				t.setSorting((o) => {
					let s = o == null ? void 0 : o.find((t) => t.id === e.id), c = o == null ? void 0 : o.findIndex((t) => t.id === e.id), l = [], u, d = a ? n : i === "desc";
					if (u = o != null && o.length && e.getCanMultiSort() && r ? s ? "toggle" : "add" : o != null && o.length && c !== o.length - 1 ? "replace" : s ? "toggle" : "replace", u === "toggle" && (a || i || (u = "remove")), u === "add") {
						var f;
						l = [...o, {
							id: e.id,
							desc: d
						}], l.splice(0, l.length - ((f = t.options.maxMultiSortColCount) == null ? 2 ** 53 - 1 : f));
					} else l = u === "toggle" ? o.map((t) => t.id === e.id ? {
						...t,
						desc: d
					} : t) : u === "remove" ? o.filter((t) => t.id !== e.id) : [{
						id: e.id,
						desc: d
					}];
					return l;
				});
			}, e.getFirstSortDir = () => {
				var n, r;
				return ((n = (r = e.columnDef.sortDescFirst) == null ? t.options.sortDescFirst : r) == null ? e.getAutoSortDir() === "desc" : n) ? "desc" : "asc";
			}, e.getNextSortingOrder = (n) => {
				var r, i;
				let a = e.getFirstSortDir(), o = e.getIsSorted();
				return o ? o !== a && ((r = t.options.enableSortingRemoval) == null || r) && (!n || (i = t.options.enableMultiRemove) == null || i) ? !1 : o === "desc" ? "asc" : "desc" : a;
			}, e.getCanSort = () => {
				var n, r;
				return ((n = e.columnDef.enableSorting) == null || n) && ((r = t.options.enableSorting) == null || r) && !!e.accessorFn;
			}, e.getCanMultiSort = () => {
				var n, r;
				return (n = (r = e.columnDef.enableMultiSort) == null ? t.options.enableMultiSort : r) == null ? !!e.accessorFn : n;
			}, e.getIsSorted = () => {
				var n;
				let r = (n = t.getState().sorting) == null ? void 0 : n.find((t) => t.id === e.id);
				return r ? r.desc ? "desc" : "asc" : !1;
			}, e.getSortIndex = () => {
				var n, r;
				return (n = (r = t.getState().sorting) == null ? void 0 : r.findIndex((t) => t.id === e.id)) == null ? -1 : n;
			}, e.clearSorting = () => {
				t.setSorting((t) => t != null && t.length ? t.filter((t) => t.id !== e.id) : []);
			}, e.getToggleSortingHandler = () => {
				let n = e.getCanSort();
				return (r) => {
					n && (r.persist == null || r.persist(), e.toggleSorting == null || e.toggleSorting(void 0, e.getCanMultiSort() ? t.options.isMultiSortEvent == null ? void 0 : t.options.isMultiSortEvent(r) : !1));
				};
			};
		},
		createTable: (e) => {
			e.setSorting = (t) => e.options.onSortingChange == null ? void 0 : e.options.onSortingChange(t), e.resetSorting = (t) => {
				var n, r;
				e.setSorting(t || (n = (r = e.initialState) == null ? void 0 : r.sorting) == null ? [] : n);
			}, e.getPreSortedRowModel = () => e.getGroupedRowModel(), e.getSortedRowModel = () => (!e._getSortedRowModel && e.options.getSortedRowModel && (e._getSortedRowModel = e.options.getSortedRowModel(e)), e.options.manualSorting || !e._getSortedRowModel ? e.getPreSortedRowModel() : e._getSortedRowModel());
		}
	},
	vF,
	PF,
	RF,
	BF,
	VF,
	EF
];
function iI(e) {
	var t, n;
	let r = [...rI, ...(t = e._features) == null ? [] : t], i = { _features: r }, a = i._features.reduce((e, t) => Object.assign(e, t.getDefaultOptions == null ? void 0 : t.getDefaultOptions(i)), {}), o = (e) => i.options.mergeOptions ? i.options.mergeOptions(a, e) : {
		...a,
		...e
	}, s = { ...(n = e.initialState) == null ? {} : n };
	i._features.forEach((e) => {
		var t;
		s = (t = e.getInitialState == null ? void 0 : e.getInitialState(s)) == null ? s : t;
	});
	let c = [], l = !1, u = {
		_features: r,
		options: {
			...a,
			...e
		},
		initialState: s,
		_queue: (e) => {
			c.push(e), l || (l = !0, Promise.resolve().then(() => {
				for (; c.length;) c.shift()();
				l = !1;
			}).catch((e) => setTimeout(() => {
				throw e;
			})));
		},
		reset: () => {
			i.setState(i.initialState);
		},
		setOptions: (e) => {
			let t = GP(e, i.options);
			i.options = o(t);
		},
		getState: () => i.options.state,
		setState: (e) => {
			i.options.onStateChange == null || i.options.onStateChange(e);
		},
		_getRowId: (e, t, n) => {
			var r;
			return (r = i.options.getRowId == null ? void 0 : i.options.getRowId(e, t, n)) == null ? `${n ? [n.id, t].join(".") : t}` : r;
		},
		getCoreRowModel: () => (i._getCoreRowModel || (i._getCoreRowModel = i.options.getCoreRowModel(i)), i._getCoreRowModel()),
		getRowModel: () => i.getPaginationRowModel(),
		getRow: (e, t) => {
			let n = (t ? i.getPrePaginationRowModel() : i.getRowModel()).rowsById[e];
			if (!n && (n = i.getCoreRowModel().rowsById[e], !n)) throw Error();
			return n;
		},
		_getDefaultColumnDef: Z(() => [i.options.defaultColumn], (e) => {
			var t;
			return e = (t = e) == null ? {} : t, {
				header: (e) => {
					let t = e.header.column.columnDef;
					return t.accessorKey ? t.accessorKey : t.accessorFn ? t.id : null;
				},
				cell: (e) => {
					var t, n;
					return (t = (n = e.renderValue()) == null || n.toString == null ? void 0 : n.toString()) == null ? null : t;
				},
				...i._features.reduce((e, t) => Object.assign(e, t.getDefaultColumnDef == null ? void 0 : t.getDefaultColumnDef()), {}),
				...e
			};
		}, Q(e, "debugColumns", "_getDefaultColumnDef")),
		_getColumnDefs: () => i.options.columns,
		getAllColumns: Z(() => [i._getColumnDefs()], (e) => {
			let t = function(e, n, r) {
				return r === void 0 && (r = 0), e.map((e) => {
					let a = ZP(i, e, r, n), o = e;
					return a.columns = o.columns ? t(o.columns, a, r + 1) : [], a;
				});
			};
			return t(e);
		}, Q(e, "debugColumns", "getAllColumns")),
		getAllFlatColumns: Z(() => [i.getAllColumns()], (e) => e.flatMap((e) => e.getFlatColumns()), Q(e, "debugColumns", "getAllFlatColumns")),
		_getAllFlatColumnsById: Z(() => [i.getAllFlatColumns()], (e) => e.reduce((e, t) => (e[t.id] = t, e), {}), Q(e, "debugColumns", "getAllFlatColumnsById")),
		getAllLeafColumns: Z(() => [i.getAllColumns(), i._getOrderColumnsFn()], (e, t) => t(e.flatMap((e) => e.getLeafColumns())), Q(e, "debugColumns", "getAllLeafColumns")),
		getColumn: (e) => i._getAllFlatColumnsById()[e]
	};
	Object.assign(i, u);
	for (let e = 0; e < i._features.length; e++) {
		let t = i._features[e];
		t == null || t.createTable == null || t.createTable(i);
	}
	return i;
}
function aI() {
	return (e) => Z(() => [e.options.data], (t) => {
		let n = {
			rows: [],
			flatRows: [],
			rowsById: {}
		}, r = function(t, i, a) {
			i === void 0 && (i = 0);
			let o = [];
			for (let c = 0; c < t.length; c++) {
				let l = nF(e, e._getRowId(t[c], c, a), t[c], c, i, void 0, a == null ? void 0 : a.id);
				if (n.flatRows.push(l), n.rowsById[l.id] = l, o.push(l), e.options.getSubRows) {
					var s;
					l.originalSubRows = e.options.getSubRows(t[c], c), (s = l.originalSubRows) != null && s.length && (l.subRows = r(l.originalSubRows, i + 1, l));
				}
			}
			return o;
		};
		return n.rows = r(t), n;
	}, Q(e.options, "debugTable", "getRowModel", () => e._autoResetPageIndex()));
}
function oI() {
	return (e) => Z(() => [e.getState().sorting, e.getPreSortedRowModel()], (t, n) => {
		if (!n.rows.length || !(t != null && t.length)) return n;
		let r = e.getState().sorting, i = [], a = r.filter((t) => {
			var n;
			return (n = e.getColumn(t.id)) == null ? void 0 : n.getCanSort();
		}), o = {};
		a.forEach((t) => {
			let n = e.getColumn(t.id);
			n && (o[t.id] = {
				sortUndefined: n.columnDef.sortUndefined,
				invertSorting: n.columnDef.invertSorting,
				sortingFn: n.getSortingFn()
			});
		});
		let s = (e) => {
			let t = e.map((e) => ({ ...e }));
			return t.sort((e, t) => {
				for (let r = 0; r < a.length; r += 1) {
					var n;
					let i = a[r], s = o[i.id], c = s.sortUndefined, l = (n = i == null ? void 0 : i.desc) != null && n, u = 0;
					if (c) {
						let n = e.getValue(i.id), r = t.getValue(i.id), a = n === void 0, o = r === void 0;
						if (a || o) {
							if (c === "first") return a ? -1 : 1;
							if (c === "last") return a ? 1 : -1;
							u = a && o ? 0 : a ? c : -c;
						}
					}
					if (u === 0 && (u = s.sortingFn(e, t, i.id)), u !== 0) return l && (u *= -1), s.invertSorting && (u *= -1), u;
				}
				return e.index - t.index;
			}), t.forEach((e) => {
				var t;
				i.push(e), (t = e.subRows) != null && t.length && (e.subRows = s(e.subRows));
			}), t;
		};
		return {
			rows: s(n.rows),
			flatRows: i,
			rowsById: n.rowsById
		};
	}, Q(e.options, "debugTable", "getSortedRowModel", () => e._autoResetPageIndex()));
}
//#endregion
//#region node_modules/@tanstack/react-table/build/lib/index.mjs
function sI(e, t) {
	return e ? cI(e) ? /*#__PURE__*/ C.createElement(e, t) : e : null;
}
function cI(e) {
	return lI(e) || typeof e == "function" || uI(e);
}
function lI(e) {
	return typeof e == "function" && (() => {
		let t = Object.getPrototypeOf(e);
		return t.prototype && t.prototype.isReactComponent;
	})();
}
function uI(e) {
	return typeof e == "object" && typeof e.$$typeof == "symbol" && ["react.memo", "react.forward_ref"].includes(e.$$typeof.description);
}
function dI(e) {
	let t = {
		state: {},
		onStateChange: () => {},
		renderFallbackValue: null,
		...e
	}, [n] = C.useState(() => ({ current: iI(t) })), [r, i] = C.useState(() => n.current.initialState);
	return n.current.setOptions((t) => ({
		...t,
		...e,
		state: {
			...r,
			...e.state
		},
		onStateChange: (t) => {
			i(t), e.onStateChange == null || e.onStateChange(t);
		}
	})), n.current;
}
//#endregion
//#region src/ExecutiveQueue.tsx
var fI = "applylens:executive-queue-state", pI = "applylens:executive-queue-action", mI = "queueTableColumnWidths", hI = "preferences-secondary-action", gI = {
	status: "loading",
	rows: [],
	metaLabel: "Loading...",
	viewMode: "detailed",
	filters: {
		actions: [],
		preferenceIds: [],
		undecidedOnly: !1,
		limit: 15
	},
	preferenceOptions: [],
	pagination: {
		page: 1,
		pageSize: 15,
		totalCount: 0,
		totalPages: 1,
		hasPrevPage: !1,
		hasNextPage: !1
	}
}, _I = [
	{
		value: "APPLY",
		label: "Ready for review"
	},
	{
		value: "APPLY_REVIEW_VARIANTS",
		label: "Review resume choice"
	},
	{
		value: "MAYBE_TAILOR",
		label: "Tailor first"
	},
	{
		value: "SKIP_FOR_NOW",
		label: "Review later"
	}
], vI = "A packet is a review bundle for this job. It includes the job, selected resume, match signals, gaps, and tailoring guidance. It does not apply to the job.";
function yI(e) {
	window.dispatchEvent(new CustomEvent(pI, { detail: e }));
}
function $(e) {
	return String(e == null ? "" : e).trim();
}
function bI(e) {
	return {
		APPLY: "Ready for review",
		APPLY_REVIEW_VARIANTS: "Review resume choice",
		MAYBE_TAILOR: "Tailor first",
		SKIP_FOR_NOW: "Review later"
	}[$(e).toUpperCase()] || $(e) || "Unavailable";
}
function xI(e) {
	return {
		APPLY: "ready",
		APPLY_REVIEW_VARIANTS: "choice",
		MAYBE_TAILOR: "tailor",
		SKIP_FOR_NOW: "later"
	}[$(e).toUpperCase()] || "unavailable";
}
function SI(e) {
	let t = $(e).toLowerCase();
	return [
		"true",
		"1",
		"yes",
		"y",
		"on"
	].includes(t) ? "Packet ready" : [
		"false",
		"0",
		"no",
		"n",
		"off"
	].includes(t) ? "No packet" : "Unavailable";
}
function CI(e) {
	return {
		no_deterministic_winner: "No clear resume match",
		borderline_deterministic_score: "Borderline match",
		tailoring_signal: "Tailoring may improve fit",
		tailoring_likely_worthwhile: "Tailoring may improve fit",
		packet_generation_blocked: "Packet unavailable",
		deterministic_equivalent_variants: "Close resume match",
		fallback_only_no_deterministic_match: "No credible resume match"
	}[$(e).toLowerCase()] || $(e).replace(/_/g, " ");
}
function wI(e) {
	return {
		SELECT_RESUME: "Choose resume",
		MAYBE_TAILOR: "Tailor first",
		SKIP_FOR_NOW: "Review later",
		APPLY: "Ready for review",
		APPLY_REVIEW_VARIANTS: "Review resume choice"
	}[$(e.operator_decision).toUpperCase()] || {
		ready_to_apply: "Ready for review",
		tailor_then_apply: "Tailor then apply",
		review_before_action: "Review first",
		hold_or_skip: "Skip for now",
		source_watch: "Source watch"
	}[$(e.operator_review_lane).toLowerCase()] || "—";
}
function TI(e) {
	let t = $(e);
	return t ? t.replace(/\.pdf$/i, "").replace(/_/g, " ") : "—";
}
function EI(e) {
	if (e == null || $(e) === "") return null;
	let t = Number($(e).replace(/,/g, ""));
	return Number.isFinite(t) ? Math.abs(t) <= 1 ? t * 100 : t : null;
}
function DI(e, t) {
	let n = $(e);
	if (!n) return t === "unknown_timestamp_allowed" ? "Timestamp unavailable" : "—";
	let r = new Date(n);
	return Number.isNaN(r.getTime()) ? n : new Intl.DateTimeFormat(void 0, {
		month: "short",
		day: "numeric",
		year: "numeric"
	}).format(r);
}
function OI(e, t) {
	return $(e.job_doc_id) || `${$(e.queue_rank) || "row"}-${t}`;
}
function kI() {
	try {
		let e = JSON.parse(localStorage.getItem("queueTableColumnWidths") || "{}");
		return e && typeof e == "object" ? e : {};
	} catch (e) {
		return {};
	}
}
function AI({ label: e, options: t, values: n, onChange: r, placeholder: i, searchable: a = !1, allLabel: o }) {
	var s;
	let [c, l] = (0, C.useState)(!1), [u, d] = (0, C.useState)(""), f = (0, C.useRef)(null);
	(0, C.useEffect)(() => {
		let e = (e) => {
			var t;
			(t = f.current) != null && t.contains(e.target) || l(!1);
		};
		return document.addEventListener("mousedown", e), () => document.removeEventListener("mousedown", e);
	}, []);
	let p = u.trim().toLowerCase().replace(/[\/_-]+/g, " ").replace(/\s+/g, " "), m = t.filter((e) => e.label.toLowerCase().replace(/[\/_-]+/g, " ").replace(/\s+/g, " ").includes(p)), h = n.length === 0 ? i : n.length === 1 ? ((s = t.find((e) => e.value === n[0])) == null ? void 0 : s.label) || i : `${n.length} selected`;
	return /* @__PURE__ */ (0, X.jsxs)("div", {
		className: "executive-queue-multiselect",
		ref: f,
		children: [
			/* @__PURE__ */ (0, X.jsx)("span", {
				className: "executive-queue-field-label",
				children: e
			}),
			/* @__PURE__ */ (0, X.jsxs)("button", {
				type: "button",
				className: `${hI} executive-queue-select-trigger`,
				"aria-haspopup": "menu",
				"aria-expanded": c,
				onClick: () => l((e) => !e),
				children: [/* @__PURE__ */ (0, X.jsx)("span", { children: h }), /* @__PURE__ */ (0, X.jsx)(A, {
					size: 15,
					"aria-hidden": "true"
				})]
			}),
			c ? /* @__PURE__ */ (0, X.jsxs)("div", {
				className: "executive-queue-select-menu",
				role: "menu",
				children: [
					a ? /* @__PURE__ */ (0, X.jsxs)("label", {
						className: "executive-queue-select-search",
						children: [
							/* @__PURE__ */ (0, X.jsxs)("span", {
								className: "sr-only",
								children: ["Search ", e.toLowerCase()]
							}),
							/* @__PURE__ */ (0, X.jsx)(le, {
								size: 15,
								"aria-hidden": "true"
							}),
							/* @__PURE__ */ (0, X.jsx)("input", {
								type: "search",
								value: u,
								onChange: (e) => d(e.target.value),
								placeholder: `Search ${e.toLowerCase()}`
							})
						]
					}) : null,
					o && !p ? /* @__PURE__ */ (0, X.jsxs)("button", {
						type: "button",
						className: `${hI} executive-queue-select-option ${n.length === 0 ? "is-selected" : ""}`,
						role: "menuitemcheckbox",
						"aria-checked": n.length === 0,
						onClick: () => r([]),
						children: [/* @__PURE__ */ (0, X.jsx)(k, {
							size: 15,
							"aria-hidden": "true"
						}), /* @__PURE__ */ (0, X.jsx)("span", { children: o })]
					}) : null,
					m.map((e) => {
						let t = n.includes(e.value);
						return /* @__PURE__ */ (0, X.jsxs)("button", {
							type: "button",
							className: `${hI} executive-queue-select-option ${t ? "is-selected" : ""}`,
							role: "menuitemcheckbox",
							"aria-checked": t,
							onClick: () => r(t ? n.filter((t) => t !== e.value) : [...n, e.value]),
							children: [/* @__PURE__ */ (0, X.jsx)(k, {
								size: 15,
								"aria-hidden": "true"
							}), /* @__PURE__ */ (0, X.jsx)("span", { children: e.label })]
						}, e.value);
					}),
					m.length ? null : /* @__PURE__ */ (0, X.jsx)("div", {
						className: "executive-queue-select-empty",
						children: "No preferences found"
					})
				]
			}) : null
		]
	});
}
function jI({ state: e }) {
	let [t, n] = (0, C.useState)(e.filters);
	(0, C.useEffect)(() => n(e.filters), [e.filters]);
	let r = e.preferenceOptions.map((e) => ({
		value: e.role_family_id,
		label: e.display_name || e.role_family_id
	}));
	return /* @__PURE__ */ (0, X.jsxs)("section", {
		className: "executive-queue-filter-card",
		"aria-label": "Queue filters",
		children: [/* @__PURE__ */ (0, X.jsxs)("div", {
			className: "executive-queue-filter-grid",
			children: [
				/* @__PURE__ */ (0, X.jsx)(AI, {
					label: "Action",
					options: _I,
					values: t.actions,
					onChange: (e) => n((t) => ({
						...t,
						actions: e
					})),
					placeholder: "All actions"
				}),
				/* @__PURE__ */ (0, X.jsx)(AI, {
					label: "Preferences",
					options: r,
					values: t.preferenceIds,
					onChange: (e) => n((t) => ({
						...t,
						preferenceIds: e
					})),
					placeholder: "All Preferences",
					allLabel: "All Preferences",
					searchable: !0
				}),
				/* @__PURE__ */ (0, X.jsxs)("label", {
					className: "executive-queue-limit-field",
					children: [/* @__PURE__ */ (0, X.jsx)("span", {
						className: "executive-queue-field-label",
						children: "Limit"
					}), /* @__PURE__ */ (0, X.jsx)("input", {
						type: "number",
						min: 1,
						max: 200,
						value: t.limit,
						onChange: (e) => n((t) => ({
							...t,
							limit: Math.min(200, Math.max(1, Number(e.target.value) || 15))
						}))
					})]
				}),
				/* @__PURE__ */ (0, X.jsxs)("fieldset", {
					className: "executive-queue-undecided-field",
					children: [/* @__PURE__ */ (0, X.jsxs)("legend", { children: ["Undecided only", /* @__PURE__ */ (0, X.jsx)("span", {
						title: "Shows only browse rows without an operator decision.",
						children: /* @__PURE__ */ (0, X.jsx)(ne, {
							size: 14,
							"aria-label": "Shows only browse rows without an operator decision."
						})
					})] }), /* @__PURE__ */ (0, X.jsxs)("div", {
						className: "executive-queue-segmented",
						children: [/* @__PURE__ */ (0, X.jsx)("button", {
							type: "button",
							className: `${hI} ${t.undecidedOnly ? "" : "is-active"}`,
							"aria-pressed": !t.undecidedOnly,
							onClick: () => n((e) => ({
								...e,
								undecidedOnly: !1
							})),
							children: "No"
						}), /* @__PURE__ */ (0, X.jsx)("button", {
							type: "button",
							className: `${hI} ${t.undecidedOnly ? "is-active" : ""}`,
							"aria-pressed": t.undecidedOnly,
							onClick: () => n((e) => ({
								...e,
								undecidedOnly: !0
							})),
							children: "Yes"
						})]
					})]
				})
			]
		}), /* @__PURE__ */ (0, X.jsxs)("div", {
			className: "executive-queue-filter-actions",
			children: [/* @__PURE__ */ (0, X.jsxs)("button", {
				type: "button",
				className: `${hI} executive-queue-clear-btn`,
				onClick: () => yI({ type: "clear_filters" }),
				children: [/* @__PURE__ */ (0, X.jsx)(se, {
					size: 15,
					"aria-hidden": "true"
				}), " Clear"]
			}), /* @__PURE__ */ (0, X.jsx)("button", {
				type: "button",
				className: "executive-queue-apply-btn",
				onClick: () => yI({
					type: "apply_filters",
					filters: t
				}),
				children: "Apply Filters"
			})]
		})]
	});
}
function MI({ value: e }) {
	let t = EI(e);
	if (t === null) return /* @__PURE__ */ (0, X.jsx)("span", {
		className: "executive-queue-muted",
		children: "—"
	});
	let n = Math.max(0, Math.min(100, t));
	return /* @__PURE__ */ (0, X.jsxs)("div", {
		className: "executive-queue-match",
		"aria-label": `Match score ${t.toFixed(2)}`,
		children: [/* @__PURE__ */ (0, X.jsx)("span", { children: t.toFixed(2) }), /* @__PURE__ */ (0, X.jsx)("span", {
			className: "executive-queue-match-track",
			"aria-hidden": "true",
			children: /* @__PURE__ */ (0, X.jsx)("span", { style: { width: `${n}%` } })
		})]
	});
}
function NI({ row: e }) {
	return /* @__PURE__ */ (0, X.jsxs)("div", {
		className: "executive-queue-details executive-queue-details--neutral",
		children: [
			/* @__PURE__ */ (0, X.jsxs)("div", { children: [/* @__PURE__ */ (0, X.jsx)("span", { children: "Priority reason" }), /* @__PURE__ */ (0, X.jsx)("strong", { children: CI(e.queue_priority_reason) || "—" })] }),
			/* @__PURE__ */ (0, X.jsxs)("div", { children: [/* @__PURE__ */ (0, X.jsx)("span", { children: "Next step" }), /* @__PURE__ */ (0, X.jsx)("strong", { children: wI(e) })] }),
			/* @__PURE__ */ (0, X.jsxs)("div", { children: [/* @__PURE__ */ (0, X.jsx)("span", { children: "Selected resume" }), /* @__PURE__ */ (0, X.jsx)("strong", { children: TI(e.operator_selected_resume || e.winner_resume) })] }),
			/* @__PURE__ */ (0, X.jsxs)("div", { children: [/* @__PURE__ */ (0, X.jsx)("span", { children: "Runner-up" }), /* @__PURE__ */ (0, X.jsx)("strong", { children: TI(e.runner_up_resume) })] }),
			/* @__PURE__ */ (0, X.jsxs)("div", { children: [/* @__PURE__ */ (0, X.jsx)("span", { children: "Score gap" }), /* @__PURE__ */ (0, X.jsx)("strong", { children: $(e.score_gap) || "—" })] }),
			/* @__PURE__ */ (0, X.jsxs)("div", { children: [/* @__PURE__ */ (0, X.jsx)("span", { children: "Missing requirements" }), /* @__PURE__ */ (0, X.jsx)("strong", { children: $(e.missing_requirement_count) || "0" })] }),
			/* @__PURE__ */ (0, X.jsxs)("p", { children: [
				/* @__PURE__ */ (0, X.jsx)(ne, {
					size: 14,
					"aria-hidden": "true"
				}),
				" ",
				vI
			] })
		]
	});
}
function PI(e) {
	let t = {
		id: "expand",
		header: "",
		size: 42,
		minSize: 42,
		maxSize: 42,
		enableSorting: !1,
		enableResizing: !1,
		cell: ({ row: e }) => /* @__PURE__ */ (0, X.jsx)("button", {
			type: "button",
			className: `${hI} executive-queue-expand-btn`,
			"aria-label": `${e.getIsExpanded() ? "Collapse" : "Expand"} details for ${$(e.original.job_title) || "job"}`,
			"aria-expanded": e.getIsExpanded(),
			onClick: e.getToggleExpandedHandler(),
			children: e.getIsExpanded() ? /* @__PURE__ */ (0, X.jsx)(A, {
				size: 15,
				"aria-hidden": "true"
			}) : /* @__PURE__ */ (0, X.jsx)(j, {
				size: 15,
				"aria-hidden": "true"
			})
		})
	}, n = {
		id: "review",
		header: "Review",
		size: 128,
		minSize: 128,
		maxSize: 128,
		enableSorting: !1,
		enableResizing: !1,
		cell: ({ row: e }) => /* @__PURE__ */ (0, X.jsx)("button", {
			type: "button",
			className: "executive-queue-review-btn",
			disabled: !!e.original.is_applied,
			"aria-label": `Review ${$(e.original.job_title) || "job"}`,
			onClick: () => yI({
				type: "review",
				row: e.original
			}),
			children: e.original.is_applied ? "Reviewed" : "Review"
		})
	};
	return [
		t,
		{
			accessorKey: "queue_rank",
			header: "Rank",
			size: 86,
			minSize: 72,
			sortingFn: "basic"
		},
		{
			id: "job_title",
			header: e === "simple" ? "Job title / company" : "Job title",
			size: e === "simple" ? 300 : 250,
			minSize: 210,
			accessorFn: (e) => `${$(e.job_title)} ${$(e.job_company)}`,
			cell: ({ row: t }) => /* @__PURE__ */ (0, X.jsxs)("div", {
				className: "executive-queue-job-cell",
				children: [
					/* @__PURE__ */ (0, X.jsx)("a", {
						href: $(t.original.job_url || t.original.job_doc_id) || void 0,
						target: "_blank",
						rel: "noreferrer",
						children: $(t.original.job_title) || "Untitled job"
					}),
					e === "simple" ? /* @__PURE__ */ (0, X.jsx)("span", { children: $(t.original.job_company) || "—" }) : null,
					/* @__PURE__ */ (0, X.jsx)("small", { children: $(t.original.job_location) || "Location unavailable" })
				]
			})
		},
		...e === "detailed" ? [{
			accessorKey: "job_company",
			header: "Company",
			size: 170,
			minSize: 130
		}, {
			accessorKey: "job_location",
			header: "Location",
			size: 170,
			minSize: 130
		}] : [],
		{
			id: "posted_at",
			header: "Posted at",
			size: 142,
			minSize: 120,
			accessorFn: (e) => e.posted_at ? new Date(e.posted_at).getTime() : null,
			sortUndefined: "last",
			cell: ({ row: e }) => DI(e.original.posted_at, e.original.freshness_status)
		},
		{
			id: "recommendation",
			header: "Recommendation",
			size: 180,
			minSize: 150,
			accessorFn: (e) => bI(e.action),
			cell: ({ row: e }) => /* @__PURE__ */ (0, X.jsx)("span", {
				className: `executive-queue-badge executive-queue-badge--${xI(e.original.action)}`,
				children: bI(e.original.action)
			})
		},
		{
			id: "packet_status",
			header: () => /* @__PURE__ */ (0, X.jsxs)("span", {
				className: "executive-queue-packet-head",
				children: ["Packet ", /* @__PURE__ */ (0, X.jsx)(ne, {
					size: 13,
					"aria-label": vI
				})]
			}),
			size: 138,
			minSize: 120,
			accessorFn: (e) => SI(e.packet_generation_allowed),
			cell: ({ row: e }) => /* @__PURE__ */ (0, X.jsx)("span", {
				className: `executive-queue-badge executive-queue-badge--packet ${SI(e.original.packet_generation_allowed) === "Packet ready" ? "is-ready" : ""}`,
				children: SI(e.original.packet_generation_allowed)
			})
		},
		{
			id: "winner_score",
			header: "Match",
			size: 132,
			minSize: 112,
			accessorFn: (e) => EI(e.winner_score),
			sortUndefined: "last",
			cell: ({ row: e }) => /* @__PURE__ */ (0, X.jsx)(MI, { value: e.original.winner_score })
		},
		{
			id: "selected_resume",
			header: "Selected Resume",
			size: 240,
			minSize: 220,
			accessorFn: (e) => $(e.operator_selected_resume || e.winner_resume),
			cell: ({ row: e }) => /* @__PURE__ */ (0, X.jsx)("span", {
				className: "executive-queue-selected-resume-value",
				title: $(e.original.operator_selected_resume || e.original.winner_resume),
				children: TI(e.original.operator_selected_resume || e.original.winner_resume)
			})
		},
		...e === "detailed" ? [
			{
				id: "runner_up_resume",
				header: "Runner-up resume",
				size: 210,
				minSize: 170,
				accessorFn: (e) => $(e.runner_up_resume),
				cell: ({ row: e }) => /* @__PURE__ */ (0, X.jsx)("span", {
					title: $(e.original.runner_up_resume),
					children: TI(e.original.runner_up_resume)
				})
			},
			{
				accessorKey: "score_gap",
				header: "Score gap",
				size: 108,
				minSize: 94,
				sortUndefined: "last"
			},
			{
				accessorKey: "missing_requirement_count",
				header: "Missing req count",
				size: 138,
				minSize: 120,
				sortUndefined: "last"
			},
			{
				id: "next_step",
				header: "Next step",
				size: 160,
				minSize: 130,
				accessorFn: (e) => wI(e)
			},
			{
				id: "queue_priority_reason",
				header: "Priority reason",
				size: 180,
				minSize: 150,
				accessorFn: (e) => CI(e.queue_priority_reason) || "—"
			}
		] : [],
		n
	];
}
function FI({ state: e }) {
	let { page: t, pageSize: n, totalCount: r, totalPages: i, hasPrevPage: a, hasNextPage: o } = e.pagination, s = r ? (t - 1) * n + 1 : 0, c = r ? Math.min(s + e.rows.length - 1, r) : 0;
	return /* @__PURE__ */ (0, X.jsxs)("div", {
		className: "executive-queue-pagination",
		children: [/* @__PURE__ */ (0, X.jsx)("span", { children: r ? `Showing ${s}-${c} of ${r} jobs` : "0 jobs" }), /* @__PURE__ */ (0, X.jsxs)("div", { children: [
			/* @__PURE__ */ (0, X.jsx)("button", {
				type: "button",
				className: hI,
				disabled: !a,
				"aria-label": "Previous queue page",
				onClick: () => yI({
					type: "page_change",
					page: t - 1
				}),
				children: "Previous"
			}),
			/* @__PURE__ */ (0, X.jsxs)("span", {
				"aria-current": "page",
				children: [
					t,
					" / ",
					Math.max(i, 1)
				]
			}),
			/* @__PURE__ */ (0, X.jsx)("button", {
				type: "button",
				className: hI,
				disabled: !o,
				"aria-label": "Next queue page",
				onClick: () => yI({
					type: "page_change",
					page: t + 1
				}),
				children: "Next"
			})
		] })]
	});
}
function II({ state: e }) {
	let [t, n] = (0, C.useState)([]), [r, i] = (0, C.useState)(kI), [a, o] = (0, C.useState)(""), s = (0, C.useMemo)(() => PI(e.viewMode), [e.viewMode]), c = dI({
		data: (0, C.useMemo)(() => e.rows.slice(), [e.rows]),
		columns: s,
		state: {
			sorting: t,
			columnSizing: r,
			expanded: a ? { [a]: !0 } : {}
		},
		getRowId: (e, t) => OI(e, t),
		onSortingChange: n,
		onColumnSizingChange: (e) => {
			i((t) => {
				let n = typeof e == "function" ? e(t) : e;
				return localStorage.setItem(mI, JSON.stringify(n)), n;
			});
		},
		onExpandedChange: (e) => {
			let t = a ? { [a]: !0 } : {}, n = typeof e == "function" ? e(t) : e, r = n === !0 ? t : n, i = Object.keys(r).find((e) => r[e] && !t[e]);
			o(i || Object.keys(r).find((e) => r[e]) || "");
		},
		getRowCanExpand: () => !0,
		getCoreRowModel: aI(),
		getSortedRowModel: oI(),
		enableSortingRemoval: !1,
		columnResizeMode: "onChange"
	});
	return /* @__PURE__ */ (0, X.jsxs)("section", {
		className: `executive-queue-table-card executive-queue-table-card--${e.viewMode}`,
		"aria-label": "Executive queue table",
		children: [
			/* @__PURE__ */ (0, X.jsxs)("header", {
				className: "executive-queue-table-header",
				children: [/* @__PURE__ */ (0, X.jsxs)("div", { children: [/* @__PURE__ */ (0, X.jsxs)("div", {
					className: "executive-queue-title-line",
					children: [/* @__PURE__ */ (0, X.jsx)("h2", { children: "Queue Table" }), /* @__PURE__ */ (0, X.jsx)("span", { children: e.pagination.totalCount })]
				}), /* @__PURE__ */ (0, X.jsx)("p", { children: e.metaLabel })] }), /* @__PURE__ */ (0, X.jsx)("div", {
					className: "executive-queue-view-toggle",
					role: "radiogroup",
					"aria-label": "Executive view mode",
					children: ["detailed", "simple"].map((t) => /* @__PURE__ */ (0, X.jsx)("button", {
						type: "button",
						role: "radio",
						"aria-checked": e.viewMode === t,
						className: `${hI} ${e.viewMode === t ? "is-active" : ""}`,
						onClick: () => yI({
							type: "view_mode_change",
							viewMode: t
						}),
						children: t === "detailed" ? "Detailed" : "Simple"
					}, t))
				})]
			}),
			e.status === "error" ? /* @__PURE__ */ (0, X.jsxs)("div", {
				className: "executive-queue-error",
				role: "alert",
				children: [
					/* @__PURE__ */ (0, X.jsx)(N, {
						size: 20,
						"aria-hidden": "true"
					}),
					/* @__PURE__ */ (0, X.jsxs)("div", { children: [/* @__PURE__ */ (0, X.jsx)("strong", { children: "Queue data is unavailable" }), /* @__PURE__ */ (0, X.jsx)("span", { children: e.message || "Try the request again." })] }),
					/* @__PURE__ */ (0, X.jsx)("button", {
						type: "button",
						className: hI,
						onClick: () => yI({ type: "retry" }),
						children: "Retry"
					})
				]
			}) : /* @__PURE__ */ (0, X.jsx)("div", {
				className: "executive-queue-table-viewport",
				"aria-busy": e.status === "loading",
				children: /* @__PURE__ */ (0, X.jsxs)("table", {
					style: { width: c.getTotalSize() },
					children: [/* @__PURE__ */ (0, X.jsx)("thead", { children: c.getHeaderGroups().map((e) => /* @__PURE__ */ (0, X.jsx)("tr", { children: e.headers.map((e) => {
						let t = e.column.getIsSorted();
						return /* @__PURE__ */ (0, X.jsxs)("th", {
							style: { width: e.getSize() },
							className: `executive-queue-column--${e.column.id} ${e.column.id === "review" ? "is-sticky-action" : ""} ${t ? "is-sorted" : ""}`.trim(),
							"aria-sort": t === "asc" ? "ascending" : t === "desc" ? "descending" : e.column.getCanSort() ? "none" : void 0,
							children: [e.isPlaceholder ? null : e.column.getCanSort() ? /* @__PURE__ */ (0, X.jsxs)("button", {
								type: "button",
								className: `${hI} executive-queue-sort-btn ${t ? "is-sorted" : ""}`,
								onClick: e.column.getToggleSortingHandler(),
								children: [sI(e.column.columnDef.header, e.getContext()), t === "asc" ? /* @__PURE__ */ (0, X.jsx)(M, { size: 14 }) : t === "desc" ? /* @__PURE__ */ (0, X.jsx)(A, { size: 14 }) : /* @__PURE__ */ (0, X.jsx)("span", { className: "executive-queue-sort-placeholder" })]
							}) : sI(e.column.columnDef.header, e.getContext()), e.column.getCanResize() ? /* @__PURE__ */ (0, X.jsx)("span", {
								className: `executive-queue-resize-handle ${e.column.getIsResizing() ? "is-resizing" : ""}`,
								onMouseDown: e.getResizeHandler(),
								onTouchStart: e.getResizeHandler(),
								role: "separator",
								"aria-orientation": "vertical",
								"aria-label": `Resize ${$(e.column.columnDef.header) || e.column.id} column`
							}) : null]
						}, e.id);
					}) }, e.id)) }), /* @__PURE__ */ (0, X.jsx)("tbody", { children: e.status === "loading" ? Array.from({ length: 5 }, (e, t) => /* @__PURE__ */ (0, X.jsx)("tr", {
						className: "executive-queue-skeleton-row",
						children: /* @__PURE__ */ (0, X.jsx)("td", {
							colSpan: s.length,
							children: /* @__PURE__ */ (0, X.jsx)("span", {})
						})
					}, `skeleton-${t}`)) : c.getRowModel().rows.length ? c.getRowModel().rows.flatMap((e) => [/* @__PURE__ */ (0, X.jsx)("tr", {
						className: `executive-queue-row ${e.getIsExpanded() ? "is-expanded" : ""}`.trim(),
						children: e.getVisibleCells().map((e) => /* @__PURE__ */ (0, X.jsx)("td", {
							style: { width: e.column.getSize() },
							className: `executive-queue-column--${e.column.id} ${e.column.id === "review" ? "is-sticky-action" : ""}`.trim(),
							children: sI(e.column.columnDef.cell, e.getContext())
						}, e.id))
					}, e.id), e.getIsExpanded() ? /* @__PURE__ */ (0, X.jsx)("tr", {
						className: "executive-queue-detail-row",
						children: /* @__PURE__ */ (0, X.jsx)("td", {
							colSpan: e.getVisibleCells().length,
							children: /* @__PURE__ */ (0, X.jsx)(NI, { row: e.original })
						})
					}, `${e.id}-details`) : null]) : /* @__PURE__ */ (0, X.jsx)("tr", { children: /* @__PURE__ */ (0, X.jsx)("td", {
						colSpan: s.length,
						children: /* @__PURE__ */ (0, X.jsxs)("div", {
							className: "executive-queue-empty",
							children: [
								/* @__PURE__ */ (0, X.jsx)("strong", { children: "No jobs match these filters" }),
								/* @__PURE__ */ (0, X.jsx)("span", { children: "Clear filters to return to the complete Executive queue." }),
								/* @__PURE__ */ (0, X.jsx)("button", {
									type: "button",
									className: hI,
									onClick: () => yI({ type: "clear_filters" }),
									children: "Clear Filters"
								})
							]
						})
					}) }) })]
				})
			}),
			/* @__PURE__ */ (0, X.jsx)(FI, { state: e })
		]
	});
}
function LI({ state: e }) {
	return /* @__PURE__ */ (0, X.jsxs)("div", {
		className: `executive-queue-dashboard executive-queue-dashboard--${e.viewMode}`,
		children: [/* @__PURE__ */ (0, X.jsx)(jI, { state: e }), /* @__PURE__ */ (0, X.jsx)(II, { state: e })]
	});
}
//#endregion
//#region src/pipeline/pipelineModel.ts
var RI = 2e3;
RI * 15;
var zI = [
	"startup",
	"scraping",
	"filtering",
	"dedupe",
	"ranking",
	"cache_filter",
	"details",
	"intelligence",
	"ai_evaluation_filter",
	"embedding_prefilter",
	"ai_evaluation",
	"resume_matching",
	"application_priority",
	"rag_export",
	"planning",
	"finalization"
], BI = {
	startup: "Startup",
	scraping: "Scraping",
	filtering: "Filtering",
	dedupe: "Deduplication",
	ranking: "Ranking",
	cache_filter: "Cache Filter",
	details: "Details",
	intelligence: "Intelligence",
	ai_evaluation_filter: "AI Evaluation Filter",
	embedding_prefilter: "Embedding Prefilter",
	ai_evaluation: "AI Evaluation",
	resume_matching: "Resume Matching",
	application_priority: "Application Priority",
	rag_export: "RAG Export",
	planning: "Planning",
	finalization: "Finalization"
}, VI = [
	{
		label: "Collection",
		keys: [
			["scraped_jobs", "Scraped"],
			["filtered_jobs", "Filtered"],
			["new_jobs", "New"]
		]
	},
	{
		label: "Relevance and deduplication",
		keys: [
			["deduped_jobs", "Deduplicated"],
			["ranked_jobs", "Ranked"],
			["detailed_jobs", "Detailed"]
		]
	},
	{
		label: "Intelligence and evaluation",
		keys: [
			["intelligent_jobs", "Intelligence"],
			["evaluable_jobs", "AI Eligible"],
			["prefilter_jobs", "Prefilter"],
			["ai_jobs", "AI Evaluated"]
		]
	},
	{
		label: "Resume matching and planning",
		keys: [
			["resume_matched_jobs", "Resume Matched"],
			["scored_jobs", "Scored"],
			["rag_export_count", "RAG Exported"],
			["planning_packets_total", "Planning Packets"],
			["planning_packets_completed", "Packets Completed"]
		]
	},
	{
		label: "Final output",
		keys: [["final_jobs", "Final Jobs"]]
	}
], HI = [
	["scraped_jobs", "Collected"],
	["filtered_jobs", "Filtered"],
	["deduped_jobs", "Deduplicated"],
	["ranked_jobs", "Ranked"],
	["ai_jobs", "Evaluated"],
	["resume_matched_jobs", "Resume matched"],
	["final_jobs", "Final"]
];
function UI(e) {
	let t = String(e || "idle").trim().toLowerCase();
	return t === "idle" ? "idle" : t === "queued" || t === "starting" ? "starting" : t === "running" ? "running" : t === "succeeded" ? "succeeded" : [
		"failed",
		"cancelled",
		"canceled",
		"stopped"
	].includes(t) ? "failed" : "unavailable";
}
function WI(e) {
	let t = Array.isArray(e.stage_order) ? e.stage_order.filter((e) => typeof e == "string" && e.length > 0) : [];
	return t.length ? t : [...zI];
}
function GI(e) {
	if (e === "" || e == null || typeof e == "boolean") return null;
	let t = typeof e == "number" ? e : Number(e);
	return Number.isFinite(t) && t >= 0 ? t : null;
}
function KI(e) {
	return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(e);
}
function qI(e) {
	if (!e) return "";
	let t = new Date(String(e));
	return Number.isNaN(t.getTime()) ? "" : new Intl.DateTimeFormat("en-US", {
		month: "short",
		day: "numeric",
		hour: "numeric",
		minute: "2-digit"
	}).format(t);
}
function JI(e, t, n = Date.now()) {
	let r = new Date(String(e || ""));
	if (Number.isNaN(r.getTime())) return "";
	let i = t ? new Date(String(t)) : null, a = i && !Number.isNaN(i.getTime()) ? i.getTime() : n, o = Math.max(0, Math.floor((a - r.getTime()) / 1e3)), s = Math.floor(o / 3600), c = Math.floor(o % 3600 / 60), l = o % 60;
	return s ? `${s}h ${c}m` : c ? `${c}m ${l}s` : `${l}s`;
}
function YI(e) {
	return String(e.updated_at_utc || e.updated_at || "").trim();
}
function XI(e, t = Date.now()) {
	if (UI(e.status) !== "running") return !1;
	let n = YI(e);
	if (!n) return !1;
	let r = new Date(n);
	return !Number.isNaN(r.getTime()) && t - r.getTime() > 3e4;
}
//#endregion
//#region src/pipeline/PipelineDashboard.tsx
var ZI = "applylens:pipeline-run-accepted", QI = "applylens_pipeline_accepted_run_id", $I = [
	["job_limit", "Job limit"],
	["job_packet_limit", "Packet limit"],
	["planning_only", "Planning only"],
	["generate_tailoring", "Generate tailoring"],
	["generate_llm_tailoring", "AI tailoring"],
	["refresh_llm_tailoring", "Refresh AI cache"],
	["generate_llm_fallback", "Backup ranking"],
	["generate_llm_adjudication", "AI review"],
	["delete_seen_data", "Rerun seen jobs"]
];
function eL(e) {
	return BI[e] || e.replace(/_/g, " ").replace(/\b\w/g, (e) => e.toUpperCase());
}
function tL(e) {
	return e === "unavailable" ? "Unavailable" : e.charAt(0).toUpperCase() + e.slice(1);
}
function nL(e, t, n) {
	return new Set(Array.isArray(e.completed_stages) ? e.completed_stages : []).has(t) ? "complete" : t === e.current_stage && n === "failed" ? "failed" : t === e.current_stage && (n === "running" || n === "starting") ? "active" : "pending";
}
function rL(e) {
	if (typeof e == "boolean") return e ? "Enabled" : "Disabled";
	if (typeof e == "number" && Number.isFinite(e)) return KI(e);
	if (typeof e == "string") {
		let t = e.trim();
		return t ? t.toLowerCase() === "yes" ? "Enabled" : t.toLowerCase() === "no" ? "Disabled" : t : "";
	}
	return "";
}
async function iL() {
	let e = await fetch("/pipeline/status", {
		method: "GET",
		credentials: "same-origin",
		headers: { Accept: "application/json" }
	});
	if (!e.ok) throw Error(`Pipeline status request failed (${e.status})`);
	return e.json();
}
function aL() {
	if (typeof window.openApplyLensPipelineConfig == "function") {
		window.openApplyLensPipelineConfig();
		return;
	}
	console.error("The reviewed Pipeline launch flow is unavailable on this page.");
}
function oL() {
	try {
		return String(window.sessionStorage.getItem("applylens_pipeline_accepted_run_id") || "").trim();
	} catch (e) {
		return "";
	}
}
function sL(e) {
	try {
		window.sessionStorage.getItem("applylens_pipeline_accepted_run_id") === e && window.sessionStorage.removeItem(QI);
	} catch (e) {}
}
function cL(e, t = {}) {
	return { pipeline: {
		...t,
		status: t.status || "starting",
		run_id: e || t.run_id,
		current_stage: t.current_stage || "startup",
		stage_message: t.stage_message || "Synchronizing the accepted pipeline run."
	} };
}
function lL() {
	return /* @__PURE__ */ (0, X.jsxs)("div", {
		className: "pipeline-dashboard pipeline-dashboard--loading",
		"aria-busy": "true",
		"aria-label": "Loading pipeline status",
		children: [
			/* @__PURE__ */ (0, X.jsx)("div", { className: "pipeline-dashboard-skeleton pipeline-dashboard-skeleton--header" }),
			/* @__PURE__ */ (0, X.jsxs)("div", {
				className: "pipeline-dashboard-top-grid",
				children: [/* @__PURE__ */ (0, X.jsx)("div", { className: "pipeline-dashboard-skeleton pipeline-dashboard-skeleton--summary" }), /* @__PURE__ */ (0, X.jsx)("div", { className: "pipeline-dashboard-skeleton pipeline-dashboard-skeleton--stage" })]
			}),
			/* @__PURE__ */ (0, X.jsx)("div", { className: "pipeline-dashboard-skeleton pipeline-dashboard-skeleton--counts" })
		]
	});
}
function uL({ onRefresh: e, onRun: t, refreshing: n, runActive: r }) {
	return /* @__PURE__ */ (0, X.jsxs)("header", {
		className: "pipeline-dashboard-header",
		children: [/* @__PURE__ */ (0, X.jsxs)("div", { children: [
			/* @__PURE__ */ (0, X.jsx)("p", {
				className: "pipeline-dashboard-eyebrow",
				children: "Operations"
			}),
			/* @__PURE__ */ (0, X.jsx)("h1", { children: "Pipeline" }),
			/* @__PURE__ */ (0, X.jsx)("p", { children: "Monitor job collection, filtering, evaluation, resume matching, and planning." })
		] }), /* @__PURE__ */ (0, X.jsxs)("div", {
			className: "pipeline-dashboard-actions",
			children: [/* @__PURE__ */ (0, X.jsxs)("button", {
				className: "pipeline-dashboard-btn pipeline-dashboard-btn--secondary",
				type: "button",
				onClick: e,
				disabled: n,
				children: [/* @__PURE__ */ (0, X.jsx)(oe, {
					size: 17,
					"aria-hidden": "true"
				}), n ? "Refreshing" : "Refresh Status"]
			}), /* @__PURE__ */ (0, X.jsxs)("button", {
				className: "pipeline-dashboard-btn pipeline-dashboard-btn--primary",
				type: "button",
				onClick: t,
				disabled: r,
				children: [r ? /* @__PURE__ */ (0, X.jsx)(O, {
					size: 17,
					"aria-hidden": "true"
				}) : /* @__PURE__ */ (0, X.jsx)(ae, {
					size: 17,
					"aria-hidden": "true"
				}), r ? "Pipeline Running..." : "Run Pipeline"]
			})]
		})]
	});
}
function dL({ pipeline: e, checkedAt: t }) {
	let n = UI(e.status), r = n === "starting" || n === "running", i = WI(e), a = new Set(Array.isArray(e.completed_stages) ? e.completed_stages : []), o = i.filter((e) => a.has(e)).length, s = i.length ? Math.min(o, i.length) : 0, c = String(e.current_stage || "").trim(), l = c && c.toLowerCase() !== "unknown" ? eL(c) : n === "failed" ? "Pipeline failed" : "Not active", u = JI(e.started_at, e.finished_at, t), d = YI(e), f = XI(e, t), p = n === "failed" ? e.error || e.summary_message || e.stage_message || "The latest pipeline run did not complete." : e.summary_message || e.stage_message || (n === "idle" ? "No pipeline run is active." : n === "succeeded" ? "The latest pipeline run completed successfully." : "Waiting for pipeline status details."), m = [
		["Run ID", e.run_id],
		["Started", qI(e.started_at)],
		["Last updated", qI(d)],
		["Completed", qI(e.finished_at)],
		["Elapsed", u],
		["Return code", e.return_code === null || e.return_code === void 0 ? "" : String(e.return_code)]
	].filter((e) => !!e[1]);
	return /* @__PURE__ */ (0, X.jsxs)("section", {
		className: `pipeline-panel pipeline-run-summary pipeline-run-summary--${n}`,
		"aria-labelledby": "pipeline-current-run-title",
		"aria-busy": r,
		children: [
			/* @__PURE__ */ (0, X.jsxs)("div", {
				className: "pipeline-panel-heading",
				children: [/* @__PURE__ */ (0, X.jsxs)("div", { children: [/* @__PURE__ */ (0, X.jsx)("p", {
					className: "pipeline-panel-kicker",
					children: "Current run"
				}), /* @__PURE__ */ (0, X.jsx)("h2", {
					id: "pipeline-current-run-title",
					children: l
				})] }), /* @__PURE__ */ (0, X.jsxs)("span", {
					className: `pipeline-status-badge pipeline-status-badge--${n}`,
					role: "status",
					children: [/* @__PURE__ */ (0, X.jsx)("span", { "aria-hidden": "true" }), tL(n)]
				})]
			}),
			/* @__PURE__ */ (0, X.jsx)("p", {
				className: "pipeline-run-message",
				children: p
			}),
			r ? /* @__PURE__ */ (0, X.jsxs)("div", {
				className: "pipeline-running-indicator",
				role: "status",
				children: [/* @__PURE__ */ (0, X.jsx)("span", {
					className: "pipeline-running-indicator__spinner",
					"aria-hidden": "true"
				}), /* @__PURE__ */ (0, X.jsxs)("span", { children: [/* @__PURE__ */ (0, X.jsx)("strong", { children: "Live run in progress" }), e.stage_message || "Waiting for the next pipeline update."] })]
			}) : null,
			f ? /* @__PURE__ */ (0, X.jsxs)("div", {
				className: "pipeline-stale-notice",
				role: "status",
				children: [/* @__PURE__ */ (0, X.jsx)(fe, {
					size: 16,
					"aria-hidden": "true"
				}), " Status may be stale. The backend still reports this run as running."]
			}) : null,
			/* @__PURE__ */ (0, X.jsxs)("div", {
				className: "pipeline-stage-progress-copy",
				children: [/* @__PURE__ */ (0, X.jsxs)("span", { children: [
					o,
					" of ",
					i.length,
					" stages complete"
				] }), e.stage_message ? /* @__PURE__ */ (0, X.jsx)("strong", { children: e.stage_message }) : null]
			}),
			/* @__PURE__ */ (0, X.jsx)("progress", {
				className: "pipeline-stage-progress",
				max: i.length || 1,
				value: s,
				"aria-label": `${o} of ${i.length} pipeline stages complete`
			}),
			r ? /* @__PURE__ */ (0, X.jsx)("div", {
				className: "pipeline-running-strip",
				"aria-hidden": "true",
				children: /* @__PURE__ */ (0, X.jsx)("span", {})
			}) : null,
			m.length ? /* @__PURE__ */ (0, X.jsx)("dl", {
				className: "pipeline-run-details",
				children: m.map(([e, t]) => /* @__PURE__ */ (0, X.jsxs)("div", { children: [/* @__PURE__ */ (0, X.jsx)("dt", { children: e }), /* @__PURE__ */ (0, X.jsx)("dd", { children: t })] }, e))
			}) : null,
			e.final_job_count !== null && e.final_job_count !== void 0 ? /* @__PURE__ */ (0, X.jsxs)("div", {
				className: "pipeline-final-count",
				children: [
					/* @__PURE__ */ (0, X.jsx)(te, {
						size: 18,
						"aria-hidden": "true"
					}),
					/* @__PURE__ */ (0, X.jsx)("span", { children: "Final jobs" }),
					/* @__PURE__ */ (0, X.jsx)("strong", { children: KI(Number(e.final_job_count)) })
				]
			}) : null
		]
	});
}
function fL({ pipeline: e }) {
	let t = UI(e.status);
	return /* @__PURE__ */ (0, X.jsxs)("section", {
		className: "pipeline-panel pipeline-stage-panel",
		"aria-labelledby": "pipeline-stage-title",
		children: [/* @__PURE__ */ (0, X.jsxs)("div", {
			className: "pipeline-panel-heading",
			children: [/* @__PURE__ */ (0, X.jsxs)("div", { children: [/* @__PURE__ */ (0, X.jsx)("p", {
				className: "pipeline-panel-kicker",
				children: "Stage progress"
			}), /* @__PURE__ */ (0, X.jsx)("h2", {
				id: "pipeline-stage-title",
				children: "Execution timeline"
			})] }), /* @__PURE__ */ (0, X.jsx)(O, {
				size: 20,
				"aria-hidden": "true"
			})]
		}), /* @__PURE__ */ (0, X.jsx)("ol", {
			className: "pipeline-stage-list",
			"aria-label": "Pipeline stages",
			children: WI(e).map((n, r) => {
				let i = nL(e, n, t);
				return /* @__PURE__ */ (0, X.jsxs)("li", {
					className: `pipeline-stage pipeline-stage--${i}`,
					"aria-current": i === "active" ? "step" : void 0,
					"data-stage-index": r + 1,
					children: [
						/* @__PURE__ */ (0, X.jsx)("span", {
							className: "pipeline-stage-marker",
							"aria-hidden": "true",
							children: i === "complete" ? /* @__PURE__ */ (0, X.jsx)(k, { size: 13 }) : i === "failed" ? /* @__PURE__ */ (0, X.jsx)(fe, { size: 13 }) : /* @__PURE__ */ (0, X.jsx)(P, { size: 9 })
						}),
						/* @__PURE__ */ (0, X.jsxs)("span", {
							className: "pipeline-stage-name",
							title: eL(n),
							children: [/* @__PURE__ */ (0, X.jsx)("span", {
								"aria-hidden": "true",
								children: String(r + 1).padStart(2, "0")
							}), eL(n)]
						}),
						/* @__PURE__ */ (0, X.jsx)("small", { children: i === "complete" ? "Complete" : i === "active" ? "Active" : i === "failed" ? "Failed" : "Pending" })
					]
				}, n);
			})
		})]
	});
}
function pL({ pipeline: e }) {
	let t = e.counts || {}, n = VI.map((e) => ({
		label: e.label,
		values: e.keys.flatMap(([e, n]) => {
			let r = GI(t[e]);
			return r === null ? (t[e] !== void 0 && t[e] !== null && console.warn(`Ignoring malformed pipeline count: ${e}`), []) : [{
				key: e,
				label: n,
				value: r
			}];
		})
	})).filter((e) => e.values.length);
	return /* @__PURE__ */ (0, X.jsxs)("section", {
		className: "pipeline-section",
		"aria-labelledby": "pipeline-counts-title",
		children: [/* @__PURE__ */ (0, X.jsxs)("div", {
			className: "pipeline-section-heading",
			children: [/* @__PURE__ */ (0, X.jsxs)("div", { children: [/* @__PURE__ */ (0, X.jsx)("p", {
				className: "pipeline-panel-kicker",
				children: "Live counts"
			}), /* @__PURE__ */ (0, X.jsx)("h2", {
				id: "pipeline-counts-title",
				children: "Jobs through the pipeline"
			})] }), /* @__PURE__ */ (0, X.jsx)("span", { children: "Only recorded values are shown" })]
		}), n.length ? /* @__PURE__ */ (0, X.jsx)("div", {
			className: "pipeline-count-groups",
			children: n.map((e) => /* @__PURE__ */ (0, X.jsxs)("section", {
				className: "pipeline-count-group",
				"aria-label": e.label,
				children: [/* @__PURE__ */ (0, X.jsx)("h3", { children: e.label }), /* @__PURE__ */ (0, X.jsx)("div", {
					className: "pipeline-count-grid",
					children: e.values.map((e) => /* @__PURE__ */ (0, X.jsxs)("article", {
						className: "pipeline-count-card",
						children: [/* @__PURE__ */ (0, X.jsx)("span", { children: e.label }), /* @__PURE__ */ (0, X.jsx)("strong", { children: KI(e.value) })]
					}, e.key))
				})]
			}, e.label))
		}) : /* @__PURE__ */ (0, X.jsx)("div", {
			className: "pipeline-empty-panel pipeline-empty-panel--compact",
			children: "Stage counts are not available for this run yet."
		})]
	});
}
function mL({ pipeline: e }) {
	let t = e.counts || {}, n = HI.flatMap(([n, r]) => {
		var i;
		let a = n === "final_jobs" ? e.final_job_count : void 0, o = GI((i = t[n]) == null ? a : i);
		return o === null ? [] : [{
			key: n,
			label: r,
			value: o
		}];
	}), r = Math.max(...n.map((e) => e.value), 0);
	return /* @__PURE__ */ (0, X.jsxs)("section", {
		className: `pipeline-panel pipeline-flow-panel${n.length ? "" : " pipeline-flow-panel--empty"}`,
		"aria-labelledby": "pipeline-flow-title",
		children: [/* @__PURE__ */ (0, X.jsxs)("div", {
			className: "pipeline-panel-heading",
			children: [/* @__PURE__ */ (0, X.jsxs)("div", { children: [/* @__PURE__ */ (0, X.jsx)("p", {
				className: "pipeline-panel-kicker",
				children: "Pipeline flow"
			}), /* @__PURE__ */ (0, X.jsx)("h2", {
				id: "pipeline-flow-title",
				children: "Current-run volume"
			})] }), /* @__PURE__ */ (0, X.jsx)("span", {
				className: "pipeline-panel-note",
				children: "Relative to the largest recorded stage"
			})]
		}), n.length ? /* @__PURE__ */ (0, X.jsx)("div", {
			className: "pipeline-flow",
			role: "img",
			"aria-label": n.map((e) => `${e.label}: ${KI(e.value)}`).join(", "),
			children: n.map((e, t) => {
				let i = r > 0 ? Math.max(e.value / r * 100, e.value > 0 ? 3 : 0) : 0;
				return /* @__PURE__ */ (0, X.jsxs)("div", {
					className: "pipeline-flow-step",
					children: [
						/* @__PURE__ */ (0, X.jsxs)("div", {
							className: "pipeline-flow-meta",
							children: [/* @__PURE__ */ (0, X.jsx)("span", { children: e.label }), /* @__PURE__ */ (0, X.jsx)("strong", { children: KI(e.value) })]
						}),
						/* @__PURE__ */ (0, X.jsx)("div", {
							className: "pipeline-flow-track",
							"aria-hidden": "true",
							children: /* @__PURE__ */ (0, X.jsx)("span", { style: { width: `${i}%` } })
						}),
						t < n.length - 1 ? /* @__PURE__ */ (0, X.jsx)("span", {
							className: "pipeline-flow-connector",
							"aria-hidden": "true"
						}) : null
					]
				}, e.key);
			})
		}) : /* @__PURE__ */ (0, X.jsx)("div", {
			className: "pipeline-empty-panel pipeline-empty-panel--compact",
			children: "Flow data will appear when the run records stage counts."
		})]
	});
}
function hL({ pipeline: e }) {
	let t = e.config || {}, n = $I.flatMap(([e, n]) => {
		let r = rL(t[e]);
		return r ? [{
			key: e,
			label: n,
			value: r
		}] : [];
	});
	return /* @__PURE__ */ (0, X.jsxs)("section", {
		className: "pipeline-panel pipeline-compact-panel",
		"aria-labelledby": "pipeline-config-title",
		children: [/* @__PURE__ */ (0, X.jsxs)("div", {
			className: "pipeline-panel-heading",
			children: [/* @__PURE__ */ (0, X.jsxs)("div", { children: [/* @__PURE__ */ (0, X.jsx)("p", {
				className: "pipeline-panel-kicker",
				children: "Run configuration"
			}), /* @__PURE__ */ (0, X.jsx)("h2", {
				id: "pipeline-config-title",
				children: "Safe settings snapshot"
			})] }), /* @__PURE__ */ (0, X.jsx)(ue, {
				size: 20,
				"aria-hidden": "true"
			})]
		}), n.length ? /* @__PURE__ */ (0, X.jsx)("dl", {
			className: "pipeline-config-list",
			children: n.map((e) => /* @__PURE__ */ (0, X.jsxs)("div", { children: [/* @__PURE__ */ (0, X.jsx)("dt", { children: e.label }), /* @__PURE__ */ (0, X.jsx)("dd", { children: e.value })] }, e.key))
		}) : /* @__PURE__ */ (0, X.jsx)("div", {
			className: "pipeline-empty-panel",
			children: "No safe configuration fields were recorded for this run."
		})]
	});
}
function gL({ pipeline: e }) {
	let t = Array.isArray(e.source_health) ? e.source_health.filter((e) => e && typeof e.source == "string" && e.source.trim()) : [];
	return /* @__PURE__ */ (0, X.jsxs)("section", {
		className: "pipeline-panel pipeline-compact-panel",
		"aria-labelledby": "pipeline-health-title",
		children: [/* @__PURE__ */ (0, X.jsxs)("div", {
			className: "pipeline-panel-heading",
			children: [/* @__PURE__ */ (0, X.jsxs)("div", { children: [/* @__PURE__ */ (0, X.jsx)("p", {
				className: "pipeline-panel-kicker",
				children: "Source health"
			}), /* @__PURE__ */ (0, X.jsx)("h2", {
				id: "pipeline-health-title",
				children: "Collection evidence"
			})] }), /* @__PURE__ */ (0, X.jsx)(de, {
				size: 20,
				"aria-hidden": "true"
			})]
		}), t.length ? /* @__PURE__ */ (0, X.jsx)("ul", {
			className: "pipeline-health-list",
			children: t.map((e) => /* @__PURE__ */ (0, X.jsxs)("li", { children: [
				/* @__PURE__ */ (0, X.jsxs)("div", { children: [/* @__PURE__ */ (0, X.jsx)("strong", { children: e.source }), /* @__PURE__ */ (0, X.jsx)("span", { children: e.status || "Status unavailable" })] }),
				GI(e.jobs_returned) === null ? null : /* @__PURE__ */ (0, X.jsxs)("span", { children: [KI(Number(e.jobs_returned)), " jobs"] }),
				e.last_success ? /* @__PURE__ */ (0, X.jsx)("time", {
					dateTime: e.last_success,
					children: qI(e.last_success)
				}) : null
			] }, e.source))
		}) : /* @__PURE__ */ (0, X.jsxs)("div", {
			className: "pipeline-source-unavailable",
			role: "status",
			children: [/* @__PURE__ */ (0, X.jsx)(de, {
				size: 18,
				"aria-hidden": "true"
			}), /* @__PURE__ */ (0, X.jsxs)("div", { children: [/* @__PURE__ */ (0, X.jsx)("strong", { children: "Source health data is not available yet" }), /* @__PURE__ */ (0, X.jsx)("span", { children: "No source status is inferred from missing job counts." })] })]
		})]
	});
}
function _L({ readStatus: e = iL, launchPipeline: t = aL, pollIntervalMs: n = RI }) {
	let r = oL(), i = (0, C.useRef)(r), [a, o] = (0, C.useState)(() => r ? {
		kind: "ready",
		payload: cL(r),
		checkedAt: Date.now()
	} : { kind: "loading" }), [s, c] = (0, C.useState)(!1), l = (0, C.useCallback)(async (t = !1) => {
		t && c(!0);
		try {
			var n, r;
			let t = await e(), a = i.current, s = String(((n = t.pipeline) == null ? void 0 : n.run_id) || "").trim();
			if (a && s !== a) {
				o({
					kind: "ready",
					payload: cL(a),
					checkedAt: Date.now()
				});
				return;
			}
			a && s === a && (i.current = "", sL(a)), o({
				kind: "ready",
				payload: t,
				checkedAt: Date.now()
			});
			let c = (r = t.pipeline) == null ? void 0 : r.status;
			UI(c) === "unavailable" && console.warn(`Unsupported pipeline status: ${String(c || "")}`);
		} catch (e) {
			console.error("Failed to read Pipeline page status", e), o({
				kind: "error",
				message: e instanceof Error ? e.message : "Pipeline status is unavailable."
			});
		} finally {
			t && c(!1);
		}
	}, [e]);
	(0, C.useEffect)(() => {
		l();
	}, [l]), (0, C.useEffect)(() => {
		let e = (e) => {
			var t;
			let n = e.detail || {}, r = String(n.runId || ((t = n.pipeline) == null ? void 0 : t.run_id) || "").trim();
			r && (i.current = r, o({
				kind: "ready",
				payload: cL(r, n.pipeline),
				checkedAt: Date.now()
			}), l());
		};
		return window.addEventListener(ZI, e), () => window.removeEventListener(ZI, e);
	}, [l]);
	let u = a.kind === "ready" && a.payload.pipeline || {}, d = UI(u.status), f = a.kind === "ready" && (d === "starting" || d === "running");
	(0, C.useEffect)(() => {
		if (!f) return;
		let e = window.setInterval(() => void l(), n);
		return () => window.clearInterval(e);
	}, [
		n,
		l,
		f
	]);
	let p = a.kind === "ready" ? a.checkedAt : Date.now(), m = (0, C.useMemo)(() => `pipeline-dashboard pipeline-dashboard--${d}`, [d]);
	return a.kind === "loading" ? /* @__PURE__ */ (0, X.jsx)(lL, {}) : a.kind === "error" ? /* @__PURE__ */ (0, X.jsxs)("div", {
		className: "pipeline-dashboard pipeline-dashboard--error",
		children: [/* @__PURE__ */ (0, X.jsx)(uL, {
			onRefresh: () => void l(!0),
			onRun: t,
			refreshing: s,
			runActive: !1
		}), /* @__PURE__ */ (0, X.jsxs)("section", {
			className: "pipeline-status-error",
			role: "alert",
			children: [
				/* @__PURE__ */ (0, X.jsx)(fe, {
					size: 22,
					"aria-hidden": "true"
				}),
				/* @__PURE__ */ (0, X.jsxs)("div", { children: [/* @__PURE__ */ (0, X.jsx)("h2", { children: "Pipeline status is unavailable" }), /* @__PURE__ */ (0, X.jsx)("p", { children: a.message })] }),
				/* @__PURE__ */ (0, X.jsx)("button", {
					type: "button",
					onClick: () => void l(!0),
					children: "Retry"
				})
			]
		})]
	}) : /* @__PURE__ */ (0, X.jsxs)("div", {
		className: m,
		"data-theme-surface": "pipeline",
		"aria-busy": f,
		children: [
			/* @__PURE__ */ (0, X.jsx)(uL, {
				onRefresh: () => void l(!0),
				onRun: t,
				refreshing: s,
				runActive: d === "starting" || d === "running"
			}),
			d === "idle" ? /* @__PURE__ */ (0, X.jsxs)("section", {
				className: "pipeline-idle-banner",
				role: "status",
				children: [/* @__PURE__ */ (0, X.jsx)(ee, {
					size: 20,
					"aria-hidden": "true"
				}), /* @__PURE__ */ (0, X.jsxs)("div", { children: [/* @__PURE__ */ (0, X.jsx)("strong", { children: "Pipeline is idle" }), /* @__PURE__ */ (0, X.jsx)("span", { children: "Start a run through the existing reviewed launch flow." })] })]
			}) : null,
			/* @__PURE__ */ (0, X.jsxs)("div", {
				className: "pipeline-dashboard-top-grid",
				children: [/* @__PURE__ */ (0, X.jsx)(dL, {
					pipeline: u,
					checkedAt: p
				}), /* @__PURE__ */ (0, X.jsx)(fL, { pipeline: u })]
			}),
			/* @__PURE__ */ (0, X.jsx)(pL, { pipeline: u }),
			/* @__PURE__ */ (0, X.jsx)(mL, { pipeline: u }),
			/* @__PURE__ */ (0, X.jsxs)("div", {
				className: "pipeline-dashboard-bottom-grid",
				children: [/* @__PURE__ */ (0, X.jsx)(hL, { pipeline: u }), /* @__PURE__ */ (0, X.jsx)(gL, { pipeline: u })]
			})
		]
	});
}
//#endregion
//#region src/main.tsx
var vL = "applylens:executive-kpi-state", yL = { status: "loading" };
function bL() {
	let [e, t] = (0, C.useState)(() => window.__APPLYLENS_EXECUTIVE_KPI_STATE__ || yL);
	return (0, C.useEffect)(() => {
		let e = (e) => {
			let n = e.detail;
			n != null && n.status && t(n);
		};
		return window.addEventListener(vL, e), () => window.removeEventListener(vL, e);
	}, []), /* @__PURE__ */ (0, X.jsx)(WP, { state: e });
}
function xL() {
	let [e, t] = (0, C.useState)(() => window.__APPLYLENS_EXECUTIVE_QUEUE_STATE__ || gI);
	return (0, C.useEffect)(() => {
		let e = (e) => {
			let n = e.detail;
			n != null && n.status && t(n);
		};
		return window.addEventListener(fI, e), () => window.removeEventListener(fI, e);
	}, []), /* @__PURE__ */ (0, X.jsx)(LI, { state: e });
}
var SL = document.getElementById("executiveKpiRoot");
SL && (0, IP.createRoot)(SL).render(/* @__PURE__ */ (0, X.jsx)(C.StrictMode, { children: /* @__PURE__ */ (0, X.jsx)(bL, {}) }));
var CL = document.getElementById("executiveQueueRoot");
CL && (0, IP.createRoot)(CL).render(/* @__PURE__ */ (0, X.jsx)(C.StrictMode, { children: /* @__PURE__ */ (0, X.jsx)(xL, {}) }));
var wL = document.getElementById("pipelineDashboardRoot");
wL && (0, IP.createRoot)(wL).render(/* @__PURE__ */ (0, X.jsx)(C.StrictMode, { children: /* @__PURE__ */ (0, X.jsx)(_L, {}) }));
//#endregion
