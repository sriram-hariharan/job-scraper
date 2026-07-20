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
	function qt(e) {
		return e &= -e, 1 < e ? 4 < e ? e & 268435455 ? 16 : 536870912 : 4 : 1;
	}
	var Jt, Yt, Xt, Zt, Qt, $t = !1, en = [], I = null, tn = null, nn = null, rn = /* @__PURE__ */ new Map(), an = /* @__PURE__ */ new Map(), on = [], sn = "mousedown mouseup touchcancel touchend touchstart auxclick dblclick pointercancel pointerdown pointerup dragend dragstart drop compositionend compositionstart keydown keypress keyup input textInput copy cut paste click change contextmenu reset submit".split(" ");
	function cn(e, t) {
		switch (e) {
			case "focusin":
			case "focusout":
				I = null;
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
		}, t !== null && (t = Wi(t), t !== null && Yt(t)), e) : (e.eventSystemFlags |= r, t = e.targetContainers, i !== null && t.indexOf(i) === -1 && t.push(i), e);
	}
	function un(e, t, n, r, i) {
		switch (t) {
			case "focusin": return I = ln(I, e, t, n, r, i), !0;
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
						e.blockedOn = t, Qt(e.priority, function() {
							Xt(n);
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
			} else return t = Wi(n), t !== null && Yt(t), e.blockedOn = n, !1;
			t.shift();
		}
		return !0;
	}
	function pn(e, t, n) {
		fn(e) && n.delete(t);
	}
	function mn() {
		$t = !1, I !== null && fn(I) && (I = null), tn !== null && fn(tn) && (tn = null), nn !== null && fn(nn) && (nn = null), rn.forEach(pn), an.forEach(pn);
	}
	function hn(e, t) {
		e.blockedOn === t && (e.blockedOn = null, $t || ($t = !0, n.unstable_scheduleCallback(n.unstable_NormalPriority, mn)));
	}
	function gn(e) {
		function t(t) {
			return hn(t, e);
		}
		if (0 < en.length) {
			hn(en[0], e);
			for (var n = 1; n < en.length; n++) {
				var r = en[n];
				r.blockedOn === e && (r.blockedOn = null);
			}
		}
		for (I !== null && hn(I, e), tn !== null && hn(tn, e), nn !== null && hn(nn, e), rn.forEach(t), an.forEach(t), n = 0; n < on.length; n++) r = on[n], r.blockedOn === e && (r.blockedOn = null);
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
					if (a !== null && Jt(a), a = Cn(e, t, n, r), a === null && hi(e, t, r, Sn, n), a === i) break;
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
	function Nr(e, t) {
		return e === t && (e !== 0 || 1 / e == 1 / t) || e !== e && t !== t;
	}
	var Pr = typeof Object.is == "function" ? Object.is : Nr;
	function Fr(e, t) {
		if (Pr(e, t)) return !0;
		if (typeof e != "object" || !e || typeof t != "object" || !t) return !1;
		var n = Object.keys(e), r = Object.keys(t);
		if (n.length !== r.length) return !1;
		for (r = 0; r < n.length; r++) {
			var i = n[r];
			if (!l.call(t, i) || !Pr(e[i], t[i])) return !1;
		}
		return !0;
	}
	function Ir(e) {
		for (; e && e.firstChild;) e = e.firstChild;
		return e;
	}
	function Lr(e, t) {
		var n = Ir(e);
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
			n = Ir(n);
		}
	}
	function Rr(e, t) {
		return e && t ? e === t ? !0 : e && e.nodeType === 3 ? !1 : t && t.nodeType === 3 ? Rr(e, t.parentNode) : "contains" in e ? e.contains(t) : e.compareDocumentPosition ? !!(e.compareDocumentPosition(t) & 16) : !1 : !1;
	}
	function zr() {
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
	function Br(e) {
		var t = e && e.nodeName && e.nodeName.toLowerCase();
		return t && (t === "input" && (e.type === "text" || e.type === "search" || e.type === "tel" || e.type === "url" || e.type === "password") || t === "textarea" || e.contentEditable === "true");
	}
	function L(e) {
		var t = zr(), n = e.focusedElem, r = e.selectionRange;
		if (t !== n && n && n.ownerDocument && Rr(n.ownerDocument.documentElement, n)) {
			if (r !== null && Br(n)) {
				if (t = r.start, e = r.end, e === void 0 && (e = t), "selectionStart" in n) n.selectionStart = t, n.selectionEnd = Math.min(e, n.value.length);
				else if (e = (t = n.ownerDocument || document) && t.defaultView || window, e.getSelection) {
					e = e.getSelection();
					var i = n.textContent.length, a = Math.min(r.start, i);
					r = r.end === void 0 ? a : Math.min(r.end, i), !e.extend && a > r && (i = r, r = a, a = i), i = Lr(n, a);
					var o = Lr(n, r);
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
		Gr || Hr == null || Hr !== _e(r) || (r = Hr, "selectionStart" in r && Br(r) ? r = {
			start: r.selectionStart,
			end: r.selectionEnd
		} : (r = (r.ownerDocument && r.ownerDocument.defaultView || window).getSelection(), r = {
			anchorNode: r.anchorNode,
			anchorOffset: r.anchorOffset,
			focusNode: r.focusNode,
			focusOffset: r.focusOffset
		}), Wr && Fr(Wr, r) || (Wr = r, r = _i(Ur, "onSelect"), 0 < r.length && (t = new Pn("onSelect", "select", null, t, n), e.push({
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
	}, Yr = {}, Xr = {};
	c && (Xr = document.createElement("div").style, "AnimationEvent" in window || (delete Jr.animationend.animation, delete Jr.animationiteration.animation, delete Jr.animationstart.animation), "TransitionEvent" in window || delete Jr.transitionend.transition);
	function Zr(e) {
		if (Yr[e]) return Yr[e];
		if (!Jr[e]) return e;
		var t = Jr[e], n;
		for (n in t) if (t.hasOwnProperty(n) && n in Xr) return Yr[e] = t[n];
		return e;
	}
	var Qr = Zr("animationend"), $r = Zr("animationiteration"), ei = Zr("animationstart"), ti = Zr("transitionend"), ni = /* @__PURE__ */ new Map(), ri = "abort auxClick cancel canPlay canPlayThrough click close contextMenu copy cut drag dragEnd dragEnter dragExit dragLeave dragOver dragStart drop durationChange emptied encrypted ended error gotPointerCapture input invalid keyDown keyPress keyUp load loadedData loadedMetadata loadStart lostPointerCapture mouseDown mouseMove mouseOut mouseOver mouseUp paste pause play playing pointerCancel pointerDown pointerMove pointerOut pointerOver pointerUp progress rateChange reset resize seeked seeking stalled submit suspend timeUpdate touchCancel touchEnd touchStart volumeChange scroll toggle touchMove waiting wheel".split(" ");
	function R(e, t) {
		ni.set(e, t), o(t, [e]);
	}
	for (var ii = 0; ii < ri.length; ii++) {
		var ai = ri[ii];
		R(ai.toLowerCase(), "on" + (ai[0].toUpperCase() + ai.slice(1)));
	}
	R(Qr, "onAnimationEnd"), R($r, "onAnimationIteration"), R(ei, "onAnimationStart"), R("dblclick", "onDoubleClick"), R("focusin", "onFocus"), R("focusout", "onBlur"), R(ti, "onTransitionEnd"), s("onMouseEnter", ["mouseout", "mouseover"]), s("onMouseLeave", ["mouseout", "mouseover"]), s("onPointerEnter", ["pointerout", "pointerover"]), s("onPointerLeave", ["pointerout", "pointerover"]), o("onChange", "change click focusin focusout input keydown keyup selectionchange".split(" ")), o("onSelect", "focusout contextmenu dragend focusin keydown keyup mousedown mouseup selectionchange".split(" ")), o("onBeforeInput", [
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
				var s = ni.get(e);
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
						case Qr:
						case $r:
						case ei:
							c = Wn;
							break;
						case ti:
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
	function Xi(e, t) {
		Ji++, qi[Ji] = e.current, e.current = t;
	}
	var Zi = {}, Qi = Yi(Zi), $i = Yi(!1), ea = Zi;
	function ta(e, t) {
		var n = e.type.contextTypes;
		if (!n) return Zi;
		var r = e.stateNode;
		if (r && r.__reactInternalMemoizedUnmaskedChildContext === t) return r.__reactInternalMemoizedMaskedChildContext;
		var i = {}, a;
		for (a in n) i[a] = t[a];
		return r && (e = e.stateNode, e.__reactInternalMemoizedUnmaskedChildContext = t, e.__reactInternalMemoizedMaskedChildContext = i), i;
	}
	function na(e) {
		return e = e.childContextTypes, e != null;
	}
	function ra() {
		z($i), z(Qi);
	}
	function ia(e, t, n) {
		if (Qi.current !== Zi) throw Error(r(168));
		Xi(Qi, t), Xi($i, n);
	}
	function aa(e, t, n) {
		var i = e.stateNode;
		if (t = t.childContextTypes, typeof i.getChildContext != "function") return n;
		for (var a in i = i.getChildContext(), i) if (!(a in t)) throw Error(r(108, de(e) || "Unknown", a));
		return ie({}, n, i);
	}
	function oa(e) {
		return e = (e = e.stateNode) && e.__reactInternalMemoizedMergedChildContext || Zi, ea = Qi.current, Xi(Qi, e), Xi($i, $i.current), !0;
	}
	function sa(e, t, n) {
		var i = e.stateNode;
		if (!i) throw Error(r(169));
		n ? (e = aa(e, t, ea), i.__reactInternalMemoizedMergedChildContext = e, z($i), z(Qi), Xi(Qi, e)) : z($i), Xi($i, n);
	}
	var ca = null, la = !1, ua = !1;
	function da(e) {
		ca === null ? ca = [e] : ca.push(e);
	}
	function fa(e) {
		la = !0, da(e);
	}
	function pa() {
		if (!ua && ca !== null) {
			ua = !0;
			var e = 0, t = F;
			try {
				var n = ca;
				for (F = 1; e < n.length; e++) {
					var r = n[e];
					do
						r = r(!0);
					while (r !== null);
				}
				ca = null, la = !1;
			} catch (t) {
				throw ca !== null && (ca = ca.slice(e + 1)), _t(Ct, pa), t;
			} finally {
				F = t, ua = !1;
			}
		}
		return null;
	}
	var ma = [], ha = 0, ga = null, _a = 0, va = [], ya = 0, ba = null, xa = 1, Sa = "";
	function Ca(e, t) {
		ma[ha++] = _a, ma[ha++] = ga, ga = e, _a = t;
	}
	function wa(e, t, n) {
		va[ya++] = xa, va[ya++] = Sa, va[ya++] = ba, ba = e;
		var r = xa;
		e = Sa;
		var i = 32 - jt(r) - 1;
		r &= ~(1 << i), n += 1;
		var a = 32 - jt(t) + i;
		if (30 < a) {
			var o = i - i % 5;
			a = (r & (1 << o) - 1).toString(32), r >>= o, i -= o, xa = 1 << 32 - jt(t) + i | n << i | r, Sa = a + e;
		} else xa = 1 << a | n << i | r, Sa = e;
	}
	function Ta(e) {
		e.return !== null && (Ca(e, 1), wa(e, 1, 0));
	}
	function Ea(e) {
		for (; e === ga;) ga = ma[--ha], ma[ha] = null, _a = ma[--ha], ma[ha] = null;
		for (; e === ba;) ba = va[--ya], va[ya] = null, Sa = va[--ya], va[ya] = null, xa = va[--ya], va[ya] = null;
	}
	var Da = null, Oa = null, ka = !1, Aa = null;
	function ja(e, t) {
		var n = $l(5, null, null, 0);
		n.elementType = "DELETED", n.stateNode = t, n.return = e, t = e.deletions, t === null ? (e.deletions = [n], e.flags |= 16) : t.push(n);
	}
	function Ma(e, t) {
		switch (e.tag) {
			case 5:
				var n = e.type;
				return t = t.nodeType !== 1 || n.toLowerCase() !== t.nodeName.toLowerCase() ? null : t, t === null ? !1 : (e.stateNode = t, Da = e, Oa = Pi(t.firstChild), !0);
			case 6: return t = e.pendingProps === "" || t.nodeType !== 3 ? null : t, t === null ? !1 : (e.stateNode = t, Da = e, Oa = null, !0);
			case 13: return t = t.nodeType === 8 ? t : null, t === null ? !1 : (n = ba === null ? null : {
				id: xa,
				overflow: Sa
			}, e.memoizedState = {
				dehydrated: t,
				treeContext: n,
				retryLane: 1073741824
			}, n = $l(18, null, null, 0), n.stateNode = t, n.return = e, e.child = n, Da = e, Oa = null, !0);
			default: return !1;
		}
	}
	function Na(e) {
		return (e.mode & 1) != 0 && (e.flags & 128) == 0;
	}
	function Pa(e) {
		if (ka) {
			var t = Oa;
			if (t) {
				var n = t;
				if (!Ma(e, t)) {
					if (Na(e)) throw Error(r(418));
					t = Pi(n.nextSibling);
					var i = Da;
					t && Ma(e, t) ? ja(i, n) : (e.flags = e.flags & -4097 | 2, ka = !1, Da = e);
				}
			} else {
				if (Na(e)) throw Error(r(418));
				e.flags = e.flags & -4097 | 2, ka = !1, Da = e;
			}
		}
	}
	function Fa(e) {
		for (e = e.return; e !== null && e.tag !== 5 && e.tag !== 3 && e.tag !== 13;) e = e.return;
		Da = e;
	}
	function Ia(e) {
		if (e !== Da) return !1;
		if (!ka) return Fa(e), ka = !0, !1;
		var t;
		if ((t = e.tag !== 3) && !(t = e.tag !== 5) && (t = e.type, t = t !== "head" && t !== "body" && !Di(e.type, e.memoizedProps)), t && (t = Oa)) {
			if (Na(e)) throw La(), Error(r(418));
			for (; t;) ja(e, t), t = Pi(t.nextSibling);
		}
		if (Fa(e), e.tag === 13) {
			if (e = e.memoizedState, e = e === null ? null : e.dehydrated, !e) throw Error(r(317));
			a: {
				for (e = e.nextSibling, t = 0; e;) {
					if (e.nodeType === 8) {
						var n = e.data;
						if (n === "/$") {
							if (t === 0) {
								Oa = Pi(e.nextSibling);
								break a;
							}
							t--;
						} else n !== "$" && n !== "$!" && n !== "$?" || t++;
					}
					e = e.nextSibling;
				}
				Oa = null;
			}
		} else Oa = Da ? Pi(e.stateNode.nextSibling) : null;
		return !0;
	}
	function La() {
		for (var e = Oa; e;) e = Pi(e.nextSibling);
	}
	function Ra() {
		Oa = Da = null, ka = !1;
	}
	function za(e) {
		Aa === null ? Aa = [e] : Aa.push(e);
	}
	var Ba = C.ReactCurrentBatchConfig;
	function Va(e, t, n) {
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
	function Ha(e, t) {
		throw e = Object.prototype.toString.call(t), Error(r(31, e === "[object Object]" ? "object with keys {" + Object.keys(t).join(", ") + "}" : e));
	}
	function Ua(e) {
		var t = e._init;
		return t(e._payload);
	}
	function Wa(e) {
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
			return e = nu(e, t), e.index = 0, e.sibling = null, e;
		}
		function o(t, n, r) {
			return t.index = r, e ? (r = t.alternate, r === null ? (t.flags |= 2, n) : (r = r.index, r < n ? (t.flags |= 2, n) : r)) : (t.flags |= 1048576, n);
		}
		function s(t) {
			return e && t.alternate === null && (t.flags |= 2), t;
		}
		function c(e, t, n, r) {
			return t === null || t.tag !== 6 ? (t = ou(n, e.mode, r), t.return = e, t) : (t = a(t, n), t.return = e, t);
		}
		function l(e, t, n, r) {
			var i = n.type;
			return i === E ? d(e, t, n.props.children, r, n.key) : t !== null && (t.elementType === i || typeof i == "object" && i && i.$$typeof === ee && Ua(i) === t.type) ? (r = a(t, n.props), r.ref = Va(e, t, n), r.return = e, r) : (r = ru(n.type, n.key, n.props, null, e.mode, r), r.ref = Va(e, t, n), r.return = e, r);
		}
		function u(e, t, n, r) {
			return t === null || t.tag !== 4 || t.stateNode.containerInfo !== n.containerInfo || t.stateNode.implementation !== n.implementation ? (t = su(n, e.mode, r), t.return = e, t) : (t = a(t, n.children || []), t.return = e, t);
		}
		function d(e, t, n, r, i) {
			return t === null || t.tag !== 7 ? (t = iu(n, e.mode, r, i), t.return = e, t) : (t = a(t, n), t.return = e, t);
		}
		function f(e, t, n) {
			if (typeof t == "string" && t !== "" || typeof t == "number") return t = ou("" + t, e.mode, n), t.return = e, t;
			if (typeof t == "object" && t) {
				switch (t.$$typeof) {
					case w: return n = ru(t.type, t.key, t.props, null, e.mode, n), n.ref = Va(e, null, t), n.return = e, n;
					case T: return t = su(t, e.mode, n), t.return = e, t;
					case ee:
						var r = t._init;
						return f(e, r(t._payload), n);
				}
				if (we(t) || re(t)) return t = iu(t, e.mode, n, null), t.return = e, t;
				Ha(e, t);
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
				Ha(e, n);
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
				Ha(t, r);
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
			if (h === s.length) return n(r, d), ka && Ca(r, h), l;
			if (d === null) {
				for (; h < s.length; h++) d = f(r, s[h], c), d !== null && (a = o(d, a, h), u === null ? l = d : u.sibling = d, u = d);
				return ka && Ca(r, h), l;
			}
			for (d = i(r, d); h < s.length; h++) g = m(d, r, h, s[h], c), g !== null && (e && g.alternate !== null && d.delete(g.key === null ? h : g.key), a = o(g, a, h), u === null ? l = g : u.sibling = g, u = g);
			return e && d.forEach(function(e) {
				return t(r, e);
			}), ka && Ca(r, h), l;
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
			if (v.done) return n(a, h), ka && Ca(a, g), u;
			if (h === null) {
				for (; !v.done; g++, v = c.next()) v = f(a, v.value, l), v !== null && (s = o(v, s, g), d === null ? u = v : d.sibling = v, d = v);
				return ka && Ca(a, g), u;
			}
			for (h = i(a, h); !v.done; g++, v = c.next()) v = m(h, a, g, v.value, l), v !== null && (e && v.alternate !== null && h.delete(v.key === null ? g : v.key), s = o(v, s, g), d === null ? u = v : d.sibling = v, d = v);
			return e && h.forEach(function(e) {
				return t(a, e);
			}), ka && Ca(a, g), u;
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
									} else if (l.elementType === c || typeof c == "object" && c && c.$$typeof === ee && Ua(c) === l.type) {
										n(e, l.sibling), r = a(l, i.props), r.ref = Va(e, l, i), r.return = e, e = r;
										break a;
									}
									n(e, l);
									break;
								} else t(e, l);
								l = l.sibling;
							}
							i.type === E ? (r = iu(i.props.children, e.mode, o, i.key), r.return = e, e = r) : (o = ru(i.type, i.key, i.props, null, e.mode, o), o.ref = Va(e, r, i), o.return = e, e = o);
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
							r = su(i, e.mode, o), r.return = e, e = r;
						}
						return s(e);
					case ee: return l = i._init, _(e, r, l(i._payload), o);
				}
				if (we(i)) return h(e, r, i, o);
				if (re(i)) return g(e, r, i, o);
				Ha(e, i);
			}
			return typeof i == "string" && i !== "" || typeof i == "number" ? (i = "" + i, r !== null && r.tag === 6 ? (n(e, r.sibling), r = a(r, i), r.return = e, e = r) : (n(e, r), r = ou(i, e.mode, o), r.return = e, e = r), s(e)) : n(e, r);
		}
		return _;
	}
	var Ga = Wa(!0), Ka = Wa(!1), qa = Yi(null), Ja = null, Ya = null, Xa = null;
	function Za() {
		Xa = Ya = Ja = null;
	}
	function Qa(e) {
		var t = qa.current;
		z(qa), e._currentValue = t;
	}
	function $a(e, t, n) {
		for (; e !== null;) {
			var r = e.alternate;
			if ((e.childLanes & t) === t ? r !== null && (r.childLanes & t) !== t && (r.childLanes |= t) : (e.childLanes |= t, r !== null && (r.childLanes |= t)), e === n) break;
			e = e.return;
		}
	}
	function eo(e, t) {
		Ja = e, Xa = Ya = null, e = e.dependencies, e !== null && e.firstContext !== null && ((e.lanes & t) !== 0 && (Bs = !0), e.firstContext = null);
	}
	function to(e) {
		var t = e._currentValue;
		if (Xa !== e) if (e = {
			context: e,
			memoizedValue: t,
			next: null
		}, Ya === null) {
			if (Ja === null) throw Error(r(308));
			Ya = e, Ja.dependencies = {
				lanes: 0,
				firstContext: e
			};
		} else Ya = Ya.next = e;
		return t;
	}
	var no = null;
	function ro(e) {
		no === null ? no = [e] : no.push(e);
	}
	function B(e, t, n, r) {
		var i = t.interleaved;
		return i === null ? (n.next = n, ro(t)) : (n.next = i.next, i.next = n), t.interleaved = n, io(e, r);
	}
	function io(e, t) {
		e.lanes |= t;
		var n = e.alternate;
		for (n !== null && (n.lanes |= t), n = e, e = e.return; e !== null;) e.childLanes |= t, n = e.alternate, n !== null && (n.childLanes |= t), n = e, e = e.return;
		return n.tag === 3 ? n.stateNode : null;
	}
	var ao = !1;
	function oo(e) {
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
	function so(e, t) {
		e = e.updateQueue, t.updateQueue === e && (t.updateQueue = {
			baseState: e.baseState,
			firstBaseUpdate: e.firstBaseUpdate,
			lastBaseUpdate: e.lastBaseUpdate,
			shared: e.shared,
			effects: e.effects
		});
	}
	function co(e, t) {
		return {
			eventTime: e,
			lane: t,
			tag: 0,
			payload: null,
			callback: null,
			next: null
		};
	}
	function lo(e, t, n) {
		var r = e.updateQueue;
		if (r === null) return null;
		if (r = r.shared, G & 2) {
			var i = r.pending;
			return i === null ? t.next = t : (t.next = i.next, i.next = t), r.pending = t, io(e, n);
		}
		return i = r.interleaved, i === null ? (t.next = t, ro(r)) : (t.next = i.next, i.next = t), r.interleaved = t, io(e, n);
	}
	function uo(e, t, n) {
		if (t = t.updateQueue, t !== null && (t = t.shared, n & 4194240)) {
			var r = t.lanes;
			r &= e.pendingLanes, n |= r, t.lanes = n, Kt(e, n);
		}
	}
	function fo(e, t) {
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
	function po(e, t, n, r) {
		var i = e.updateQueue;
		ao = !1;
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
							case 2: ao = !0;
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
			nl |= o, e.lanes = o, e.memoizedState = d;
		}
	}
	function mo(e, t, n) {
		if (e = t.effects, t.effects = null, e !== null) for (t = 0; t < e.length; t++) {
			var i = e[t], a = i.callback;
			if (a !== null) {
				if (i.callback = null, i = n, typeof a != "function") throw Error(r(191, a));
				a.call(i);
			}
		}
	}
	var ho = {}, V = Yi(ho), go = Yi(ho), _o = Yi(ho);
	function vo(e) {
		if (e === ho) throw Error(r(174));
		return e;
	}
	function yo(e, t) {
		switch (Xi(_o, t), Xi(go, e), Xi(V, ho), e = t.nodeType, e) {
			case 9:
			case 11:
				t = (t = t.documentElement) ? t.namespaceURI : je(null, "");
				break;
			default: e = e === 8 ? t.parentNode : t, t = e.namespaceURI || null, e = e.tagName, t = je(t, e);
		}
		z(V), Xi(V, t);
	}
	function bo() {
		z(V), z(go), z(_o);
	}
	function xo(e) {
		vo(_o.current);
		var t = vo(V.current), n = je(t, e.type);
		t !== n && (Xi(go, e), Xi(V, n));
	}
	function So(e) {
		go.current === e && (z(V), z(go));
	}
	var Co = Yi(0);
	function wo(e) {
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
	var To = [];
	function Eo() {
		for (var e = 0; e < To.length; e++) To[e]._workInProgressVersionPrimary = null;
		To.length = 0;
	}
	var Do = C.ReactCurrentDispatcher, Oo = C.ReactCurrentBatchConfig, ko = 0, H = null, Ao = null, jo = null, Mo = !1, No = !1, Po = 0, Fo = 0;
	function Io() {
		throw Error(r(321));
	}
	function Lo(e, t) {
		if (t === null) return !1;
		for (var n = 0; n < t.length && n < e.length; n++) if (!Pr(e[n], t[n])) return !1;
		return !0;
	}
	function Ro(e, t, n, i, a, o) {
		if (ko = o, H = t, t.memoizedState = null, t.updateQueue = null, t.lanes = 0, Do.current = e === null || e.memoizedState === null ? xs : Ss, e = n(i, a), No) {
			o = 0;
			do {
				if (No = !1, Po = 0, 25 <= o) throw Error(r(301));
				o += 1, jo = Ao = null, t.updateQueue = null, Do.current = Cs, e = n(i, a);
			} while (No);
		}
		if (Do.current = bs, t = Ao !== null && Ao.next !== null, ko = 0, jo = Ao = H = null, Mo = !1, t) throw Error(r(300));
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
		return jo === null ? H.memoizedState = jo = e : jo = jo.next = e, jo;
	}
	function Vo() {
		if (Ao === null) {
			var e = H.alternate;
			e = e === null ? null : e.memoizedState;
		} else e = Ao.next;
		var t = jo === null ? H.memoizedState : jo.next;
		if (t !== null) jo = t, Ao = e;
		else {
			if (e === null) throw Error(r(310));
			Ao = e, e = {
				memoizedState: Ao.memoizedState,
				baseState: Ao.baseState,
				baseQueue: Ao.baseQueue,
				queue: Ao.queue,
				next: null
			}, jo === null ? H.memoizedState = jo = e : jo = jo.next = e;
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
				if ((ko & d) === d) l !== null && (l = l.next = {
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
					l === null ? (c = l = f, s = i) : l = l.next = f, H.lanes |= d, nl |= d;
				}
				u = u.next;
			} while (u !== null && u !== o);
			l === null ? s = i : l.next = c, Pr(i, t.memoizedState) || (Bs = !0), t.memoizedState = i, t.baseState = s, t.baseQueue = l, n.lastRenderedState = i;
		}
		if (e = n.interleaved, e !== null) {
			a = e;
			do
				o = a.lane, H.lanes |= o, nl |= o, a = a.next;
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
			Pr(o, t.memoizedState) || (Bs = !0), t.memoizedState = o, t.baseQueue === null && (t.baseState = o), n.lastRenderedState = o;
		}
		return [o, i];
	}
	function Go() {}
	function Ko(e, t) {
		var n = H, i = Vo(), a = t(), o = !Pr(i.memoizedState, a);
		if (o && (i.memoizedState = a, Bs = !0), i = i.queue, is(Yo.bind(null, n, i, e), [e]), i.getSnapshot !== t || o || jo !== null && jo.memoizedState.tag & 1) {
			if (n.flags |= 2048, $o(9, Jo.bind(null, n, i, a, t), void 0, null), Yc === null) throw Error(r(349));
			ko & 30 || qo(n, t, a);
		}
		return a;
	}
	function qo(e, t, n) {
		e.flags |= 16384, e = {
			getSnapshot: t,
			value: n
		}, t = H.updateQueue, t === null ? (t = {
			lastEffect: null,
			stores: null
		}, H.updateQueue = t, t.stores = [e]) : (n = t.stores, n === null ? t.stores = [e] : n.push(e));
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
			return !Pr(e, n);
		} catch (e) {
			return !0;
		}
	}
	function Zo(e) {
		var t = io(e, 1);
		t !== null && xl(t, e, 1, -1);
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
		}, t.queue = e, e = e.dispatch = gs.bind(null, H, e), [t.memoizedState, e];
	}
	function $o(e, t, n, r) {
		return e = {
			tag: e,
			create: t,
			destroy: n,
			deps: r,
			next: null
		}, t = H.updateQueue, t === null ? (t = {
			lastEffect: null,
			stores: null
		}, H.updateQueue = t, t.lastEffect = e.next = e) : (n = t.lastEffect, n === null ? t.lastEffect = e.next = e : (r = n.next, n.next = e, e.next = r, t.lastEffect = e)), e;
	}
	function es() {
		return Vo().memoizedState;
	}
	function ts(e, t, n, r) {
		var i = Bo();
		H.flags |= e, i.memoizedState = $o(1 | t, n, void 0, r === void 0 ? null : r);
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
		H.flags |= e, i.memoizedState = $o(1 | t, n, a, r);
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
		return ko & 21 ? (Pr(n, t) || (n = Ht(), H.lanes |= n, nl |= n, e.baseState = !0), t) : (e.baseState && (e.baseState = !1, Bs = !0), e.memoizedState = n);
	}
	function ps(e, t) {
		var n = F;
		F = n !== 0 && 4 > n ? n : 4, e(!0);
		var r = Oo.transition;
		Oo.transition = {};
		try {
			e(!1), t();
		} finally {
			F = n, Oo.transition = r;
		}
	}
	function ms() {
		return Vo().memoizedState;
	}
	function hs(e, t, n) {
		var r = bl(e);
		if (n = {
			lane: r,
			action: n,
			hasEagerState: !1,
			eagerState: null,
			next: null
		}, _s(e)) vs(t, n);
		else if (n = B(e, t, n, r), n !== null) {
			var i = yl();
			xl(n, e, r, i), ys(n, t, r);
		}
	}
	function gs(e, t, n) {
		var r = bl(e), i = {
			lane: r,
			action: n,
			hasEagerState: !1,
			eagerState: null,
			next: null
		};
		if (_s(e)) vs(t, i);
		else {
			var a = e.alternate;
			if (e.lanes === 0 && (a === null || a.lanes === 0) && (a = t.lastRenderedReducer, a !== null)) try {
				var o = t.lastRenderedState, s = a(o, n);
				if (i.hasEagerState = !0, i.eagerState = s, Pr(s, o)) {
					var c = t.interleaved;
					c === null ? (i.next = i, ro(t)) : (i.next = c.next, c.next = i), t.interleaved = i;
					return;
				}
			} catch (e) {}
			n = B(e, t, i, r), n !== null && (i = yl(), xl(n, e, r, i), ys(n, t, r));
		}
	}
	function _s(e) {
		var t = e.alternate;
		return e === H || t !== null && t === H;
	}
	function vs(e, t) {
		No = Mo = !0;
		var n = e.pending;
		n === null ? t.next = t : (t.next = n.next, n.next = t), e.pending = t;
	}
	function ys(e, t, n) {
		if (n & 4194240) {
			var r = t.lanes;
			r &= e.pendingLanes, n |= r, t.lanes = n, Kt(e, n);
		}
	}
	var bs = {
		readContext: to,
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
	}, xs = {
		readContext: to,
		useCallback: function(e, t) {
			return Bo().memoizedState = [e, t === void 0 ? null : t], e;
		},
		useContext: to,
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
			}, r.queue = e, e = e.dispatch = hs.bind(null, H, e), [r.memoizedState, e];
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
			var i = H, a = Bo();
			if (ka) {
				if (n === void 0) throw Error(r(407));
				n = n();
			} else {
				if (n = t(), Yc === null) throw Error(r(349));
				ko & 30 || qo(i, t, n);
			}
			a.memoizedState = n;
			var o = {
				value: n,
				getSnapshot: t
			};
			return a.queue = o, rs(Yo.bind(null, i, o, e), [e]), i.flags |= 2048, $o(9, Jo.bind(null, i, o, n, t), void 0, null), n;
		},
		useId: function() {
			var e = Bo(), t = Yc.identifierPrefix;
			if (ka) {
				var n = Sa, r = xa;
				n = (r & ~(1 << 32 - jt(r) - 1)).toString(32) + n, t = ":" + t + "R" + n, n = Po++, 0 < n && (t += "H" + n.toString(32)), t += ":";
			} else n = Fo++, t = ":" + t + "r" + n.toString(32) + ":";
			return e.memoizedState = t;
		},
		unstable_isNewReconciler: !1
	}, Ss = {
		readContext: to,
		useCallback: us,
		useContext: to,
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
	}, Cs = {
		readContext: to,
		useCallback: us,
		useContext: to,
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
	function ws(e, t) {
		if (e && e.defaultProps) {
			for (var n in t = ie({}, t), e = e.defaultProps, e) t[n] === void 0 && (t[n] = e[n]);
			return t;
		}
		return t;
	}
	function U(e, t, n, r) {
		t = e.memoizedState, n = n(r, t), n = n == null ? t : ie({}, t, n), e.memoizedState = n, e.lanes === 0 && (e.updateQueue.baseState = n);
	}
	var Ts = {
		isMounted: function(e) {
			return (e = e._reactInternals) ? dt(e) === e : !1;
		},
		enqueueSetState: function(e, t, n) {
			e = e._reactInternals;
			var r = yl(), i = bl(e), a = co(r, i);
			a.payload = t, n != null && (a.callback = n), t = lo(e, a, i), t !== null && (xl(t, e, i, r), uo(t, e, i));
		},
		enqueueReplaceState: function(e, t, n) {
			e = e._reactInternals;
			var r = yl(), i = bl(e), a = co(r, i);
			a.tag = 1, a.payload = t, n != null && (a.callback = n), t = lo(e, a, i), t !== null && (xl(t, e, i, r), uo(t, e, i));
		},
		enqueueForceUpdate: function(e, t) {
			e = e._reactInternals;
			var n = yl(), r = bl(e), i = co(n, r);
			i.tag = 2, t != null && (i.callback = t), t = lo(e, i, r), t !== null && (xl(t, e, r, n), uo(t, e, r));
		}
	};
	function Es(e, t, n, r, i, a, o) {
		return e = e.stateNode, typeof e.shouldComponentUpdate == "function" ? e.shouldComponentUpdate(r, a, o) : t.prototype && t.prototype.isPureReactComponent ? !Fr(n, r) || !Fr(i, a) : !0;
	}
	function Ds(e, t, n) {
		var r = !1, i = Zi, a = t.contextType;
		return typeof a == "object" && a ? a = to(a) : (i = na(t) ? ea : Qi.current, r = t.contextTypes, a = (r = r != null) ? ta(e, i) : Zi), t = new t(n, a), e.memoizedState = t.state !== null && t.state !== void 0 ? t.state : null, t.updater = Ts, e.stateNode = t, t._reactInternals = e, r && (e = e.stateNode, e.__reactInternalMemoizedUnmaskedChildContext = i, e.__reactInternalMemoizedMaskedChildContext = a), t;
	}
	function Os(e, t, n, r) {
		e = t.state, typeof t.componentWillReceiveProps == "function" && t.componentWillReceiveProps(n, r), typeof t.UNSAFE_componentWillReceiveProps == "function" && t.UNSAFE_componentWillReceiveProps(n, r), t.state !== e && Ts.enqueueReplaceState(t, t.state, null);
	}
	function ks(e, t, n, r) {
		var i = e.stateNode;
		i.props = n, i.state = e.memoizedState, i.refs = {}, oo(e);
		var a = t.contextType;
		typeof a == "object" && a ? i.context = to(a) : (a = na(t) ? ea : Qi.current, i.context = ta(e, a)), i.state = e.memoizedState, a = t.getDerivedStateFromProps, typeof a == "function" && (U(e, t, a, n), i.state = e.memoizedState), typeof t.getDerivedStateFromProps == "function" || typeof i.getSnapshotBeforeUpdate == "function" || typeof i.UNSAFE_componentWillMount != "function" && typeof i.componentWillMount != "function" || (t = i.state, typeof i.componentWillMount == "function" && i.componentWillMount(), typeof i.UNSAFE_componentWillMount == "function" && i.UNSAFE_componentWillMount(), t !== i.state && Ts.enqueueReplaceState(i, i.state, null), po(e, n, i, r), i.state = e.memoizedState), typeof i.componentDidMount == "function" && (e.flags |= 4194308);
	}
	function As(e, t) {
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
	function js(e, t, n) {
		return {
			value: e,
			source: null,
			stack: n == null ? null : n,
			digest: t == null ? null : t
		};
	}
	function Ms(e, t) {
		try {
			console.error(t.value);
		} catch (e) {
			setTimeout(function() {
				throw e;
			});
		}
	}
	var Ns = typeof WeakMap == "function" ? WeakMap : Map;
	function Ps(e, t, n) {
		n = co(-1, n), n.tag = 3, n.payload = { element: null };
		var r = t.value;
		return n.callback = function() {
			ll || (ll = !0, ul = r), Ms(e, t);
		}, n;
	}
	function Fs(e, t, n) {
		n = co(-1, n), n.tag = 3;
		var r = e.type.getDerivedStateFromError;
		if (typeof r == "function") {
			var i = t.value;
			n.payload = function() {
				return r(i);
			}, n.callback = function() {
				Ms(e, t);
			};
		}
		var a = e.stateNode;
		return a !== null && typeof a.componentDidCatch == "function" && (n.callback = function() {
			Ms(e, t), typeof r != "function" && (dl === null ? dl = /* @__PURE__ */ new Set([this]) : dl.add(this));
			var n = t.stack;
			this.componentDidCatch(t.value, { componentStack: n === null ? "" : n });
		}), n;
	}
	function Is(e, t, n) {
		var r = e.pingCache;
		if (r === null) {
			r = e.pingCache = new Ns();
			var i = /* @__PURE__ */ new Set();
			r.set(t, i);
		} else i = r.get(t), i === void 0 && (i = /* @__PURE__ */ new Set(), r.set(t, i));
		i.has(n) || (i.add(n), e = Kl.bind(null, e, t, n), t.then(e, e));
	}
	function Ls(e) {
		do {
			var t;
			if ((t = e.tag === 13) && (t = e.memoizedState, t = t === null || t.dehydrated !== null), t) return e;
			e = e.return;
		} while (e !== null);
		return null;
	}
	function Rs(e, t, n, r, i) {
		return e.mode & 1 ? (e.flags |= 65536, e.lanes = i, e) : (e === t ? e.flags |= 65536 : (e.flags |= 128, n.flags |= 131072, n.flags &= -52805, n.tag === 1 && (n.alternate === null ? n.tag = 17 : (t = co(-1, 1), t.tag = 2, lo(n, t, 1))), n.lanes |= 1), e);
	}
	var zs = C.ReactCurrentOwner, Bs = !1;
	function Vs(e, t, n, r) {
		t.child = e === null ? Ka(t, null, n, r) : Ga(t, e.child, n, r);
	}
	function Hs(e, t, n, r, i) {
		n = n.render;
		var a = t.ref;
		return eo(t, i), r = Ro(e, t, n, r, a, i), n = zo(), e !== null && !Bs ? (t.updateQueue = e.updateQueue, t.flags &= -2053, e.lanes &= ~i, cc(e, t, i)) : (ka && n && Ta(t), t.flags |= 1, Vs(e, t, r, i), t.child);
	}
	function Us(e, t, n, r, i) {
		if (e === null) {
			var a = n.type;
			return typeof a == "function" && !eu(a) && a.defaultProps === void 0 && n.compare === null && n.defaultProps === void 0 ? (t.tag = 15, t.type = a, Ws(e, t, a, r, i)) : (e = ru(n.type, null, r, t, t.mode, i), e.ref = t.ref, e.return = t, t.child = e);
		}
		if (a = e.child, (e.lanes & i) === 0) {
			var o = a.memoizedProps;
			if (n = n.compare, n = n === null ? Fr : n, n(o, r) && e.ref === t.ref) return cc(e, t, i);
		}
		return t.flags |= 1, e = nu(a, r), e.ref = t.ref, e.return = t, t.child = e;
	}
	function Ws(e, t, n, r, i) {
		if (e !== null) {
			var a = e.memoizedProps;
			if (Fr(a, r) && e.ref === t.ref) if (Bs = !1, t.pendingProps = r = a, (e.lanes & i) !== 0) e.flags & 131072 && (Bs = !0);
			else return t.lanes = e.lanes, cc(e, t, i);
		}
		return qs(e, t, n, r, i);
	}
	function Gs(e, t, n) {
		var r = t.pendingProps, i = r.children, a = e === null ? null : e.memoizedState;
		if (r.mode === "hidden") if (!(t.mode & 1)) t.memoizedState = {
			baseLanes: 0,
			cachePool: null,
			transitions: null
		}, Xi($c, Qc), Qc |= n;
		else {
			if (!(n & 1073741824)) return e = a === null ? n : a.baseLanes | n, t.lanes = t.childLanes = 1073741824, t.memoizedState = {
				baseLanes: e,
				cachePool: null,
				transitions: null
			}, t.updateQueue = null, Xi($c, Qc), Qc |= e, null;
			t.memoizedState = {
				baseLanes: 0,
				cachePool: null,
				transitions: null
			}, r = a === null ? n : a.baseLanes, Xi($c, Qc), Qc |= r;
		}
		else a === null ? r = n : (r = a.baseLanes | n, t.memoizedState = null), Xi($c, Qc), Qc |= r;
		return Vs(e, t, i, n), t.child;
	}
	function Ks(e, t) {
		var n = t.ref;
		(e === null && n !== null || e !== null && e.ref !== n) && (t.flags |= 512, t.flags |= 2097152);
	}
	function qs(e, t, n, r, i) {
		var a = na(n) ? ea : Qi.current;
		return a = ta(t, a), eo(t, i), n = Ro(e, t, n, r, a, i), r = zo(), e !== null && !Bs ? (t.updateQueue = e.updateQueue, t.flags &= -2053, e.lanes &= ~i, cc(e, t, i)) : (ka && r && Ta(t), t.flags |= 1, Vs(e, t, n, i), t.child);
	}
	function Js(e, t, n, r, i) {
		if (na(n)) {
			var a = !0;
			oa(t);
		} else a = !1;
		if (eo(t, i), t.stateNode === null) sc(e, t), Ds(t, n, r), ks(t, n, r, i), r = !0;
		else if (e === null) {
			var o = t.stateNode, s = t.memoizedProps;
			o.props = s;
			var c = o.context, l = n.contextType;
			typeof l == "object" && l ? l = to(l) : (l = na(n) ? ea : Qi.current, l = ta(t, l));
			var u = n.getDerivedStateFromProps, d = typeof u == "function" || typeof o.getSnapshotBeforeUpdate == "function";
			d || typeof o.UNSAFE_componentWillReceiveProps != "function" && typeof o.componentWillReceiveProps != "function" || (s !== r || c !== l) && Os(t, o, r, l), ao = !1;
			var f = t.memoizedState;
			o.state = f, po(t, r, o, i), c = t.memoizedState, s !== r || f !== c || $i.current || ao ? (typeof u == "function" && (U(t, n, u, r), c = t.memoizedState), (s = ao || Es(t, n, s, r, f, c, l)) ? (d || typeof o.UNSAFE_componentWillMount != "function" && typeof o.componentWillMount != "function" || (typeof o.componentWillMount == "function" && o.componentWillMount(), typeof o.UNSAFE_componentWillMount == "function" && o.UNSAFE_componentWillMount()), typeof o.componentDidMount == "function" && (t.flags |= 4194308)) : (typeof o.componentDidMount == "function" && (t.flags |= 4194308), t.memoizedProps = r, t.memoizedState = c), o.props = r, o.state = c, o.context = l, r = s) : (typeof o.componentDidMount == "function" && (t.flags |= 4194308), r = !1);
		} else {
			o = t.stateNode, so(e, t), s = t.memoizedProps, l = t.type === t.elementType ? s : ws(t.type, s), o.props = l, d = t.pendingProps, f = o.context, c = n.contextType, typeof c == "object" && c ? c = to(c) : (c = na(n) ? ea : Qi.current, c = ta(t, c));
			var p = n.getDerivedStateFromProps;
			(u = typeof p == "function" || typeof o.getSnapshotBeforeUpdate == "function") || typeof o.UNSAFE_componentWillReceiveProps != "function" && typeof o.componentWillReceiveProps != "function" || (s !== d || f !== c) && Os(t, o, r, c), ao = !1, f = t.memoizedState, o.state = f, po(t, r, o, i);
			var m = t.memoizedState;
			s !== d || f !== m || $i.current || ao ? (typeof p == "function" && (U(t, n, p, r), m = t.memoizedState), (l = ao || Es(t, n, l, r, f, m, c) || !1) ? (u || typeof o.UNSAFE_componentWillUpdate != "function" && typeof o.componentWillUpdate != "function" || (typeof o.componentWillUpdate == "function" && o.componentWillUpdate(r, m, c), typeof o.UNSAFE_componentWillUpdate == "function" && o.UNSAFE_componentWillUpdate(r, m, c)), typeof o.componentDidUpdate == "function" && (t.flags |= 4), typeof o.getSnapshotBeforeUpdate == "function" && (t.flags |= 1024)) : (typeof o.componentDidUpdate != "function" || s === e.memoizedProps && f === e.memoizedState || (t.flags |= 4), typeof o.getSnapshotBeforeUpdate != "function" || s === e.memoizedProps && f === e.memoizedState || (t.flags |= 1024), t.memoizedProps = r, t.memoizedState = m), o.props = r, o.state = m, o.context = c, r = l) : (typeof o.componentDidUpdate != "function" || s === e.memoizedProps && f === e.memoizedState || (t.flags |= 4), typeof o.getSnapshotBeforeUpdate != "function" || s === e.memoizedProps && f === e.memoizedState || (t.flags |= 1024), r = !1);
		}
		return Ys(e, t, n, r, a, i);
	}
	function Ys(e, t, n, r, i, a) {
		Ks(e, t);
		var o = (t.flags & 128) != 0;
		if (!r && !o) return i && sa(t, n, !1), cc(e, t, a);
		r = t.stateNode, zs.current = t;
		var s = o && typeof n.getDerivedStateFromError != "function" ? null : r.render();
		return t.flags |= 1, e !== null && o ? (t.child = Ga(t, e.child, null, a), t.child = Ga(t, null, s, a)) : Vs(e, t, s, a), t.memoizedState = r.state, i && sa(t, n, !0), t.child;
	}
	function Xs(e) {
		var t = e.stateNode;
		t.pendingContext ? ia(e, t.pendingContext, t.pendingContext !== t.context) : t.context && ia(e, t.context, !1), yo(e, t.containerInfo);
	}
	function Zs(e, t, n, r, i) {
		return Ra(), za(i), t.flags |= 256, Vs(e, t, n, r), t.child;
	}
	var Qs = {
		dehydrated: null,
		treeContext: null,
		retryLane: 0
	};
	function $s(e) {
		return {
			baseLanes: e,
			cachePool: null,
			transitions: null
		};
	}
	function ec(e, t, n) {
		var r = t.pendingProps, i = Co.current, a = !1, o = (t.flags & 128) != 0, s;
		if ((s = o) || (s = e !== null && e.memoizedState === null ? !1 : (i & 2) != 0), s ? (a = !0, t.flags &= -129) : (e === null || e.memoizedState !== null) && (i |= 1), Xi(Co, i & 1), e === null) return Pa(t), e = t.memoizedState, e !== null && (e = e.dehydrated, e !== null) ? (t.mode & 1 ? e.data === "$!" ? t.lanes = 8 : t.lanes = 1073741824 : t.lanes = 1, null) : (o = r.children, e = r.fallback, a ? (r = t.mode, a = t.child, o = {
			mode: "hidden",
			children: o
		}, !(r & 1) && a !== null ? (a.childLanes = 0, a.pendingProps = o) : a = au(o, r, 0, null), e = iu(e, r, n, null), a.return = t, e.return = t, a.sibling = e, t.child = a, t.child.memoizedState = $s(n), t.memoizedState = Qs, e) : tc(t, o));
		if (i = e.memoizedState, i !== null && (s = i.dehydrated, s !== null)) return rc(e, t, o, r, s, i, n);
		if (a) {
			a = r.fallback, o = t.mode, i = e.child, s = i.sibling;
			var c = {
				mode: "hidden",
				children: r.children
			};
			return !(o & 1) && t.child !== i ? (r = t.child, r.childLanes = 0, r.pendingProps = c, t.deletions = null) : (r = nu(i, c), r.subtreeFlags = i.subtreeFlags & 14680064), s === null ? (a = iu(a, o, n, null), a.flags |= 2) : a = nu(s, a), a.return = t, r.return = t, r.sibling = a, t.child = r, r = a, a = t.child, o = e.child.memoizedState, o = o === null ? $s(n) : {
				baseLanes: o.baseLanes | n,
				cachePool: null,
				transitions: o.transitions
			}, a.memoizedState = o, a.childLanes = e.childLanes & ~n, t.memoizedState = Qs, r;
		}
		return a = e.child, e = a.sibling, r = nu(a, {
			mode: "visible",
			children: r.children
		}), !(t.mode & 1) && (r.lanes = n), r.return = t, r.sibling = null, e !== null && (n = t.deletions, n === null ? (t.deletions = [e], t.flags |= 16) : n.push(e)), t.child = r, t.memoizedState = null, r;
	}
	function tc(e, t) {
		return t = au({
			mode: "visible",
			children: t
		}, e.mode, 0, null), t.return = e, e.child = t;
	}
	function nc(e, t, n, r) {
		return r !== null && za(r), Ga(t, e.child, null, n), e = tc(t, t.pendingProps.children), e.flags |= 2, t.memoizedState = null, e;
	}
	function rc(e, t, n, i, a, o, s) {
		if (n) return t.flags & 256 ? (t.flags &= -257, i = js(Error(r(422))), nc(e, t, s, i)) : t.memoizedState === null ? (o = i.fallback, a = t.mode, i = au({
			mode: "visible",
			children: i.children
		}, a, 0, null), o = iu(o, a, s, null), o.flags |= 2, i.return = t, o.return = t, i.sibling = o, t.child = i, t.mode & 1 && Ga(t, e.child, null, s), t.child.memoizedState = $s(s), t.memoizedState = Qs, o) : (t.child = e.child, t.flags |= 128, null);
		if (!(t.mode & 1)) return nc(e, t, s, null);
		if (a.data === "$!") {
			if (i = a.nextSibling && a.nextSibling.dataset, i) var c = i.dgst;
			return i = c, o = Error(r(419)), i = js(o, i, void 0), nc(e, t, s, i);
		}
		if (c = (s & e.childLanes) !== 0, Bs || c) {
			if (i = Yc, i !== null) {
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
				a = (a & (i.suspendedLanes | s)) === 0 ? a : 0, a !== 0 && a !== o.retryLane && (o.retryLane = a, io(e, a), xl(i, e, a, -1));
			}
			return Fl(), i = js(Error(r(421))), nc(e, t, s, i);
		}
		return a.data === "$?" ? (t.flags |= 128, t.child = e.child, t = Jl.bind(null, e), a._reactRetry = t, null) : (e = o.treeContext, Oa = Pi(a.nextSibling), Da = t, ka = !0, Aa = null, e !== null && (va[ya++] = xa, va[ya++] = Sa, va[ya++] = ba, xa = e.id, Sa = e.overflow, ba = t), t = tc(t, i.children), t.flags |= 4096, t);
	}
	function ic(e, t, n) {
		e.lanes |= t;
		var r = e.alternate;
		r !== null && (r.lanes |= t), $a(e.return, t, n);
	}
	function ac(e, t, n, r, i) {
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
	function oc(e, t, n) {
		var r = t.pendingProps, i = r.revealOrder, a = r.tail;
		if (Vs(e, t, r.children, n), r = Co.current, r & 2) r = r & 1 | 2, t.flags |= 128;
		else {
			if (e !== null && e.flags & 128) a: for (e = t.child; e !== null;) {
				if (e.tag === 13) e.memoizedState !== null && ic(e, n, t);
				else if (e.tag === 19) ic(e, n, t);
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
		if (Xi(Co, r), !(t.mode & 1)) t.memoizedState = null;
		else switch (i) {
			case "forwards":
				for (n = t.child, i = null; n !== null;) e = n.alternate, e !== null && wo(e) === null && (i = n), n = n.sibling;
				n = i, n === null ? (i = t.child, t.child = null) : (i = n.sibling, n.sibling = null), ac(t, !1, i, n, a);
				break;
			case "backwards":
				for (n = null, i = t.child, t.child = null; i !== null;) {
					if (e = i.alternate, e !== null && wo(e) === null) {
						t.child = i;
						break;
					}
					e = i.sibling, i.sibling = n, n = i, i = e;
				}
				ac(t, !0, n, null, a);
				break;
			case "together":
				ac(t, !1, null, null, void 0);
				break;
			default: t.memoizedState = null;
		}
		return t.child;
	}
	function sc(e, t) {
		!(t.mode & 1) && e !== null && (e.alternate = null, t.alternate = null, t.flags |= 2);
	}
	function cc(e, t, n) {
		if (e !== null && (t.dependencies = e.dependencies), nl |= t.lanes, (n & t.childLanes) === 0) return null;
		if (e !== null && t.child !== e.child) throw Error(r(153));
		if (t.child !== null) {
			for (e = t.child, n = nu(e, e.pendingProps), t.child = n, n.return = t; e.sibling !== null;) e = e.sibling, n = n.sibling = nu(e, e.pendingProps), n.return = t;
			n.sibling = null;
		}
		return t.child;
	}
	function lc(e, t, n) {
		switch (t.tag) {
			case 3:
				Xs(t), Ra();
				break;
			case 5:
				xo(t);
				break;
			case 1:
				na(t.type) && oa(t);
				break;
			case 4:
				yo(t, t.stateNode.containerInfo);
				break;
			case 10:
				var r = t.type._context, i = t.memoizedProps.value;
				Xi(qa, r._currentValue), r._currentValue = i;
				break;
			case 13:
				if (r = t.memoizedState, r !== null) return r.dehydrated === null ? (n & t.child.childLanes) === 0 ? (Xi(Co, Co.current & 1), e = cc(e, t, n), e === null ? null : e.sibling) : ec(e, t, n) : (Xi(Co, Co.current & 1), t.flags |= 128, null);
				Xi(Co, Co.current & 1);
				break;
			case 19:
				if (r = (n & t.childLanes) !== 0, e.flags & 128) {
					if (r) return oc(e, t, n);
					t.flags |= 128;
				}
				if (i = t.memoizedState, i !== null && (i.rendering = null, i.tail = null, i.lastEffect = null), Xi(Co, Co.current), r) break;
				return null;
			case 22:
			case 23: return t.lanes = 0, Gs(e, t, n);
		}
		return cc(e, t, n);
	}
	var uc = function(e, t) {
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
	}, dc = function(e, t, n, r) {
		var i = e.memoizedProps;
		if (i !== r) {
			e = t.stateNode, vo(V.current);
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
	}, fc = function(e, t, n, r) {
		n !== r && (t.flags |= 4);
	};
	function pc(e, t) {
		if (!ka) switch (e.tailMode) {
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
	function mc(e) {
		var t = e.alternate !== null && e.alternate.child === e.child, n = 0, r = 0;
		if (t) for (var i = e.child; i !== null;) n |= i.lanes | i.childLanes, r |= i.subtreeFlags & 14680064, r |= i.flags & 14680064, i.return = e, i = i.sibling;
		else for (i = e.child; i !== null;) n |= i.lanes | i.childLanes, r |= i.subtreeFlags, r |= i.flags, i.return = e, i = i.sibling;
		return e.subtreeFlags |= r, e.childLanes = n, t;
	}
	function hc(e, t, n) {
		var i = t.pendingProps;
		switch (Ea(t), t.tag) {
			case 2:
			case 16:
			case 15:
			case 0:
			case 11:
			case 7:
			case 8:
			case 12:
			case 9:
			case 14: return mc(t), null;
			case 1: return na(t.type) && ra(), mc(t), null;
			case 3: return i = t.stateNode, bo(), z($i), z(Qi), Eo(), i.pendingContext && (i.context = i.pendingContext, i.pendingContext = null), (e === null || e.child === null) && (Ia(t) ? t.flags |= 4 : e === null || e.memoizedState.isDehydrated && !(t.flags & 256) || (t.flags |= 1024, Aa !== null && (Tl(Aa), Aa = null))), mc(t), null;
			case 5:
				So(t);
				var o = vo(_o.current);
				if (n = t.type, e !== null && t.stateNode != null) dc(e, t, n, i, o), e.ref !== t.ref && (t.flags |= 512, t.flags |= 2097152);
				else {
					if (!i) {
						if (t.stateNode === null) throw Error(r(166));
						return mc(t), null;
					}
					if (e = vo(V.current), Ia(t)) {
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
						c = o.nodeType === 9 ? o : o.ownerDocument, e === "http://www.w3.org/1999/xhtml" && (e = Ae(n)), e === "http://www.w3.org/1999/xhtml" ? n === "script" ? (e = c.createElement("div"), e.innerHTML = "<script><\/script>", e = e.removeChild(e.firstChild)) : typeof i.is == "string" ? e = c.createElement(n, { is: i.is }) : (e = c.createElement(n), n === "select" && (c = e, i.multiple ? c.multiple = !0 : i.size && (c.size = i.size))) : e = c.createElementNS(e, n), e[Li] = t, e[Ri] = i, uc(e, t, !1, !1), t.stateNode = e;
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
				return mc(t), null;
			case 6:
				if (e && t.stateNode != null) fc(e, t, e.memoizedProps, i);
				else {
					if (typeof i != "string" && t.stateNode === null) throw Error(r(166));
					if (n = vo(_o.current), vo(V.current), Ia(t)) {
						if (i = t.stateNode, n = t.memoizedProps, i[Li] = t, (s = i.nodeValue !== n) && (e = Da, e !== null)) switch (e.tag) {
							case 3:
								Ci(i.nodeValue, n, (e.mode & 1) != 0);
								break;
							case 5: !0 !== e.memoizedProps.suppressHydrationWarning && Ci(i.nodeValue, n, (e.mode & 1) != 0);
						}
						s && (t.flags |= 4);
					} else i = (n.nodeType === 9 ? n : n.ownerDocument).createTextNode(i), i[Li] = t, t.stateNode = i;
				}
				return mc(t), null;
			case 13:
				if (z(Co), i = t.memoizedState, e === null || e.memoizedState !== null && e.memoizedState.dehydrated !== null) {
					if (ka && Oa !== null && t.mode & 1 && !(t.flags & 128)) La(), Ra(), t.flags |= 98560, s = !1;
					else if (s = Ia(t), i !== null && i.dehydrated !== null) {
						if (e === null) {
							if (!s) throw Error(r(318));
							if (s = t.memoizedState, s = s === null ? null : s.dehydrated, !s) throw Error(r(317));
							s[Li] = t;
						} else Ra(), !(t.flags & 128) && (t.memoizedState = null), t.flags |= 4;
						mc(t), s = !1;
					} else Aa !== null && (Tl(Aa), Aa = null), s = !0;
					if (!s) return t.flags & 65536 ? t : null;
				}
				return t.flags & 128 ? (t.lanes = n, t) : (i = i !== null, i !== (e !== null && e.memoizedState !== null) && i && (t.child.flags |= 8192, t.mode & 1 && (e === null || Co.current & 1 ? el === 0 && (el = 3) : Fl())), t.updateQueue !== null && (t.flags |= 4), mc(t), null);
			case 4: return bo(), e === null && pi(t.stateNode.containerInfo), mc(t), null;
			case 10: return Qa(t.type._context), mc(t), null;
			case 17: return na(t.type) && ra(), mc(t), null;
			case 19:
				if (z(Co), s = t.memoizedState, s === null) return mc(t), null;
				if (i = (t.flags & 128) != 0, c = s.rendering, c === null) if (i) pc(s, !1);
				else {
					if (el !== 0 || e !== null && e.flags & 128) for (e = t.child; e !== null;) {
						if (c = wo(e), c !== null) {
							for (t.flags |= 128, pc(s, !1), i = c.updateQueue, i !== null && (t.updateQueue = i, t.flags |= 4), t.subtreeFlags = 0, i = n, n = t.child; n !== null;) s = n, e = i, s.flags &= 14680066, c = s.alternate, c === null ? (s.childLanes = 0, s.lanes = e, s.child = null, s.subtreeFlags = 0, s.memoizedProps = null, s.memoizedState = null, s.updateQueue = null, s.dependencies = null, s.stateNode = null) : (s.childLanes = c.childLanes, s.lanes = c.lanes, s.child = c.child, s.subtreeFlags = 0, s.deletions = null, s.memoizedProps = c.memoizedProps, s.memoizedState = c.memoizedState, s.updateQueue = c.updateQueue, s.type = c.type, e = c.dependencies, s.dependencies = e === null ? null : {
								lanes: e.lanes,
								firstContext: e.firstContext
							}), n = n.sibling;
							return Xi(Co, Co.current & 1 | 2), t.child;
						}
						e = e.sibling;
					}
					s.tail !== null && xt() > sl && (t.flags |= 128, i = !0, pc(s, !1), t.lanes = 4194304);
				}
				else {
					if (!i) if (e = wo(c), e !== null) {
						if (t.flags |= 128, i = !0, n = e.updateQueue, n !== null && (t.updateQueue = n, t.flags |= 4), pc(s, !0), s.tail === null && s.tailMode === "hidden" && !c.alternate && !ka) return mc(t), null;
					} else 2 * xt() - s.renderingStartTime > sl && n !== 1073741824 && (t.flags |= 128, i = !0, pc(s, !1), t.lanes = 4194304);
					s.isBackwards ? (c.sibling = t.child, t.child = c) : (n = s.last, n === null ? t.child = c : n.sibling = c, s.last = c);
				}
				return s.tail === null ? (mc(t), null) : (t = s.tail, s.rendering = t, s.tail = t.sibling, s.renderingStartTime = xt(), t.sibling = null, n = Co.current, Xi(Co, i ? n & 1 | 2 : n & 1), t);
			case 22:
			case 23: return jl(), i = t.memoizedState !== null, e !== null && e.memoizedState !== null !== i && (t.flags |= 8192), i && t.mode & 1 ? Qc & 1073741824 && (mc(t), t.subtreeFlags & 6 && (t.flags |= 8192)) : mc(t), null;
			case 24: return null;
			case 25: return null;
		}
		throw Error(r(156, t.tag));
	}
	function gc(e, t) {
		switch (Ea(t), t.tag) {
			case 1: return na(t.type) && ra(), e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
			case 3: return bo(), z($i), z(Qi), Eo(), e = t.flags, e & 65536 && !(e & 128) ? (t.flags = e & -65537 | 128, t) : null;
			case 5: return So(t), null;
			case 13:
				if (z(Co), e = t.memoizedState, e !== null && e.dehydrated !== null) {
					if (t.alternate === null) throw Error(r(340));
					Ra();
				}
				return e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
			case 19: return z(Co), null;
			case 4: return bo(), null;
			case 10: return Qa(t.type._context), null;
			case 22:
			case 23: return jl(), null;
			case 24: return null;
			default: return null;
		}
	}
	var _c = !1, vc = !1, yc = typeof WeakSet == "function" ? WeakSet : Set, W = null;
	function bc(e, t) {
		var n = e.ref;
		if (n !== null) if (typeof n == "function") try {
			n(null);
		} catch (n) {
			Gl(e, t, n);
		}
		else n.current = null;
	}
	function xc(e, t, n) {
		try {
			n();
		} catch (n) {
			Gl(e, t, n);
		}
	}
	var Sc = !1;
	function Cc(e, t) {
		if (Ti = vn, e = zr(), Br(e)) {
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
		}, vn = !1, W = t; W !== null;) if (t = W, e = t.child, t.subtreeFlags & 1028 && e !== null) e.return = t, W = e;
		else for (; W !== null;) {
			t = W;
			try {
				var h = t.alternate;
				if (t.flags & 1024) switch (t.tag) {
					case 0:
					case 11:
					case 15: break;
					case 1:
						if (h !== null) {
							var g = h.memoizedProps, _ = h.memoizedState, v = t.stateNode;
							v.__reactInternalSnapshotBeforeUpdate = v.getSnapshotBeforeUpdate(t.elementType === t.type ? g : ws(t.type, g), _);
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
				Gl(t, t.return, e);
			}
			if (e = t.sibling, e !== null) {
				e.return = t.return, W = e;
				break;
			}
			W = t.return;
		}
		return h = Sc, Sc = !1, h;
	}
	function wc(e, t, n) {
		var r = t.updateQueue;
		if (r = r === null ? null : r.lastEffect, r !== null) {
			var i = r = r.next;
			do {
				if ((i.tag & e) === e) {
					var a = i.destroy;
					i.destroy = void 0, a !== void 0 && xc(t, n, a);
				}
				i = i.next;
			} while (i !== r);
		}
	}
	function Tc(e, t) {
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
	function Ec(e) {
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
	function Dc(e) {
		var t = e.alternate;
		t !== null && (e.alternate = null, Dc(t)), e.child = null, e.deletions = null, e.sibling = null, e.tag === 5 && (t = e.stateNode, t !== null && (delete t[Li], delete t[Ri], delete t[Bi], delete t[Vi], delete t[Hi])), e.stateNode = null, e.return = null, e.dependencies = null, e.memoizedProps = null, e.memoizedState = null, e.pendingProps = null, e.stateNode = null, e.updateQueue = null;
	}
	function Oc(e) {
		return e.tag === 5 || e.tag === 3 || e.tag === 4;
	}
	function kc(e) {
		a: for (;;) {
			for (; e.sibling === null;) {
				if (e.return === null || Oc(e.return)) return null;
				e = e.return;
			}
			for (e.sibling.return = e.return, e = e.sibling; e.tag !== 5 && e.tag !== 6 && e.tag !== 18;) {
				if (e.flags & 2 || e.child === null || e.tag === 4) continue a;
				e.child.return = e, e = e.child;
			}
			if (!(e.flags & 2)) return e.stateNode;
		}
	}
	function Ac(e, t, n) {
		var r = e.tag;
		if (r === 5 || r === 6) e = e.stateNode, t ? n.nodeType === 8 ? n.parentNode.insertBefore(e, t) : n.insertBefore(e, t) : (n.nodeType === 8 ? (t = n.parentNode, t.insertBefore(e, n)) : (t = n, t.appendChild(e)), n = n._reactRootContainer, n != null || t.onclick !== null || (t.onclick = wi));
		else if (r !== 4 && (e = e.child, e !== null)) for (Ac(e, t, n), e = e.sibling; e !== null;) Ac(e, t, n), e = e.sibling;
	}
	function jc(e, t, n) {
		var r = e.tag;
		if (r === 5 || r === 6) e = e.stateNode, t ? n.insertBefore(e, t) : n.appendChild(e);
		else if (r !== 4 && (e = e.child, e !== null)) for (jc(e, t, n), e = e.sibling; e !== null;) jc(e, t, n), e = e.sibling;
	}
	var Mc = null, Nc = !1;
	function Pc(e, t, n) {
		for (n = n.child; n !== null;) Fc(e, t, n), n = n.sibling;
	}
	function Fc(e, t, n) {
		if (kt && typeof kt.onCommitFiberUnmount == "function") try {
			kt.onCommitFiberUnmount(Ot, n);
		} catch (e) {}
		switch (n.tag) {
			case 5: vc || bc(n, t);
			case 6:
				var r = Mc, i = Nc;
				Mc = null, Pc(e, t, n), Mc = r, Nc = i, Mc !== null && (Nc ? (e = Mc, n = n.stateNode, e.nodeType === 8 ? e.parentNode.removeChild(n) : e.removeChild(n)) : Mc.removeChild(n.stateNode));
				break;
			case 18:
				Mc !== null && (Nc ? (e = Mc, n = n.stateNode, e.nodeType === 8 ? Ni(e.parentNode, n) : e.nodeType === 1 && Ni(e, n), gn(e)) : Ni(Mc, n.stateNode));
				break;
			case 4:
				r = Mc, i = Nc, Mc = n.stateNode.containerInfo, Nc = !0, Pc(e, t, n), Mc = r, Nc = i;
				break;
			case 0:
			case 11:
			case 14:
			case 15:
				if (!vc && (r = n.updateQueue, r !== null && (r = r.lastEffect, r !== null))) {
					i = r = r.next;
					do {
						var a = i, o = a.destroy;
						a = a.tag, o !== void 0 && (a & 2 || a & 4) && xc(n, t, o), i = i.next;
					} while (i !== r);
				}
				Pc(e, t, n);
				break;
			case 1:
				if (!vc && (bc(n, t), r = n.stateNode, typeof r.componentWillUnmount == "function")) try {
					r.props = n.memoizedProps, r.state = n.memoizedState, r.componentWillUnmount();
				} catch (e) {
					Gl(n, t, e);
				}
				Pc(e, t, n);
				break;
			case 21:
				Pc(e, t, n);
				break;
			case 22:
				n.mode & 1 ? (vc = (r = vc) || n.memoizedState !== null, Pc(e, t, n), vc = r) : Pc(e, t, n);
				break;
			default: Pc(e, t, n);
		}
	}
	function Ic(e) {
		var t = e.updateQueue;
		if (t !== null) {
			e.updateQueue = null;
			var n = e.stateNode;
			n === null && (n = e.stateNode = new yc()), t.forEach(function(t) {
				var r = Yl.bind(null, e, t);
				n.has(t) || (n.add(t), t.then(r, r));
			});
		}
	}
	function Lc(e, t) {
		var n = t.deletions;
		if (n !== null) for (var i = 0; i < n.length; i++) {
			var a = n[i];
			try {
				var o = e, s = t, c = s;
				a: for (; c !== null;) {
					switch (c.tag) {
						case 5:
							Mc = c.stateNode, Nc = !1;
							break a;
						case 3:
							Mc = c.stateNode.containerInfo, Nc = !0;
							break a;
						case 4:
							Mc = c.stateNode.containerInfo, Nc = !0;
							break a;
					}
					c = c.return;
				}
				if (Mc === null) throw Error(r(160));
				Fc(o, s, a), Mc = null, Nc = !1;
				var l = a.alternate;
				l !== null && (l.return = null), a.return = null;
			} catch (e) {
				Gl(a, t, e);
			}
		}
		if (t.subtreeFlags & 12854) for (t = t.child; t !== null;) Rc(t, e), t = t.sibling;
	}
	function Rc(e, t) {
		var n = e.alternate, i = e.flags;
		switch (e.tag) {
			case 0:
			case 11:
			case 14:
			case 15:
				if (Lc(t, e), zc(e), i & 4) {
					try {
						wc(3, e, e.return), Tc(3, e);
					} catch (t) {
						Gl(e, e.return, t);
					}
					try {
						wc(5, e, e.return);
					} catch (t) {
						Gl(e, e.return, t);
					}
				}
				break;
			case 1:
				Lc(t, e), zc(e), i & 512 && n !== null && bc(n, n.return);
				break;
			case 5:
				if (Lc(t, e), zc(e), i & 512 && n !== null && bc(n, n.return), e.flags & 32) {
					var a = e.stateNode;
					try {
						Pe(a, "");
					} catch (t) {
						Gl(e, e.return, t);
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
						Gl(e, e.return, t);
					}
				}
				break;
			case 6:
				if (Lc(t, e), zc(e), i & 4) {
					if (e.stateNode === null) throw Error(r(162));
					a = e.stateNode, o = e.memoizedProps;
					try {
						a.nodeValue = o;
					} catch (t) {
						Gl(e, e.return, t);
					}
				}
				break;
			case 3:
				if (Lc(t, e), zc(e), i & 4 && n !== null && n.memoizedState.isDehydrated) try {
					gn(t.containerInfo);
				} catch (t) {
					Gl(e, e.return, t);
				}
				break;
			case 4:
				Lc(t, e), zc(e);
				break;
			case 13:
				Lc(t, e), zc(e), a = e.child, a.flags & 8192 && (o = a.memoizedState !== null, a.stateNode.isHidden = o, !o || a.alternate !== null && a.alternate.memoizedState !== null || (ol = xt())), i & 4 && Ic(e);
				break;
			case 22:
				if (d = n !== null && n.memoizedState !== null, e.mode & 1 ? (vc = (u = vc) || d, Lc(t, e), vc = u) : Lc(t, e), zc(e), i & 8192) {
					if (u = e.memoizedState !== null, (e.stateNode.isHidden = u) && !d && e.mode & 1) for (W = e, d = e.child; d !== null;) {
						for (f = W = d; W !== null;) {
							switch (p = W, m = p.child, p.tag) {
								case 0:
								case 11:
								case 14:
								case 15:
									wc(4, p, p.return);
									break;
								case 1:
									bc(p, p.return);
									var h = p.stateNode;
									if (typeof h.componentWillUnmount == "function") {
										i = p, n = p.return;
										try {
											t = i, h.props = t.memoizedProps, h.state = t.memoizedState, h.componentWillUnmount();
										} catch (e) {
											Gl(i, n, e);
										}
									}
									break;
								case 5:
									bc(p, p.return);
									break;
								case 22: if (p.memoizedState !== null) {
									Uc(f);
									continue;
								}
							}
							m === null ? Uc(f) : (m.return = p, W = m);
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
									Gl(e, e.return, t);
								}
							}
						} else if (f.tag === 6) {
							if (d === null) try {
								f.stateNode.nodeValue = u ? "" : f.memoizedProps;
							} catch (t) {
								Gl(e, e.return, t);
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
				Lc(t, e), zc(e), i & 4 && Ic(e);
				break;
			case 21: break;
			default: Lc(t, e), zc(e);
		}
	}
	function zc(e) {
		var t = e.flags;
		if (t & 2) {
			try {
				a: {
					for (var n = e.return; n !== null;) {
						if (Oc(n)) {
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
						i.flags & 32 && (Pe(a, ""), i.flags &= -33), jc(e, kc(e), a);
						break;
					case 3:
					case 4:
						var o = i.stateNode.containerInfo;
						Ac(e, kc(e), o);
						break;
					default: throw Error(r(161));
				}
			} catch (t) {
				Gl(e, e.return, t);
			}
			e.flags &= -3;
		}
		t & 4096 && (e.flags &= -4097);
	}
	function Bc(e, t, n) {
		W = e, Vc(e, t, n);
	}
	function Vc(e, t, n) {
		for (var r = (e.mode & 1) != 0; W !== null;) {
			var i = W, a = i.child;
			if (i.tag === 22 && r) {
				var o = i.memoizedState !== null || _c;
				if (!o) {
					var s = i.alternate, c = s !== null && s.memoizedState !== null || vc;
					s = _c;
					var l = vc;
					if (_c = o, (vc = c) && !l) for (W = i; W !== null;) o = W, c = o.child, o.tag === 22 && o.memoizedState !== null || c === null ? Wc(i) : (c.return = o, W = c);
					for (; a !== null;) W = a, Vc(a, t, n), a = a.sibling;
					W = i, _c = s, vc = l;
				}
				Hc(e, t, n);
			} else i.subtreeFlags & 8772 && a !== null ? (a.return = i, W = a) : Hc(e, t, n);
		}
	}
	function Hc(e) {
		for (; W !== null;) {
			var t = W;
			if (t.flags & 8772) {
				var n = t.alternate;
				try {
					if (t.flags & 8772) switch (t.tag) {
						case 0:
						case 11:
						case 15:
							vc || Tc(5, t);
							break;
						case 1:
							var i = t.stateNode;
							if (t.flags & 4 && !vc) if (n === null) i.componentDidMount();
							else {
								var a = t.elementType === t.type ? n.memoizedProps : ws(t.type, n.memoizedProps);
								i.componentDidUpdate(a, n.memoizedState, i.__reactInternalSnapshotBeforeUpdate);
							}
							var o = t.updateQueue;
							o !== null && mo(t, o, i);
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
								mo(t, s, n);
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
					vc || t.flags & 512 && Ec(t);
				} catch (e) {
					Gl(t, t.return, e);
				}
			}
			if (t === e) {
				W = null;
				break;
			}
			if (n = t.sibling, n !== null) {
				n.return = t.return, W = n;
				break;
			}
			W = t.return;
		}
	}
	function Uc(e) {
		for (; W !== null;) {
			var t = W;
			if (t === e) {
				W = null;
				break;
			}
			var n = t.sibling;
			if (n !== null) {
				n.return = t.return, W = n;
				break;
			}
			W = t.return;
		}
	}
	function Wc(e) {
		for (; W !== null;) {
			var t = W;
			try {
				switch (t.tag) {
					case 0:
					case 11:
					case 15:
						var n = t.return;
						try {
							Tc(4, t);
						} catch (e) {
							Gl(t, n, e);
						}
						break;
					case 1:
						var r = t.stateNode;
						if (typeof r.componentDidMount == "function") {
							var i = t.return;
							try {
								r.componentDidMount();
							} catch (e) {
								Gl(t, i, e);
							}
						}
						var a = t.return;
						try {
							Ec(t);
						} catch (e) {
							Gl(t, a, e);
						}
						break;
					case 5:
						var o = t.return;
						try {
							Ec(t);
						} catch (e) {
							Gl(t, o, e);
						}
				}
			} catch (e) {
				Gl(t, t.return, e);
			}
			if (t === e) {
				W = null;
				break;
			}
			var s = t.sibling;
			if (s !== null) {
				s.return = t.return, W = s;
				break;
			}
			W = t.return;
		}
	}
	var Gc = Math.ceil, Kc = C.ReactCurrentDispatcher, qc = C.ReactCurrentOwner, Jc = C.ReactCurrentBatchConfig, G = 0, Yc = null, Xc = null, Zc = 0, Qc = 0, $c = Yi(0), el = 0, tl = null, nl = 0, K = 0, rl = 0, il = null, al = null, ol = 0, sl = Infinity, cl = null, ll = !1, ul = null, dl = null, fl = !1, pl = null, ml = 0, hl = 0, gl = null, _l = -1, vl = 0;
	function yl() {
		return G & 6 ? xt() : _l === -1 ? _l = xt() : _l;
	}
	function bl(e) {
		return e.mode & 1 ? G & 2 && Zc !== 0 ? Zc & -Zc : Ba.transition === null ? (e = F, e === 0 ? (e = window.event, e = e === void 0 ? 16 : wn(e.type), e) : e) : (vl === 0 && (vl = Ht()), vl) : 1;
	}
	function xl(e, t, n, i) {
		if (50 < hl) throw hl = 0, gl = null, Error(r(185));
		Wt(e, n, i), (!(G & 2) || e !== Yc) && (e === Yc && (!(G & 2) && (K |= n), el === 4 && Dl(e, Zc)), Sl(e, i), n === 1 && G === 0 && !(t.mode & 1) && (sl = xt() + 500, la && pa()));
	}
	function Sl(e, t) {
		var n = e.callbackNode;
		Bt(e, t);
		var r = Rt(e, e === Yc ? Zc : 0);
		if (r === 0) n !== null && vt(n), e.callbackNode = null, e.callbackPriority = 0;
		else if (t = r & -r, e.callbackPriority !== t) {
			if (n != null && vt(n), t === 1) e.tag === 0 ? fa(Ol.bind(null, e)) : da(Ol.bind(null, e)), ji(function() {
				!(G & 6) && pa();
			}), n = null;
			else {
				switch (qt(r)) {
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
				n = Zl(n, Cl.bind(null, e));
			}
			e.callbackPriority = t, e.callbackNode = n;
		}
	}
	function Cl(e, t) {
		if (_l = -1, vl = 0, G & 6) throw Error(r(327));
		var n = e.callbackNode;
		if (Ul() && e.callbackNode !== n) return null;
		var i = Rt(e, e === Yc ? Zc : 0);
		if (i === 0) return null;
		if (i & 30 || (i & e.expiredLanes) !== 0 || t) t = Il(e, i);
		else {
			t = i;
			var a = G;
			G |= 2;
			var o = Pl();
			(Yc !== e || Zc !== t) && (cl = null, sl = xt() + 500, Ml(e, t));
			do
				try {
					Rl();
					break;
				} catch (t) {
					Nl(e, t);
				}
			while (1);
			Za(), Kc.current = o, G = a, Xc === null ? (Yc = null, Zc = 0, t = el) : t = 0;
		}
		if (t !== 0) {
			if (t === 2 && (a = Vt(e), a !== 0 && (i = a, t = wl(e, a))), t === 1) throw n = tl, Ml(e, 0), Dl(e, i), Sl(e, xt()), n;
			if (t === 6) Dl(e, i);
			else {
				if (a = e.current.alternate, !(i & 30) && !El(a) && (t = Il(e, i), t === 2 && (o = Vt(e), o !== 0 && (i = o, t = wl(e, o))), t === 1)) throw n = tl, Ml(e, 0), Dl(e, i), Sl(e, xt()), n;
				switch (e.finishedWork = a, e.finishedLanes = i, t) {
					case 0:
					case 1: throw Error(r(345));
					case 2:
						Vl(e, al, cl);
						break;
					case 3:
						if (Dl(e, i), (i & 130023424) === i && (t = ol + 500 - xt(), 10 < t)) {
							if (Rt(e, 0) !== 0) break;
							if (a = e.suspendedLanes, (a & i) !== i) {
								yl(), e.pingedLanes |= e.suspendedLanes & a;
								break;
							}
							e.timeoutHandle = Oi(Vl.bind(null, e, al, cl), t);
							break;
						}
						Vl(e, al, cl);
						break;
					case 4:
						if (Dl(e, i), (i & 4194240) === i) break;
						for (t = e.eventTimes, a = -1; 0 < i;) {
							var s = 31 - jt(i);
							o = 1 << s, s = t[s], s > a && (a = s), i &= ~o;
						}
						if (i = a, i = xt() - i, i = (120 > i ? 120 : 480 > i ? 480 : 1080 > i ? 1080 : 1920 > i ? 1920 : 3e3 > i ? 3e3 : 4320 > i ? 4320 : 1960 * Gc(i / 1960)) - i, 10 < i) {
							e.timeoutHandle = Oi(Vl.bind(null, e, al, cl), i);
							break;
						}
						Vl(e, al, cl);
						break;
					case 5:
						Vl(e, al, cl);
						break;
					default: throw Error(r(329));
				}
			}
		}
		return Sl(e, xt()), e.callbackNode === n ? Cl.bind(null, e) : null;
	}
	function wl(e, t) {
		var n = il;
		return e.current.memoizedState.isDehydrated && (Ml(e, t).flags |= 256), e = Il(e, t), e !== 2 && (t = al, al = n, t !== null && Tl(t)), e;
	}
	function Tl(e) {
		al === null ? al = e : al.push.apply(al, e);
	}
	function El(e) {
		for (var t = e;;) {
			if (t.flags & 16384) {
				var n = t.updateQueue;
				if (n !== null && (n = n.stores, n !== null)) for (var r = 0; r < n.length; r++) {
					var i = n[r], a = i.getSnapshot;
					i = i.value;
					try {
						if (!Pr(a(), i)) return !1;
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
	function Dl(e, t) {
		for (t &= ~rl, t &= ~K, e.suspendedLanes |= t, e.pingedLanes &= ~t, e = e.expirationTimes; 0 < t;) {
			var n = 31 - jt(t), r = 1 << n;
			e[n] = -1, t &= ~r;
		}
	}
	function Ol(e) {
		if (G & 6) throw Error(r(327));
		Ul();
		var t = Rt(e, 0);
		if (!(t & 1)) return Sl(e, xt()), null;
		var n = Il(e, t);
		if (e.tag !== 0 && n === 2) {
			var i = Vt(e);
			i !== 0 && (t = i, n = wl(e, i));
		}
		if (n === 1) throw n = tl, Ml(e, 0), Dl(e, t), Sl(e, xt()), n;
		if (n === 6) throw Error(r(345));
		return e.finishedWork = e.current.alternate, e.finishedLanes = t, Vl(e, al, cl), Sl(e, xt()), null;
	}
	function kl(e, t) {
		var n = G;
		G |= 1;
		try {
			return e(t);
		} finally {
			G = n, G === 0 && (sl = xt() + 500, la && pa());
		}
	}
	function Al(e) {
		pl !== null && pl.tag === 0 && !(G & 6) && Ul();
		var t = G;
		G |= 1;
		var n = Jc.transition, r = F;
		try {
			if (Jc.transition = null, F = 1, e) return e();
		} finally {
			F = r, Jc.transition = n, G = t, !(G & 6) && pa();
		}
	}
	function jl() {
		Qc = $c.current, z($c);
	}
	function Ml(e, t) {
		e.finishedWork = null, e.finishedLanes = 0;
		var n = e.timeoutHandle;
		if (n !== -1 && (e.timeoutHandle = -1, ki(n)), Xc !== null) for (n = Xc.return; n !== null;) {
			var r = n;
			switch (Ea(r), r.tag) {
				case 1:
					r = r.type.childContextTypes, r != null && ra();
					break;
				case 3:
					bo(), z($i), z(Qi), Eo();
					break;
				case 5:
					So(r);
					break;
				case 4:
					bo();
					break;
				case 13:
					z(Co);
					break;
				case 19:
					z(Co);
					break;
				case 10:
					Qa(r.type._context);
					break;
				case 22:
				case 23: jl();
			}
			n = n.return;
		}
		if (Yc = e, Xc = e = nu(e.current, null), Zc = Qc = t, el = 0, tl = null, rl = K = nl = 0, al = il = null, no !== null) {
			for (t = 0; t < no.length; t++) if (n = no[t], r = n.interleaved, r !== null) {
				n.interleaved = null;
				var i = r.next, a = n.pending;
				if (a !== null) {
					var o = a.next;
					a.next = i, r.next = o;
				}
				n.pending = r;
			}
			no = null;
		}
		return e;
	}
	function Nl(e, t) {
		do {
			var n = Xc;
			try {
				if (Za(), Do.current = bs, Mo) {
					for (var i = H.memoizedState; i !== null;) {
						var a = i.queue;
						a !== null && (a.pending = null), i = i.next;
					}
					Mo = !1;
				}
				if (ko = 0, jo = Ao = H = null, No = !1, Po = 0, qc.current = null, n === null || n.return === null) {
					el = 1, tl = t, Xc = null;
					break;
				}
				a: {
					var o = e, s = n.return, c = n, l = t;
					if (t = Zc, c.flags |= 32768, typeof l == "object" && l && typeof l.then == "function") {
						var u = l, d = c, f = d.tag;
						if (!(d.mode & 1) && (f === 0 || f === 11 || f === 15)) {
							var p = d.alternate;
							p ? (d.updateQueue = p.updateQueue, d.memoizedState = p.memoizedState, d.lanes = p.lanes) : (d.updateQueue = null, d.memoizedState = null);
						}
						var m = Ls(s);
						if (m !== null) {
							m.flags &= -257, Rs(m, s, c, o, t), m.mode & 1 && Is(o, u, t), t = m, l = u;
							var h = t.updateQueue;
							if (h === null) {
								var g = /* @__PURE__ */ new Set();
								g.add(l), t.updateQueue = g;
							} else h.add(l);
							break a;
						} else {
							if (!(t & 1)) {
								Is(o, u, t), Fl();
								break a;
							}
							l = Error(r(426));
						}
					} else if (ka && c.mode & 1) {
						var _ = Ls(s);
						if (_ !== null) {
							!(_.flags & 65536) && (_.flags |= 256), Rs(_, s, c, o, t), za(As(l, c));
							break a;
						}
					}
					o = l = As(l, c), el !== 4 && (el = 2), il === null ? il = [o] : il.push(o), o = s;
					do {
						switch (o.tag) {
							case 3:
								o.flags |= 65536, t &= -t, o.lanes |= t;
								var v = Ps(o, l, t);
								fo(o, v);
								break a;
							case 1:
								c = l;
								var y = o.type, b = o.stateNode;
								if (!(o.flags & 128) && (typeof y.getDerivedStateFromError == "function" || b !== null && typeof b.componentDidCatch == "function" && (dl === null || !dl.has(b)))) {
									o.flags |= 65536, t &= -t, o.lanes |= t;
									var x = Fs(o, c, t);
									fo(o, x);
									break a;
								}
						}
						o = o.return;
					} while (o !== null);
				}
				Bl(n);
			} catch (e) {
				t = e, Xc === n && n !== null && (Xc = n = n.return);
				continue;
			}
			break;
		} while (1);
	}
	function Pl() {
		var e = Kc.current;
		return Kc.current = bs, e === null ? bs : e;
	}
	function Fl() {
		(el === 0 || el === 3 || el === 2) && (el = 4), Yc === null || !(nl & 268435455) && !(K & 268435455) || Dl(Yc, Zc);
	}
	function Il(e, t) {
		var n = G;
		G |= 2;
		var i = Pl();
		(Yc !== e || Zc !== t) && (cl = null, Ml(e, t));
		do
			try {
				Ll();
				break;
			} catch (t) {
				Nl(e, t);
			}
		while (1);
		if (Za(), G = n, Kc.current = i, Xc !== null) throw Error(r(261));
		return Yc = null, Zc = 0, el;
	}
	function Ll() {
		for (; Xc !== null;) zl(Xc);
	}
	function Rl() {
		for (; Xc !== null && !yt();) zl(Xc);
	}
	function zl(e) {
		var t = Xl(e.alternate, e, Qc);
		e.memoizedProps = e.pendingProps, t === null ? Bl(e) : Xc = t, qc.current = null;
	}
	function Bl(e) {
		var t = e;
		do {
			var n = t.alternate;
			if (e = t.return, t.flags & 32768) {
				if (n = gc(n, t), n !== null) {
					n.flags &= 32767, Xc = n;
					return;
				}
				if (e !== null) e.flags |= 32768, e.subtreeFlags = 0, e.deletions = null;
				else {
					el = 6, Xc = null;
					return;
				}
			} else if (n = hc(n, t, Qc), n !== null) {
				Xc = n;
				return;
			}
			if (t = t.sibling, t !== null) {
				Xc = t;
				return;
			}
			Xc = t = e;
		} while (t !== null);
		el === 0 && (el = 5);
	}
	function Vl(e, t, n) {
		var r = F, i = Jc.transition;
		try {
			Jc.transition = null, F = 1, Hl(e, t, n, r);
		} finally {
			Jc.transition = i, F = r;
		}
		return null;
	}
	function Hl(e, t, n, i) {
		do
			Ul();
		while (pl !== null);
		if (G & 6) throw Error(r(327));
		n = e.finishedWork;
		var a = e.finishedLanes;
		if (n === null) return null;
		if (e.finishedWork = null, e.finishedLanes = 0, n === e.current) throw Error(r(177));
		e.callbackNode = null, e.callbackPriority = 0;
		var o = n.lanes | n.childLanes;
		if (Gt(e, o), e === Yc && (Xc = Yc = null, Zc = 0), !(n.subtreeFlags & 2064) && !(n.flags & 2064) || fl || (fl = !0, Zl(Tt, function() {
			return Ul(), null;
		})), o = (n.flags & 15990) != 0, n.subtreeFlags & 15990 || o) {
			o = Jc.transition, Jc.transition = null;
			var s = F;
			F = 1;
			var c = G;
			G |= 4, qc.current = null, Cc(e, n), Rc(n, e), L(Ei), vn = !!Ti, Ei = Ti = null, e.current = n, Bc(n, e, a), bt(), G = c, F = s, Jc.transition = o;
		} else e.current = n;
		if (fl && (fl = !1, pl = e, ml = a), o = e.pendingLanes, o === 0 && (dl = null), At(n.stateNode, i), Sl(e, xt()), t !== null) for (i = e.onRecoverableError, n = 0; n < t.length; n++) a = t[n], i(a.value, {
			componentStack: a.stack,
			digest: a.digest
		});
		if (ll) throw ll = !1, e = ul, ul = null, e;
		return ml & 1 && e.tag !== 0 && Ul(), o = e.pendingLanes, o & 1 ? e === gl ? hl++ : (hl = 0, gl = e) : hl = 0, pa(), null;
	}
	function Ul() {
		if (pl !== null) {
			var e = qt(ml), t = Jc.transition, n = F;
			try {
				if (Jc.transition = null, F = 16 > e ? 16 : e, pl === null) var i = !1;
				else {
					if (e = pl, pl = null, ml = 0, G & 6) throw Error(r(331));
					var a = G;
					for (G |= 4, W = e.current; W !== null;) {
						var o = W, s = o.child;
						if (W.flags & 16) {
							var c = o.deletions;
							if (c !== null) {
								for (var l = 0; l < c.length; l++) {
									var u = c[l];
									for (W = u; W !== null;) {
										var d = W;
										switch (d.tag) {
											case 0:
											case 11:
											case 15: wc(8, d, o);
										}
										var f = d.child;
										if (f !== null) f.return = d, W = f;
										else for (; W !== null;) {
											d = W;
											var p = d.sibling, m = d.return;
											if (Dc(d), d === u) {
												W = null;
												break;
											}
											if (p !== null) {
												p.return = m, W = p;
												break;
											}
											W = m;
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
								W = o;
							}
						}
						if (o.subtreeFlags & 2064 && s !== null) s.return = o, W = s;
						else b: for (; W !== null;) {
							if (o = W, o.flags & 2048) switch (o.tag) {
								case 0:
								case 11:
								case 15: wc(9, o, o.return);
							}
							var v = o.sibling;
							if (v !== null) {
								v.return = o.return, W = v;
								break b;
							}
							W = o.return;
						}
					}
					var y = e.current;
					for (W = y; W !== null;) {
						s = W;
						var b = s.child;
						if (s.subtreeFlags & 2064 && b !== null) b.return = s, W = b;
						else b: for (s = y; W !== null;) {
							if (c = W, c.flags & 2048) try {
								switch (c.tag) {
									case 0:
									case 11:
									case 15: Tc(9, c);
								}
							} catch (e) {
								Gl(c, c.return, e);
							}
							if (c === s) {
								W = null;
								break b;
							}
							var x = c.sibling;
							if (x !== null) {
								x.return = c.return, W = x;
								break b;
							}
							W = c.return;
						}
					}
					if (G = a, pa(), kt && typeof kt.onPostCommitFiberRoot == "function") try {
						kt.onPostCommitFiberRoot(Ot, e);
					} catch (e) {}
					i = !0;
				}
				return i;
			} finally {
				F = n, Jc.transition = t;
			}
		}
		return !1;
	}
	function Wl(e, t, n) {
		t = As(n, t), t = Ps(e, t, 1), e = lo(e, t, 1), t = yl(), e !== null && (Wt(e, 1, t), Sl(e, t));
	}
	function Gl(e, t, n) {
		if (e.tag === 3) Wl(e, e, n);
		else for (; t !== null;) {
			if (t.tag === 3) {
				Wl(t, e, n);
				break;
			} else if (t.tag === 1) {
				var r = t.stateNode;
				if (typeof t.type.getDerivedStateFromError == "function" || typeof r.componentDidCatch == "function" && (dl === null || !dl.has(r))) {
					e = As(n, e), e = Fs(t, e, 1), t = lo(t, e, 1), e = yl(), t !== null && (Wt(t, 1, e), Sl(t, e));
					break;
				}
			}
			t = t.return;
		}
	}
	function Kl(e, t, n) {
		var r = e.pingCache;
		r !== null && r.delete(t), t = yl(), e.pingedLanes |= e.suspendedLanes & n, Yc === e && (Zc & n) === n && (el === 4 || el === 3 && (Zc & 130023424) === Zc && 500 > xt() - ol ? Ml(e, 0) : rl |= n), Sl(e, t);
	}
	function ql(e, t) {
		t === 0 && (e.mode & 1 ? (t = It, It <<= 1, !(It & 130023424) && (It = 4194304)) : t = 1);
		var n = yl();
		e = io(e, t), e !== null && (Wt(e, t, n), Sl(e, n));
	}
	function Jl(e) {
		var t = e.memoizedState, n = 0;
		t !== null && (n = t.retryLane), ql(e, n);
	}
	function Yl(e, t) {
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
		i !== null && i.delete(t), ql(e, n);
	}
	var Xl = function(e, t, n) {
		if (e !== null) if (e.memoizedProps !== t.pendingProps || $i.current) Bs = !0;
		else {
			if ((e.lanes & n) === 0 && !(t.flags & 128)) return Bs = !1, lc(e, t, n);
			Bs = !!(e.flags & 131072);
		}
		else Bs = !1, ka && t.flags & 1048576 && wa(t, _a, t.index);
		switch (t.lanes = 0, t.tag) {
			case 2:
				var i = t.type;
				sc(e, t), e = t.pendingProps;
				var a = ta(t, Qi.current);
				eo(t, n), a = Ro(null, t, i, e, a, n);
				var o = zo();
				return t.flags |= 1, typeof a == "object" && a && typeof a.render == "function" && a.$$typeof === void 0 ? (t.tag = 1, t.memoizedState = null, t.updateQueue = null, na(i) ? (o = !0, oa(t)) : o = !1, t.memoizedState = a.state !== null && a.state !== void 0 ? a.state : null, oo(t), a.updater = Ts, t.stateNode = a, a._reactInternals = t, ks(t, i, e, n), t = Ys(null, t, i, !0, o, n)) : (t.tag = 0, ka && o && Ta(t), Vs(null, t, a, n), t = t.child), t;
			case 16:
				i = t.elementType;
				a: {
					switch (sc(e, t), e = t.pendingProps, a = i._init, i = a(i._payload), t.type = i, a = t.tag = tu(i), e = ws(i, e), a) {
						case 0:
							t = qs(null, t, i, e, n);
							break a;
						case 1:
							t = Js(null, t, i, e, n);
							break a;
						case 11:
							t = Hs(null, t, i, e, n);
							break a;
						case 14:
							t = Us(null, t, i, ws(i.type, e), n);
							break a;
					}
					throw Error(r(306, i, ""));
				}
				return t;
			case 0: return i = t.type, a = t.pendingProps, a = t.elementType === i ? a : ws(i, a), qs(e, t, i, a, n);
			case 1: return i = t.type, a = t.pendingProps, a = t.elementType === i ? a : ws(i, a), Js(e, t, i, a, n);
			case 3:
				a: {
					if (Xs(t), e === null) throw Error(r(387));
					i = t.pendingProps, o = t.memoizedState, a = o.element, so(e, t), po(t, i, null, n);
					var s = t.memoizedState;
					if (i = s.element, o.isDehydrated) if (o = {
						element: i,
						isDehydrated: !1,
						cache: s.cache,
						pendingSuspenseBoundaries: s.pendingSuspenseBoundaries,
						transitions: s.transitions
					}, t.updateQueue.baseState = o, t.memoizedState = o, t.flags & 256) {
						a = As(Error(r(423)), t), t = Zs(e, t, i, n, a);
						break a;
					} else if (i !== a) {
						a = As(Error(r(424)), t), t = Zs(e, t, i, n, a);
						break a;
					} else for (Oa = Pi(t.stateNode.containerInfo.firstChild), Da = t, ka = !0, Aa = null, n = Ka(t, null, i, n), t.child = n; n;) n.flags = n.flags & -3 | 4096, n = n.sibling;
					else {
						if (Ra(), i === a) {
							t = cc(e, t, n);
							break a;
						}
						Vs(e, t, i, n);
					}
					t = t.child;
				}
				return t;
			case 5: return xo(t), e === null && Pa(t), i = t.type, a = t.pendingProps, o = e === null ? null : e.memoizedProps, s = a.children, Di(i, a) ? s = null : o !== null && Di(i, o) && (t.flags |= 32), Ks(e, t), Vs(e, t, s, n), t.child;
			case 6: return e === null && Pa(t), null;
			case 13: return ec(e, t, n);
			case 4: return yo(t, t.stateNode.containerInfo), i = t.pendingProps, e === null ? t.child = Ga(t, null, i, n) : Vs(e, t, i, n), t.child;
			case 11: return i = t.type, a = t.pendingProps, a = t.elementType === i ? a : ws(i, a), Hs(e, t, i, a, n);
			case 7: return Vs(e, t, t.pendingProps, n), t.child;
			case 8: return Vs(e, t, t.pendingProps.children, n), t.child;
			case 12: return Vs(e, t, t.pendingProps.children, n), t.child;
			case 10:
				a: {
					if (i = t.type._context, a = t.pendingProps, o = t.memoizedProps, s = a.value, Xi(qa, i._currentValue), i._currentValue = s, o !== null) if (Pr(o.value, s)) {
						if (o.children === a.children && !$i.current) {
							t = cc(e, t, n);
							break a;
						}
					} else for (o = t.child, o !== null && (o.return = t); o !== null;) {
						var c = o.dependencies;
						if (c !== null) {
							s = o.child;
							for (var l = c.firstContext; l !== null;) {
								if (l.context === i) {
									if (o.tag === 1) {
										l = co(-1, n & -n), l.tag = 2;
										var u = o.updateQueue;
										if (u !== null) {
											u = u.shared;
											var d = u.pending;
											d === null ? l.next = l : (l.next = d.next, d.next = l), u.pending = l;
										}
									}
									o.lanes |= n, l = o.alternate, l !== null && (l.lanes |= n), $a(o.return, n, t), c.lanes |= n;
									break;
								}
								l = l.next;
							}
						} else if (o.tag === 10) s = o.type === t.type ? null : o.child;
						else if (o.tag === 18) {
							if (s = o.return, s === null) throw Error(r(341));
							s.lanes |= n, c = s.alternate, c !== null && (c.lanes |= n), $a(s, n, t), s = o.sibling;
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
					Vs(e, t, a.children, n), t = t.child;
				}
				return t;
			case 9: return a = t.type, i = t.pendingProps.children, eo(t, n), a = to(a), i = i(a), t.flags |= 1, Vs(e, t, i, n), t.child;
			case 14: return i = t.type, a = ws(i, t.pendingProps), a = ws(i.type, a), Us(e, t, i, a, n);
			case 15: return Ws(e, t, t.type, t.pendingProps, n);
			case 17: return i = t.type, a = t.pendingProps, a = t.elementType === i ? a : ws(i, a), sc(e, t), t.tag = 1, na(i) ? (e = !0, oa(t)) : e = !1, eo(t, n), Ds(t, i, a), ks(t, i, a, n), Ys(null, t, i, !0, e, n);
			case 19: return oc(e, t, n);
			case 22: return Gs(e, t, n);
		}
		throw Error(r(156, t.tag));
	};
	function Zl(e, t) {
		return _t(e, t);
	}
	function Ql(e, t, n, r) {
		this.tag = e, this.key = n, this.sibling = this.child = this.return = this.stateNode = this.type = this.elementType = null, this.index = 0, this.ref = null, this.pendingProps = t, this.dependencies = this.memoizedState = this.updateQueue = this.memoizedProps = null, this.mode = r, this.subtreeFlags = this.flags = 0, this.deletions = null, this.childLanes = this.lanes = 0, this.alternate = null;
	}
	function $l(e, t, n, r) {
		return new Ql(e, t, n, r);
	}
	function eu(e) {
		return e = e.prototype, !(!e || !e.isReactComponent);
	}
	function tu(e) {
		if (typeof e == "function") return +!!eu(e);
		if (e != null) {
			if (e = e.$$typeof, e === j) return 11;
			if (e === P) return 14;
		}
		return 2;
	}
	function nu(e, t) {
		var n = e.alternate;
		return n === null ? (n = $l(e.tag, t, e.key, e.mode), n.elementType = e.elementType, n.type = e.type, n.stateNode = e.stateNode, n.alternate = e, e.alternate = n) : (n.pendingProps = t, n.type = e.type, n.flags = 0, n.subtreeFlags = 0, n.deletions = null), n.flags = e.flags & 14680064, n.childLanes = e.childLanes, n.lanes = e.lanes, n.child = e.child, n.memoizedProps = e.memoizedProps, n.memoizedState = e.memoizedState, n.updateQueue = e.updateQueue, t = e.dependencies, n.dependencies = t === null ? null : {
			lanes: t.lanes,
			firstContext: t.firstContext
		}, n.sibling = e.sibling, n.index = e.index, n.ref = e.ref, n;
	}
	function ru(e, t, n, i, a, o) {
		var s = 2;
		if (i = e, typeof e == "function") eu(e) && (s = 1);
		else if (typeof e == "string") s = 5;
		else a: switch (e) {
			case E: return iu(n.children, a, o, t);
			case D:
				s = 8, a |= 8;
				break;
			case O: return e = $l(12, n, t, a | 2), e.elementType = O, e.lanes = o, e;
			case M: return e = $l(13, n, t, a), e.elementType = M, e.lanes = o, e;
			case N: return e = $l(19, n, t, a), e.elementType = N, e.lanes = o, e;
			case te: return au(n, a, o, t);
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
		return t = $l(s, n, t, a), t.elementType = e, t.type = i, t.lanes = o, t;
	}
	function iu(e, t, n, r) {
		return e = $l(7, e, r, t), e.lanes = n, e;
	}
	function au(e, t, n, r) {
		return e = $l(22, e, r, t), e.elementType = te, e.lanes = n, e.stateNode = { isHidden: !1 }, e;
	}
	function ou(e, t, n) {
		return e = $l(6, e, null, t), e.lanes = n, e;
	}
	function su(e, t, n) {
		return t = $l(4, e.children === null ? [] : e.children, e.key, t), t.lanes = n, t.stateNode = {
			containerInfo: e.containerInfo,
			pendingChildren: null,
			implementation: e.implementation
		}, t;
	}
	function cu(e, t, n, r, i) {
		this.tag = t, this.containerInfo = e, this.finishedWork = this.pingCache = this.current = this.pendingChildren = null, this.timeoutHandle = -1, this.callbackNode = this.pendingContext = this.context = null, this.callbackPriority = 0, this.eventTimes = Ut(0), this.expirationTimes = Ut(-1), this.entangledLanes = this.finishedLanes = this.mutableReadLanes = this.expiredLanes = this.pingedLanes = this.suspendedLanes = this.pendingLanes = 0, this.entanglements = Ut(0), this.identifierPrefix = r, this.onRecoverableError = i, this.mutableSourceEagerHydrationData = null;
	}
	function lu(e, t, n, r, i, a, o, s, c) {
		return e = new cu(e, t, n, s, c), t === 1 ? (t = 1, !0 === a && (t |= 8)) : t = 0, a = $l(3, null, null, t), e.current = a, a.stateNode = e, a.memoizedState = {
			element: r,
			isDehydrated: n,
			cache: null,
			transitions: null,
			pendingSuspenseBoundaries: null
		}, oo(a), e;
	}
	function uu(e, t, n) {
		var r = 3 < arguments.length && arguments[3] !== void 0 ? arguments[3] : null;
		return {
			$$typeof: T,
			key: r == null ? null : "" + r,
			children: e,
			containerInfo: t,
			implementation: n
		};
	}
	function du(e) {
		if (!e) return Zi;
		e = e._reactInternals;
		a: {
			if (dt(e) !== e || e.tag !== 1) throw Error(r(170));
			var t = e;
			do {
				switch (t.tag) {
					case 3:
						t = t.stateNode.context;
						break a;
					case 1: if (na(t.type)) {
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
			if (na(n)) return aa(e, n, t);
		}
		return t;
	}
	function fu(e, t, n, r, i, a, o, s, c) {
		return e = lu(n, r, !0, e, i, a, o, s, c), e.context = du(null), n = e.current, r = yl(), i = bl(n), a = co(r, i), a.callback = t == null ? null : t, lo(n, a, i), e.current.lanes = i, Wt(e, i, r), Sl(e, r), e;
	}
	function pu(e, t, n, r) {
		var i = t.current, a = yl(), o = bl(i);
		return n = du(n), t.context === null ? t.context = n : t.pendingContext = n, t = co(a, o), t.payload = { element: e }, r = r === void 0 ? null : r, r !== null && (t.callback = r), e = lo(i, t, o), e !== null && (xl(e, i, o, a), uo(e, i, o)), o;
	}
	function mu(e) {
		if (e = e.current, !e.child) return null;
		switch (e.child.tag) {
			case 5: return e.child.stateNode;
			default: return e.child.stateNode;
		}
	}
	function hu(e, t) {
		if (e = e.memoizedState, e !== null && e.dehydrated !== null) {
			var n = e.retryLane;
			e.retryLane = n !== 0 && n < t ? n : t;
		}
	}
	function gu(e, t) {
		hu(e, t), (e = e.alternate) && hu(e, t);
	}
	function _u() {
		return null;
	}
	var vu = typeof reportError == "function" ? reportError : function(e) {
		console.error(e);
	};
	function yu(e) {
		this._internalRoot = e;
	}
	bu.prototype.render = yu.prototype.render = function(e) {
		var t = this._internalRoot;
		if (t === null) throw Error(r(409));
		pu(e, t, null, null);
	}, bu.prototype.unmount = yu.prototype.unmount = function() {
		var e = this._internalRoot;
		if (e !== null) {
			this._internalRoot = null;
			var t = e.containerInfo;
			Al(function() {
				pu(null, e, null, null);
			}), t[zi] = null;
		}
	};
	function bu(e) {
		this._internalRoot = e;
	}
	bu.prototype.unstable_scheduleHydration = function(e) {
		if (e) {
			var t = Zt();
			e = {
				blockedOn: null,
				target: e,
				priority: t
			};
			for (var n = 0; n < on.length && t !== 0 && t < on[n].priority; n++);
			on.splice(n, 0, e), n === 0 && dn(e);
		}
	};
	function xu(e) {
		return !(!e || e.nodeType !== 1 && e.nodeType !== 9 && e.nodeType !== 11);
	}
	function Su(e) {
		return !(!e || e.nodeType !== 1 && e.nodeType !== 9 && e.nodeType !== 11 && (e.nodeType !== 8 || e.nodeValue !== " react-mount-point-unstable "));
	}
	function Cu() {}
	function wu(e, t, n, r, i) {
		if (i) {
			if (typeof r == "function") {
				var a = r;
				r = function() {
					var e = mu(o);
					a.call(e);
				};
			}
			var o = fu(t, r, e, 0, null, !1, !1, "", Cu);
			return e._reactRootContainer = o, e[zi] = o.current, pi(e.nodeType === 8 ? e.parentNode : e), Al(), o;
		}
		for (; i = e.lastChild;) e.removeChild(i);
		if (typeof r == "function") {
			var s = r;
			r = function() {
				var e = mu(c);
				s.call(e);
			};
		}
		var c = lu(e, 0, !1, null, null, !1, !1, "", Cu);
		return e._reactRootContainer = c, e[zi] = c.current, pi(e.nodeType === 8 ? e.parentNode : e), Al(function() {
			pu(t, c, n, r);
		}), c;
	}
	function Tu(e, t, n, r, i) {
		var a = n._reactRootContainer;
		if (a) {
			var o = a;
			if (typeof i == "function") {
				var s = i;
				i = function() {
					var e = mu(o);
					s.call(e);
				};
			}
			pu(t, o, e, i);
		} else o = wu(n, t, e, i, r);
		return mu(o);
	}
	Jt = function(e) {
		switch (e.tag) {
			case 3:
				var t = e.stateNode;
				if (t.current.memoizedState.isDehydrated) {
					var n = Lt(t.pendingLanes);
					n !== 0 && (Kt(t, n | 1), Sl(t, xt()), !(G & 6) && (sl = xt() + 500, pa()));
				}
				break;
			case 13: Al(function() {
				var t = io(e, 1);
				t !== null && xl(t, e, 1, yl());
			}), gu(e, 1);
		}
	}, Yt = function(e) {
		if (e.tag === 13) {
			var t = io(e, 134217728);
			t !== null && xl(t, e, 134217728, yl()), gu(e, 134217728);
		}
	}, Xt = function(e) {
		if (e.tag === 13) {
			var t = bl(e), n = io(e, t);
			n !== null && xl(n, e, t, yl()), gu(e, t);
		}
	}, Zt = function() {
		return F;
	}, Qt = function(e, t) {
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
	}, Xe = kl, Ze = Al;
	var Eu = {
		usingClientEntryPoint: !1,
		Events: [
			Wi,
			Gi,
			Ki,
			Je,
			Ye,
			kl
		]
	}, Du = {
		findFiberByHostInstance: Ui,
		bundleType: 0,
		version: "18.3.1",
		rendererPackageName: "react-dom"
	}, Ou = {
		bundleType: Du.bundleType,
		version: Du.version,
		rendererPackageName: Du.rendererPackageName,
		rendererConfig: Du.rendererConfig,
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
		findFiberByHostInstance: Du.findFiberByHostInstance || _u,
		findHostInstancesForRefresh: null,
		scheduleRefresh: null,
		scheduleRoot: null,
		setRefreshHandler: null,
		getCurrentFiber: null,
		reconcilerVersion: "18.3.1-next-f1338f8080-20240426"
	};
	if (typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ < "u") {
		var ku = __REACT_DEVTOOLS_GLOBAL_HOOK__;
		if (!ku.isDisabled && ku.supportsFiber) try {
			Ot = ku.inject(Ou), kt = ku;
		} catch (e) {}
	}
	e.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED = Eu, e.createPortal = function(e, t) {
		var n = 2 < arguments.length && arguments[2] !== void 0 ? arguments[2] : null;
		if (!xu(t)) throw Error(r(200));
		return uu(e, t, null, n);
	}, e.createRoot = function(e, t) {
		if (!xu(e)) throw Error(r(299));
		var n = !1, i = "", a = vu;
		return t != null && (!0 === t.unstable_strictMode && (n = !0), t.identifierPrefix !== void 0 && (i = t.identifierPrefix), t.onRecoverableError !== void 0 && (a = t.onRecoverableError)), t = lu(e, 1, !1, null, null, n, !1, i, a), e[zi] = t.current, pi(e.nodeType === 8 ? e.parentNode : e), new yu(t);
	}, e.findDOMNode = function(e) {
		if (e == null) return null;
		if (e.nodeType === 1) return e;
		var t = e._reactInternals;
		if (t === void 0) throw typeof e.render == "function" ? Error(r(188)) : (e = Object.keys(e).join(","), Error(r(268, e)));
		return e = ht(t), e = e === null ? null : e.stateNode, e;
	}, e.flushSync = function(e) {
		return Al(e);
	}, e.hydrate = function(e, t, n) {
		if (!Su(t)) throw Error(r(200));
		return Tu(null, e, t, !0, n);
	}, e.hydrateRoot = function(e, t, n) {
		if (!xu(e)) throw Error(r(405));
		var i = n != null && n.hydratedSources || null, a = !1, o = "", s = vu;
		if (n != null && (!0 === n.unstable_strictMode && (a = !0), n.identifierPrefix !== void 0 && (o = n.identifierPrefix), n.onRecoverableError !== void 0 && (s = n.onRecoverableError)), t = fu(t, null, e, 1, n == null ? null : n, a, !1, o, s), e[zi] = t.current, pi(e), i) for (e = 0; e < i.length; e++) n = i[e], a = n._getVersion, a = a(n._source), t.mutableSourceEagerHydrationData == null ? t.mutableSourceEagerHydrationData = [n, a] : t.mutableSourceEagerHydrationData.push(n, a);
		return new bu(t);
	}, e.render = function(e, t, n) {
		if (!Su(t)) throw Error(r(200));
		return Tu(null, e, t, !1, n);
	}, e.unmountComponentAtNode = function(e) {
		if (!Su(e)) throw Error(r(40));
		return e._reactRootContainer ? (Al(function() {
			Tu(null, null, e, !1, function() {
				e._reactRootContainer = null, e[zi] = null;
			});
		}), !0) : !1;
	}, e.unstable_batchedUpdates = kl, e.unstable_renderSubtreeIntoContainer = function(e, t, n, i) {
		if (!Su(n)) throw Error(r(200));
		if (e == null || e._reactInternals === void 0) throw Error(r(38));
		return Tu(e, t, n, !1, i);
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
}]]), k = D("arrow-up-down", [
	["path", {
		d: "m21 16-4 4-4-4",
		key: "f6ql7i"
	}],
	["path", {
		d: "M17 20V4",
		key: "1ejh1v"
	}],
	["path", {
		d: "m3 8 4-4 4 4",
		key: "11wl7u"
	}],
	["path", {
		d: "M7 4v16",
		key: "1glfcx"
	}]
]), A = D("briefcase-business", [
	["path", {
		d: "M12 12h.01",
		key: "1mp3jc"
	}],
	["path", {
		d: "M16 6V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2",
		key: "1ksdt3"
	}],
	["path", {
		d: "M22 13a18.15 18.15 0 0 1-20 0",
		key: "12hx5q"
	}],
	["rect", {
		width: "20",
		height: "14",
		x: "2",
		y: "6",
		rx: "2",
		key: "i6l2r4"
	}]
]), j = D("check", [["path", {
	d: "M20 6 9 17l-5-5",
	key: "1gmf2c"
}]]), M = D("chevron-down", [["path", {
	d: "m6 9 6 6 6-6",
	key: "qrunsl"
}]]), N = D("chevron-right", [["path", {
	d: "m9 18 6-6-6-6",
	key: "mthhwq"
}]]), P = D("chevron-up", [["path", {
	d: "m18 15-6-6-6 6",
	key: "153udz"
}]]), ee = D("circle-check", [["circle", {
	cx: "12",
	cy: "12",
	r: "10",
	key: "1mglay"
}], ["path", {
	d: "m9 12 2 2 4-4",
	key: "dzmm74"
}]]), te = D("circle", [["circle", {
	cx: "12",
	cy: "12",
	r: "10",
	key: "1mglay"
}]]), ne = D("clipboard-check", [
	["rect", {
		width: "8",
		height: "4",
		x: "8",
		y: "2",
		rx: "1",
		ry: "1",
		key: "tgr4d6"
	}],
	["path", {
		d: "M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2",
		key: "116196"
	}],
	["path", {
		d: "m9 14 2 2 4-4",
		key: "df797q"
	}]
]), re = D("clipboard-list", [
	["rect", {
		width: "8",
		height: "4",
		x: "8",
		y: "2",
		rx: "1",
		ry: "1",
		key: "tgr4d6"
	}],
	["path", {
		d: "M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2",
		key: "116196"
	}],
	["path", {
		d: "M12 11h4",
		key: "1jrz19"
	}],
	["path", {
		d: "M12 16h4",
		key: "n85exb"
	}],
	["path", {
		d: "M8 11h.01",
		key: "1dfujw"
	}],
	["path", {
		d: "M8 16h.01",
		key: "18s6g9"
	}]
]), ie = D("clock-3", [["circle", {
	cx: "12",
	cy: "12",
	r: "10",
	key: "1mglay"
}], ["path", {
	d: "M12 6v6h4",
	key: "135r8i"
}]]), ae = D("database", [
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
]), oe = D("file-text", [
	["path", {
		d: "M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z",
		key: "1oefj6"
	}],
	["path", {
		d: "M14 2v5a1 1 0 0 0 1 1h5",
		key: "wfsgrz"
	}],
	["path", {
		d: "M10 9H8",
		key: "b1mrlr"
	}],
	["path", {
		d: "M16 13H8",
		key: "t4e002"
	}],
	["path", {
		d: "M16 17H8",
		key: "z1uh3a"
	}]
]), se = D("folder-heart", [["path", {
	d: "M10.638 20H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H20a2 2 0 0 1 2 2v3.417",
	key: "10r6g4"
}], ["path", {
	d: "M14.62 18.8A2.25 2.25 0 1 1 18 15.836a2.25 2.25 0 1 1 3.38 2.966l-2.626 2.856a.998.998 0 0 1-1.507 0z",
	key: "15cy7q"
}]]), ce = D("info", [
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
]), le = D("list-checks", [
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
]), ue = D("messages-square", [["path", {
	d: "M16 10a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 14.286V4a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z",
	key: "1n2ejm"
}], ["path", {
	d: "M20 9a2 2 0 0 1 2 2v10.286a.71.71 0 0 1-1.212.502l-2.202-2.202A2 2 0 0 0 17.172 19H10a2 2 0 0 1-2-2v-1",
	key: "1qfcsi"
}]]), de = D("play", [["path", {
	d: "M5 5a2 2 0 0 1 3.008-1.728l11.997 6.998a2 2 0 0 1 .003 3.458l-12 7A2 2 0 0 1 5 19z",
	key: "10ikf1"
}]]), fe = D("refresh-cw", [
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
]), pe = D("rotate-ccw", [["path", {
	d: "M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8",
	key: "1357e3"
}], ["path", {
	d: "M3 3v5h5",
	key: "1xhq8a"
}]]), me = D("rows-3", [
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
]), he = D("search", [["path", {
	d: "m21 21-4.34-4.34",
	key: "14j7rj"
}], ["circle", {
	cx: "11",
	cy: "11",
	r: "8",
	key: "4ej97u"
}]]), ge = D("settings-2", [
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
]), _e = D("shield-check", [["path", {
	d: "M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z",
	key: "oel41y"
}], ["path", {
	d: "m9 12 2 2 4-4",
	key: "dzmm74"
}]]), ve = D("triangle-alert", [
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
]), ye = D("user-round-check", [
	["path", {
		d: "M2 21a8 8 0 0 1 13.292-6",
		key: "bjp14o"
	}],
	["circle", {
		cx: "10",
		cy: "8",
		r: "5",
		key: "o932ke"
	}],
	["path", {
		d: "m16 19 2 2 4-4",
		key: "1b14m6"
	}]
]), be = D("users-round", [
	["path", {
		d: "M18 21a8 8 0 0 0-16 0",
		key: "3ypg7q"
	}],
	["circle", {
		cx: "10",
		cy: "8",
		r: "5",
		key: "o932ke"
	}],
	["path", {
		d: "M22 20c0-3.37-2-6.5-4-8a5 5 0 0 0-.45-8.3",
		key: "10s06x"
	}]
]), xe = D("wand-sparkles", [
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
function Se(e) {
	var t, n, r = "";
	if (typeof e == "string" || typeof e == "number") r += e;
	else if (typeof e == "object") if (Array.isArray(e)) {
		var i = e.length;
		for (t = 0; t < i; t++) e[t] && (n = Se(e[t])) && (r && (r += " "), r += n);
	} else for (n in e) e[n] && (r && (r += " "), r += n);
	return r;
}
function Ce() {
	for (var e, t, n = 0, r = "", i = arguments.length; n < i; n++) (e = arguments[n]) && (t = Se(e)) && (r && (r += " "), r += t);
	return r;
}
//#endregion
//#region node_modules/recharts/es6/util/excludeEventProps.js
var we = /* @__PURE__ */ "dangerouslySetInnerHTML.onCopy.onCopyCapture.onCut.onCutCapture.onPaste.onPasteCapture.onCompositionEnd.onCompositionEndCapture.onCompositionStart.onCompositionStartCapture.onCompositionUpdate.onCompositionUpdateCapture.onFocus.onFocusCapture.onBlur.onBlurCapture.onChange.onChangeCapture.onBeforeInput.onBeforeInputCapture.onInput.onInputCapture.onReset.onResetCapture.onSubmit.onSubmitCapture.onInvalid.onInvalidCapture.onLoad.onLoadCapture.onError.onErrorCapture.onKeyDown.onKeyDownCapture.onKeyPress.onKeyPressCapture.onKeyUp.onKeyUpCapture.onAbort.onAbortCapture.onCanPlay.onCanPlayCapture.onCanPlayThrough.onCanPlayThroughCapture.onDurationChange.onDurationChangeCapture.onEmptied.onEmptiedCapture.onEncrypted.onEncryptedCapture.onEnded.onEndedCapture.onLoadedData.onLoadedDataCapture.onLoadedMetadata.onLoadedMetadataCapture.onLoadStart.onLoadStartCapture.onPause.onPauseCapture.onPlay.onPlayCapture.onPlaying.onPlayingCapture.onProgress.onProgressCapture.onRateChange.onRateChangeCapture.onSeeked.onSeekedCapture.onSeeking.onSeekingCapture.onStalled.onStalledCapture.onSuspend.onSuspendCapture.onTimeUpdate.onTimeUpdateCapture.onVolumeChange.onVolumeChangeCapture.onWaiting.onWaitingCapture.onAuxClick.onAuxClickCapture.onClick.onClickCapture.onContextMenu.onContextMenuCapture.onDoubleClick.onDoubleClickCapture.onDrag.onDragCapture.onDragEnd.onDragEndCapture.onDragEnter.onDragEnterCapture.onDragExit.onDragExitCapture.onDragLeave.onDragLeaveCapture.onDragOver.onDragOverCapture.onDragStart.onDragStartCapture.onDrop.onDropCapture.onMouseDown.onMouseDownCapture.onMouseEnter.onMouseLeave.onMouseMove.onMouseMoveCapture.onMouseOut.onMouseOutCapture.onMouseOver.onMouseOverCapture.onMouseUp.onMouseUpCapture.onSelect.onSelectCapture.onTouchCancel.onTouchCancelCapture.onTouchEnd.onTouchEndCapture.onTouchMove.onTouchMoveCapture.onTouchStart.onTouchStartCapture.onPointerDown.onPointerDownCapture.onPointerMove.onPointerMoveCapture.onPointerUp.onPointerUpCapture.onPointerCancel.onPointerCancelCapture.onPointerEnter.onPointerEnterCapture.onPointerLeave.onPointerLeaveCapture.onPointerOver.onPointerOverCapture.onPointerOut.onPointerOutCapture.onGotPointerCapture.onGotPointerCaptureCapture.onLostPointerCapture.onLostPointerCaptureCapture.onScroll.onScrollCapture.onWheel.onWheelCapture.onAnimationStart.onAnimationStartCapture.onAnimationEnd.onAnimationEndCapture.onAnimationIteration.onAnimationIterationCapture.onTransitionEnd.onTransitionEndCapture".split(".");
function Te(e) {
	return typeof e == "string" && we.includes(e);
}
//#endregion
//#region node_modules/recharts/es6/util/svgPropertiesNoEvents.js
var Ee = /* @__PURE__ */ new Set(/* @__PURE__ */ "aria-activedescendant.aria-atomic.aria-autocomplete.aria-busy.aria-checked.aria-colcount.aria-colindex.aria-colspan.aria-controls.aria-current.aria-describedby.aria-details.aria-disabled.aria-errormessage.aria-expanded.aria-flowto.aria-haspopup.aria-hidden.aria-invalid.aria-keyshortcuts.aria-label.aria-labelledby.aria-level.aria-live.aria-modal.aria-multiline.aria-multiselectable.aria-orientation.aria-owns.aria-placeholder.aria-posinset.aria-pressed.aria-readonly.aria-relevant.aria-required.aria-roledescription.aria-rowcount.aria-rowindex.aria-rowspan.aria-selected.aria-setsize.aria-sort.aria-valuemax.aria-valuemin.aria-valuenow.aria-valuetext.className.color.height.id.lang.max.media.method.min.name.style.target.width.role.tabIndex.accentHeight.accumulate.additive.alignmentBaseline.allowReorder.alphabetic.amplitude.arabicForm.ascent.attributeName.attributeType.autoReverse.azimuth.baseFrequency.baselineShift.baseProfile.bbox.begin.bias.by.calcMode.capHeight.clip.clipPath.clipPathUnits.clipRule.colorInterpolation.colorInterpolationFilters.colorProfile.colorRendering.contentScriptType.contentStyleType.cursor.cx.cy.d.decelerate.descent.diffuseConstant.direction.display.divisor.dominantBaseline.dur.dx.dy.edgeMode.elevation.enableBackground.end.exponent.externalResourcesRequired.fill.fillOpacity.fillRule.filter.filterRes.filterUnits.floodColor.floodOpacity.focusable.fontFamily.fontSize.fontSizeAdjust.fontStretch.fontStyle.fontVariant.fontWeight.format.from.fx.fy.g1.g2.glyphName.glyphOrientationHorizontal.glyphOrientationVertical.glyphRef.gradientTransform.gradientUnits.hanging.horizAdvX.horizOriginX.href.ideographic.imageRendering.in2.in.intercept.k1.k2.k3.k4.k.kernelMatrix.kernelUnitLength.kerning.keyPoints.keySplines.keyTimes.lengthAdjust.letterSpacing.lightingColor.limitingConeAngle.local.markerEnd.markerHeight.markerMid.markerStart.markerUnits.markerWidth.mask.maskContentUnits.maskUnits.mathematical.mode.numOctaves.offset.opacity.operator.order.orient.orientation.origin.overflow.overlinePosition.overlineThickness.paintOrder.panose1.pathLength.patternContentUnits.patternTransform.patternUnits.pointerEvents.pointsAtX.pointsAtY.pointsAtZ.preserveAlpha.preserveAspectRatio.primitiveUnits.r.radius.refX.refY.renderingIntent.repeatCount.repeatDur.requiredExtensions.requiredFeatures.restart.result.rotate.rx.ry.seed.shapeRendering.slope.spacing.specularConstant.specularExponent.speed.spreadMethod.startOffset.stdDeviation.stemh.stemv.stitchTiles.stopColor.stopOpacity.strikethroughPosition.strikethroughThickness.string.stroke.strokeDasharray.strokeDashoffset.strokeLinecap.strokeLinejoin.strokeMiterlimit.strokeOpacity.strokeWidth.surfaceScale.systemLanguage.tableValues.targetX.targetY.textAnchor.textDecoration.textLength.textRendering.to.transform.u1.u2.underlinePosition.underlineThickness.unicode.unicodeBidi.unicodeRange.unitsPerEm.vAlphabetic.values.vectorEffect.version.vertAdvY.vertOriginX.vertOriginY.vHanging.vIdeographic.viewTarget.visibility.vMathematical.widths.wordSpacing.writingMode.x1.x2.x.xChannelSelector.xHeight.xlinkActuate.xlinkArcrole.xlinkHref.xlinkRole.xlinkShow.xlinkTitle.xlinkType.xmlBase.xmlLang.xmlns.xmlnsXlink.xmlSpace.y1.y2.y.yChannelSelector.z.zoomAndPan.ref.key.angle".split("."));
function De(e) {
	return typeof e == "string" && Ee.has(e);
}
function Oe(e) {
	return typeof e == "string" && e.startsWith("data-");
}
function ke(e) {
	if (typeof e != "object" || !e) return {};
	var t = {};
	for (var n in e) Object.prototype.hasOwnProperty.call(e, n) && (De(n) || Oe(n)) && (t[n] = e[n]);
	return t;
}
function Ae(e) {
	if (e == null) return null;
	if (/*#__PURE__*/ (0, C.isValidElement)(e) && typeof e.props == "object" && e.props !== null) {
		var t = e.props;
		return ke(t);
	}
	return typeof e == "object" && !Array.isArray(e) ? ke(e) : null;
}
//#endregion
//#region node_modules/recharts/es6/util/svgPropertiesAndEvents.js
function je(e) {
	var t = {};
	for (var n in e) Object.prototype.hasOwnProperty.call(e, n) && (De(n) || Oe(n) || Te(n)) && (t[n] = e[n]);
	return t;
}
//#endregion
//#region node_modules/recharts/es6/container/Surface.js
var Me = [
	"children",
	"width",
	"height",
	"viewBox",
	"className",
	"style",
	"title",
	"desc"
];
function Ne() {
	return Ne = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, Ne.apply(null, arguments);
}
function Pe(e, t) {
	if (e == null) return {};
	var n, r, i = Fe(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function Fe(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var Ie = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.children, r = e.width, i = e.height, a = e.viewBox, o = e.className, s = e.style, c = e.title, l = e.desc, u = Pe(e, Me), d = a || {
		width: r,
		height: i,
		x: 0,
		y: 0
	}, f = Ce("recharts-surface", o);
	return /*#__PURE__*/ C.createElement("svg", Ne({}, je(u), {
		className: f,
		width: r,
		height: i,
		style: s,
		viewBox: `${d.x} ${d.y} ${d.width} ${d.height}`,
		ref: t
	}), /*#__PURE__*/ C.createElement("title", null, c), /*#__PURE__*/ C.createElement("desc", null, l), n);
}), Le = ["children", "className"];
function Re() {
	return Re = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, Re.apply(null, arguments);
}
function ze(e, t) {
	if (e == null) return {};
	var n, r, i = Be(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function Be(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var Ve = /*#__PURE__*/ C.forwardRef((e, t) => {
	var n = e.children, r = e.className, i = ze(e, Le), a = Ce("recharts-layer", r);
	return /*#__PURE__*/ C.createElement("g", Re({ className: a }, je(i), { ref: t }), n);
}), He = /*#__PURE__*/ (0, C.createContext)(null);
//#endregion
//#region node_modules/d3-shape/src/constant.js
function Ue(e) {
	return function() {
		return e;
	};
}
//#endregion
//#region node_modules/d3-path/src/path.js
var We = Math.PI, Ge = 2 * We, Ke = 1e-6, qe = Ge - Ke;
function Je(e) {
	this._ += e[0];
	for (let t = 1, n = e.length; t < n; ++t) this._ += arguments[t] + e[t];
}
function Ye(e) {
	let t = Math.floor(e);
	if (!(t >= 0)) throw Error(`invalid digits: ${e}`);
	if (t > 15) return Je;
	let n = 10 ** t;
	return function(e) {
		this._ += e[0];
		for (let t = 1, r = e.length; t < r; ++t) this._ += Math.round(arguments[t] * n) / n + e[t];
	};
}
var Xe = class {
	constructor(e) {
		this._x0 = this._y0 = this._x1 = this._y1 = null, this._ = "", this._append = e == null ? Je : Ye(e);
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
		else if (d > Ke) if (!(Math.abs(u * s - c * l) > Ke) || !i) this._append`L${this._x1 = e},${this._y1 = t}`;
		else {
			let f = n - a, p = r - o, m = s * s + c * c, h = f * f + p * p, g = Math.sqrt(m), _ = Math.sqrt(d), v = i * Math.tan((We - Math.acos((m + d - h) / (2 * g * _))) / 2), y = v / _, b = v / g;
			Math.abs(y - 1) > Ke && this._append`L${e + y * l},${t + y * u}`, this._append`A${i},${i},0,0,${+(u * f > l * p)},${this._x1 = e + b * s},${this._y1 = t + b * c}`;
		}
	}
	arc(e, t, n, r, i, a) {
		if (e = +e, t = +t, n = +n, a = !!a, n < 0) throw Error(`negative radius: ${n}`);
		let o = n * Math.cos(r), s = n * Math.sin(r), c = e + o, l = t + s, u = 1 ^ a, d = a ? r - i : i - r;
		this._x1 === null ? this._append`M${c},${l}` : (Math.abs(this._x1 - c) > Ke || Math.abs(this._y1 - l) > Ke) && this._append`L${c},${l}`, n && (d < 0 && (d = d % Ge + Ge), d > qe ? this._append`A${n},${n},0,1,${u},${e - o},${t - s}A${n},${n},0,1,${u},${this._x1 = c},${this._y1 = l}` : d > Ke && this._append`A${n},${n},0,${+(d >= We)},${u},${this._x1 = e + n * Math.cos(i)},${this._y1 = t + n * Math.sin(i)}`);
	}
	rect(e, t, n, r) {
		this._append`M${this._x0 = this._x1 = +e},${this._y0 = this._y1 = +t}h${n = +n}v${+r}h${-n}Z`;
	}
	toString() {
		return this._;
	}
};
function Ze() {
	return new Xe();
}
Ze.prototype = Xe.prototype;
//#endregion
//#region node_modules/d3-shape/src/path.js
function Qe(e) {
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
	}, () => new Xe(t);
}
Array.prototype.slice;
function $e(e) {
	return typeof e == "object" && "length" in e ? e : Array.from(e);
}
//#endregion
//#region node_modules/d3-shape/src/curve/linear.js
function et(e) {
	this._context = e;
}
et.prototype = {
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
function tt(e) {
	return new et(e);
}
//#endregion
//#region node_modules/d3-shape/src/point.js
function nt(e) {
	return e[0];
}
function rt(e) {
	return e[1];
}
//#endregion
//#region node_modules/d3-shape/src/line.js
function it(e, t) {
	var n = Ue(!0), r = null, i = tt, a = null, o = Qe(s);
	e = typeof e == "function" ? e : e === void 0 ? nt : Ue(e), t = typeof t == "function" ? t : t === void 0 ? rt : Ue(t);
	function s(s) {
		var c, l = (s = $e(s)).length, u, d = !1, f;
		for (r == null && (a = i(f = o())), c = 0; c <= l; ++c) !(c < l && n(u = s[c], c, s)) === d && ((d = !d) ? a.lineStart() : a.lineEnd()), d && a.point(+e(u, c, s), +t(u, c, s));
		if (f) return a = null, f + "" || null;
	}
	return s.x = function(t) {
		return arguments.length ? (e = typeof t == "function" ? t : Ue(+t), s) : e;
	}, s.y = function(e) {
		return arguments.length ? (t = typeof e == "function" ? e : Ue(+e), s) : t;
	}, s.defined = function(e) {
		return arguments.length ? (n = typeof e == "function" ? e : Ue(!!e), s) : n;
	}, s.curve = function(e) {
		return arguments.length ? (i = e, r != null && (a = i(r)), s) : i;
	}, s.context = function(e) {
		return arguments.length ? (e == null ? r = a = null : a = i(r = e), s) : r;
	}, s;
}
//#endregion
//#region node_modules/d3-shape/src/area.js
function at(e, t, n) {
	var r = null, i = Ue(!0), a = null, o = tt, s = null, c = Qe(l);
	e = typeof e == "function" ? e : e === void 0 ? nt : Ue(+e), t = typeof t == "function" ? t : Ue(t === void 0 ? 0 : +t), n = typeof n == "function" ? n : n === void 0 ? rt : Ue(+n);
	function l(l) {
		var u, d, f, p = (l = $e(l)).length, m, h = !1, g, _ = Array(p), v = Array(p);
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
		return it().defined(i).curve(o).context(a);
	}
	return l.x = function(t) {
		return arguments.length ? (e = typeof t == "function" ? t : Ue(+t), r = null, l) : e;
	}, l.x0 = function(t) {
		return arguments.length ? (e = typeof t == "function" ? t : Ue(+t), l) : e;
	}, l.x1 = function(e) {
		return arguments.length ? (r = e == null ? null : typeof e == "function" ? e : Ue(+e), l) : r;
	}, l.y = function(e) {
		return arguments.length ? (t = typeof e == "function" ? e : Ue(+e), n = null, l) : t;
	}, l.y0 = function(e) {
		return arguments.length ? (t = typeof e == "function" ? e : Ue(+e), l) : t;
	}, l.y1 = function(e) {
		return arguments.length ? (n = e == null ? null : typeof e == "function" ? e : Ue(+e), l) : n;
	}, l.lineX0 = l.lineY0 = function() {
		return u().x(e).y(t);
	}, l.lineY1 = function() {
		return u().x(e).y(n);
	}, l.lineX1 = function() {
		return u().x(r).y(t);
	}, l.defined = function(e) {
		return arguments.length ? (i = typeof e == "function" ? e : Ue(!!e), l) : i;
	}, l.curve = function(e) {
		return arguments.length ? (o = e, a != null && (s = o(a)), l) : o;
	}, l.context = function(e) {
		return arguments.length ? (e == null ? a = s = null : s = o(a = e), l) : a;
	}, l;
}
//#endregion
//#region node_modules/d3-shape/src/curve/bump.js
var ot = class {
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
function st(e) {
	return new ot(e, !0);
}
function ct(e) {
	return new ot(e, !1);
}
//#endregion
//#region node_modules/d3-shape/src/noop.js
function lt() {}
//#endregion
//#region node_modules/d3-shape/src/curve/basis.js
function ut(e, t, n) {
	e._context.bezierCurveTo((2 * e._x0 + e._x1) / 3, (2 * e._y0 + e._y1) / 3, (e._x0 + 2 * e._x1) / 3, (e._y0 + 2 * e._y1) / 3, (e._x0 + 4 * e._x1 + t) / 6, (e._y0 + 4 * e._y1 + n) / 6);
}
function dt(e) {
	this._context = e;
}
dt.prototype = {
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
			case 3: ut(this, this._x1, this._y1);
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
				ut(this, e, t);
				break;
		}
		this._x0 = this._x1, this._x1 = e, this._y0 = this._y1, this._y1 = t;
	}
};
function ft(e) {
	return new dt(e);
}
//#endregion
//#region node_modules/d3-shape/src/curve/basisClosed.js
function pt(e) {
	this._context = e;
}
pt.prototype = {
	areaStart: lt,
	areaEnd: lt,
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
				ut(this, e, t);
				break;
		}
		this._x0 = this._x1, this._x1 = e, this._y0 = this._y1, this._y1 = t;
	}
};
function mt(e) {
	return new pt(e);
}
//#endregion
//#region node_modules/d3-shape/src/curve/basisOpen.js
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
				ut(this, e, t);
				break;
		}
		this._x0 = this._x1, this._x1 = e, this._y0 = this._y1, this._y1 = t;
	}
};
function gt(e) {
	return new ht(e);
}
//#endregion
//#region node_modules/d3-shape/src/curve/linearClosed.js
function _t(e) {
	this._context = e;
}
_t.prototype = {
	areaStart: lt,
	areaEnd: lt,
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
function vt(e) {
	return new _t(e);
}
//#endregion
//#region node_modules/d3-shape/src/curve/monotone.js
function yt(e) {
	return e < 0 ? -1 : 1;
}
function bt(e, t, n) {
	var r = e._x1 - e._x0, i = t - e._x1, a = (e._y1 - e._y0) / (r || i < 0 && -0), o = (n - e._y1) / (i || r < 0 && -0), s = (a * i + o * r) / (r + i);
	return (yt(a) + yt(o)) * Math.min(Math.abs(a), Math.abs(o), .5 * Math.abs(s)) || 0;
}
function xt(e, t) {
	var n = e._x1 - e._x0;
	return n ? (3 * (e._y1 - e._y0) / n - t) / 2 : t;
}
function St(e, t, n) {
	var r = e._x0, i = e._y0, a = e._x1, o = e._y1, s = (a - r) / 3;
	e._context.bezierCurveTo(r + s, i + s * t, a - s, o - s * n, a, o);
}
function Ct(e) {
	this._context = e;
}
Ct.prototype = {
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
				St(this, this._t0, xt(this, this._t0));
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
					this._point = 3, St(this, xt(this, n = bt(this, e, t)), n);
					break;
				default:
					St(this, this._t0, n = bt(this, e, t));
					break;
			}
			this._x0 = this._x1, this._x1 = e, this._y0 = this._y1, this._y1 = t, this._t0 = n;
		}
	}
};
function wt(e) {
	this._context = new Tt(e);
}
(wt.prototype = Object.create(Ct.prototype)).point = function(e, t) {
	Ct.prototype.point.call(this, t, e);
};
function Tt(e) {
	this._context = e;
}
Tt.prototype = {
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
function Et(e) {
	return new Ct(e);
}
function Dt(e) {
	return new wt(e);
}
//#endregion
//#region node_modules/d3-shape/src/curve/natural.js
function Ot(e) {
	this._context = e;
}
Ot.prototype = {
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
		else for (var r = kt(e), i = kt(t), a = 0, o = 1; o < n; ++a, ++o) this._context.bezierCurveTo(r[0][a], i[0][a], r[1][a], i[1][a], e[o], t[o]);
		(this._line || this._line !== 0 && n === 1) && this._context.closePath(), this._line = 1 - this._line, this._x = this._y = null;
	},
	point: function(e, t) {
		this._x.push(+e), this._y.push(+t);
	}
};
function kt(e) {
	var t, n = e.length - 1, r, i = Array(n), a = Array(n), o = Array(n);
	for (i[0] = 0, a[0] = 2, o[0] = e[0] + 2 * e[1], t = 1; t < n - 1; ++t) i[t] = 1, a[t] = 4, o[t] = 4 * e[t] + 2 * e[t + 1];
	for (i[n - 1] = 2, a[n - 1] = 7, o[n - 1] = 8 * e[n - 1] + e[n], t = 1; t < n; ++t) r = i[t] / a[t - 1], a[t] -= r, o[t] -= r * o[t - 1];
	for (i[n - 1] = o[n - 1] / a[n - 1], t = n - 2; t >= 0; --t) i[t] = (o[t] - i[t + 1]) / a[t];
	for (a[n - 1] = (e[n] + i[n - 1]) / 2, t = 0; t < n - 1; ++t) a[t] = 2 * e[t + 1] - i[t + 1];
	return [i, a];
}
function At(e) {
	return new Ot(e);
}
//#endregion
//#region node_modules/d3-shape/src/curve/step.js
function jt(e, t) {
	this._context = e, this._t = t;
}
jt.prototype = {
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
function Mt(e) {
	return new jt(e, .5);
}
function Nt(e) {
	return new jt(e, 0);
}
function Pt(e) {
	return new jt(e, 1);
}
//#endregion
//#region node_modules/d3-shape/src/offset/none.js
function Ft(e, t) {
	if ((o = e.length) > 1) for (var n = 1, r, i, a = e[t[0]], o, s = a.length; n < o; ++n) for (i = a, a = e[t[n]], r = 0; r < s; ++r) a[r][1] += a[r][0] = isNaN(i[r][1]) ? i[r][0] : i[r][1];
}
//#endregion
//#region node_modules/d3-shape/src/order/none.js
function It(e) {
	for (var t = e.length, n = Array(t); --t >= 0;) n[t] = t;
	return n;
}
//#endregion
//#region node_modules/d3-shape/src/stack.js
function Lt(e, t) {
	return e[t];
}
function Rt(e) {
	let t = [];
	return t.key = e, t;
}
function zt() {
	var e = Ue([]), t = It, n = Ft, r = Lt;
	function i(i) {
		var a = Array.from(e.apply(this, arguments), Rt), o, s = a.length, c = -1, l;
		for (let e of i) for (o = 0, ++c; o < s; ++o) (a[o][c] = [0, +r(e, a[o].key, c, i)]).data = e;
		for (o = 0, l = $e(t(a)); o < s; ++o) a[l[o]].index = o;
		return n(a, l), a;
	}
	return i.keys = function(t) {
		return arguments.length ? (e = typeof t == "function" ? t : Ue(Array.from(t)), i) : e;
	}, i.value = function(e) {
		return arguments.length ? (r = typeof e == "function" ? e : Ue(+e), i) : r;
	}, i.order = function(e) {
		return arguments.length ? (t = e == null ? It : typeof e == "function" ? e : Ue(Array.from(e)), i) : t;
	}, i.offset = function(e) {
		return arguments.length ? (n = e == null ? Ft : e, i) : n;
	}, i;
}
//#endregion
//#region node_modules/d3-shape/src/offset/expand.js
function Bt(e, t) {
	if ((r = e.length) > 0) {
		for (var n, r, i = 0, a = e[0].length, o; i < a; ++i) {
			for (o = n = 0; n < r; ++n) o += e[n][i][1] || 0;
			if (o) for (n = 0; n < r; ++n) e[n][i][1] /= o;
		}
		Ft(e, t);
	}
}
//#endregion
//#region node_modules/d3-shape/src/offset/silhouette.js
function Vt(e, t) {
	if ((i = e.length) > 0) {
		for (var n = 0, r = e[t[0]], i, a = r.length; n < a; ++n) {
			for (var o = 0, s = 0; o < i; ++o) s += e[o][n][1] || 0;
			r[n][1] += r[n][0] = -s / 2;
		}
		Ft(e, t);
	}
}
//#endregion
//#region node_modules/d3-shape/src/offset/wiggle.js
function Ht(e, t) {
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
		i[r - 1][1] += i[r - 1][0] = n, Ft(e, t);
	}
}
//#endregion
//#region node_modules/es-toolkit/dist/_internal/isUnsafeProperty.mjs
function Ut(e) {
	return e === "__proto__";
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/isDeepKey.mjs
function Wt(e) {
	switch (typeof e) {
		case "number":
		case "symbol": return !1;
		case "string": return e.includes(".") || e.includes("[") || e.includes("]");
	}
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/toKey.mjs
function Gt(e) {
	var t;
	return typeof e == "string" || typeof e == "symbol" ? e : Object.is(e == null || (t = e.valueOf) == null ? void 0 : t.call(e), -0) ? "-0" : String(e);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/util/toString.mjs
function Kt(e) {
	if (e == null) return "";
	if (typeof e == "string") return e;
	if (Array.isArray(e)) return e.map(Kt).join(",");
	let t = String(e);
	return t === "0" && Object.is(Number(e), -0) ? "-0" : t;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/util/toPath.mjs
function F(e) {
	if (Array.isArray(e)) return e.map(Gt);
	if (typeof e == "symbol") return [e];
	e = Kt(e);
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
function qt(e, t, n) {
	if (e == null) return n;
	switch (typeof t) {
		case "string": {
			if (Ut(t)) return n;
			let r = e[t];
			return r === void 0 ? Wt(t) && !Object.hasOwn(e, t) ? qt(e, F(t), n) : n : r;
		}
		case "number":
		case "symbol": {
			typeof t == "number" && (t = Gt(t));
			let r = e[t];
			return r === void 0 ? n : r;
		}
		default: {
			if (Array.isArray(t)) return Jt(e, t, n);
			if (t = Object.is(t == null ? void 0 : t.valueOf(), -0) ? "-0" : String(t), Ut(t)) return n;
			let r = e[t];
			return r === void 0 ? n : r;
		}
	}
}
function Jt(e, t, n) {
	if (t.length === 0) return n;
	let r = e;
	for (let e = 0; e < t.length; e++) {
		if (r == null || Ut(t[e])) return n;
		r = r[t[e]];
	}
	return r === void 0 ? n : r;
}
//#endregion
//#region node_modules/recharts/es6/util/round.js
var Yt = 4;
function Xt(e) {
	var t = 10 ** (arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : Yt), n = Math.round(e * t) / t;
	return Object.is(n, -0) ? 0 : n;
}
function Zt(e) {
	var t = [...arguments].slice(1);
	return e.reduce((e, n, r) => {
		var i = t[r - 1];
		return typeof i == "string" ? e + i + n : i === void 0 ? e + n : e + Xt(i) + n;
	}, "");
}
//#endregion
//#region node_modules/recharts/es6/util/DataUtils.js
var Qt = (e) => e === 0 ? 0 : e > 0 ? 1 : -1, $t = (e) => typeof e == "number" && e != +e, en = (e) => typeof e == "string" && e.length > 1 && e.indexOf("%") === e.length - 1, I = (e) => (typeof e == "number" || e instanceof Number) && !$t(e), tn = (e) => I(e) || typeof e == "string", nn = 0, rn = (e) => {
	var t = ++nn;
	return `${e || ""}${t}`;
}, an = function(e, t) {
	var n = arguments.length > 2 && arguments[2] !== void 0 ? arguments[2] : 0, r = arguments.length > 3 && arguments[3] !== void 0 && arguments[3];
	if (!I(e) && typeof e != "string") return n;
	var i;
	if (en(e)) {
		if (t == null) return n;
		var a = e.indexOf("%");
		i = t * parseFloat(e.slice(0, a)) / 100;
	} else i = +e;
	return $t(i) && (i = n), r && t != null && i > t && (i = t), i;
}, on = (e) => {
	if (!Array.isArray(e)) return !1;
	for (var t = e.length, n = {}, r = 0; r < t; r++) if (!n[String(e[r])]) n[String(e[r])] = !0;
	else return !0;
	return !1;
};
function sn(e, t, n) {
	return I(e) && I(t) ? Xt(e + n * (t - e)) : t;
}
function cn(e, t, n) {
	if (!(!e || !e.length)) return e.find((e) => e && (typeof t == "function" ? t(e) : qt(e, t)) === n);
}
var ln = (e) => e == null, un = (e) => ln(e) ? e : `${e.charAt(0).toUpperCase()}${e.slice(1)}`;
function dn(e) {
	return e != null;
}
function fn() {}
//#endregion
//#region node_modules/recharts/es6/util/types.js
var pn = (e) => "radius" in e && "startAngle" in e && "endAngle" in e, mn = (e, t) => {
	if (!e || typeof e == "function" || typeof e == "boolean") return null;
	var n = e;
	if (/*#__PURE__*/ (0, C.isValidElement)(e) && (n = e.props), typeof n != "object" && typeof n != "function") return null;
	var r = {};
	return Object.keys(n).forEach((e) => {
		Te(e) && typeof n[e] == "function" && (r[e] = t || ((t) => n[e](n, t)));
	}), r;
}, hn = (e, t, n) => (r) => (e(t, n, r), null), gn = (e, t, n) => {
	if (e === null || typeof e != "object" && typeof e != "function") return null;
	var r = null;
	return Object.keys(e).forEach((i) => {
		var a = e[i];
		Te(i) && typeof a == "function" && (r || (r = {}), r[i] = hn(a, t, n));
	}), r;
};
//#endregion
//#region node_modules/recharts/es6/util/resolveDefaultProps.js
function _n(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function vn(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? _n(Object(n), !0).forEach(function(t) {
			yn(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : _n(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function yn(e, t, n) {
	return (t = bn(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function bn(e) {
	var t = xn(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function xn(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function Sn(e, t) {
	var n = vn({}, e), r = t;
	return Object.keys(t).reduce((e, t) => (e[t] === void 0 && r[t] !== void 0 && (e[t] = r[t]), e), n);
}
//#endregion
//#region node_modules/es-toolkit/dist/array/uniqBy.mjs
function Cn(e, t) {
	let n = /* @__PURE__ */ new Map();
	for (let r = 0; r < e.length; r++) {
		let i = e[r], a = t(i, r, e);
		n.has(a) || n.set(a, i);
	}
	return Array.from(n.values());
}
//#endregion
//#region node_modules/es-toolkit/dist/function/ary.mjs
function wn(e, t) {
	return function(...n) {
		return e.apply(this, n.slice(0, t));
	};
}
//#endregion
//#region node_modules/es-toolkit/dist/function/identity.mjs
function Tn(e) {
	return e;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/object/property.mjs
function En(e) {
	return function(t) {
		return qt(t, e);
	};
}
//#endregion
//#region node_modules/es-toolkit/dist/predicate/isPrimitive.mjs
function Dn(e) {
	return e == null || typeof e != "object" && typeof e != "function";
}
//#endregion
//#region node_modules/es-toolkit/dist/predicate/isTypedArray.mjs
function On(e) {
	return ArrayBuffer.isView(e) && !(e instanceof DataView);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/getSymbols.mjs
function kn(e) {
	return Object.getOwnPropertySymbols(e).filter((t) => Object.prototype.propertyIsEnumerable.call(e, t));
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/getTag.mjs
function An(e) {
	return e == null ? e === void 0 ? "[object Undefined]" : "[object Null]" : Object.prototype.toString.call(e);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/tags.mjs
var jn = "[object RegExp]", Mn = "[object String]", Nn = "[object Number]", Pn = "[object Boolean]", Fn = "[object Arguments]", In = "[object Symbol]", Ln = "[object Date]", Rn = "[object Map]", zn = "[object Set]", Bn = "[object Array]", Vn = "[object ArrayBuffer]", Hn = "[object Object]", Un = "[object DataView]", Wn = "[object Uint8Array]", Gn = "[object Uint8ClampedArray]", Kn = "[object Uint16Array]", qn = "[object Uint32Array]", Jn = "[object Int8Array]", Yn = "[object Int16Array]", Xn = "[object Int32Array]", Zn = "[object Float32Array]", Qn = "[object Float64Array]", $n = typeof globalThis == "object" && globalThis || typeof window == "object" && window || typeof self == "object" && self || typeof global == "object" && global || (function() {
	return this;
})();
//#endregion
//#region node_modules/es-toolkit/dist/predicate/isBuffer.mjs
function er(e) {
	return $n.Buffer !== void 0 && $n.Buffer.isBuffer(e);
}
//#endregion
//#region node_modules/es-toolkit/dist/object/cloneDeepWith.mjs
function tr(e, t) {
	return nr(e, void 0, e, /* @__PURE__ */ new Map(), t);
}
function nr(e, t, n, r = /* @__PURE__ */ new Map(), i = void 0) {
	let a = i == null ? void 0 : i(e, t, n, r);
	if (a !== void 0) return a;
	if (Dn(e)) return e;
	if (r.has(e)) return r.get(e);
	if (Array.isArray(e)) {
		let t = Array(e.length);
		r.set(e, t);
		for (let a = 0; a < e.length; a++) t[a] = nr(e[a], a, n, r, i);
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
		for (let [a, o] of e) t.set(a, nr(o, a, n, r, i));
		return t;
	}
	if (e instanceof Set) {
		let t = /* @__PURE__ */ new Set();
		r.set(e, t);
		for (let a of e) t.add(nr(a, void 0, n, r, i));
		return t;
	}
	if (er(e)) return e.subarray();
	if (On(e)) {
		let t = new (Object.getPrototypeOf(e)).constructor(e.length);
		r.set(e, t);
		for (let a = 0; a < e.length; a++) t[a] = nr(e[a], a, n, r, i);
		return t;
	}
	if (e instanceof ArrayBuffer || typeof SharedArrayBuffer < "u" && e instanceof SharedArrayBuffer) return e.slice(0);
	if (e instanceof DataView) {
		let t = new DataView(e.buffer.slice(0), e.byteOffset, e.byteLength);
		return r.set(e, t), rr(t, e, n, r, i), t;
	}
	if (typeof File < "u" && e instanceof File) {
		let t = new File([e], e.name, { type: e.type });
		return r.set(e, t), rr(t, e, n, r, i), t;
	}
	if (typeof Blob < "u" && e instanceof Blob) {
		let t = new Blob([e], { type: e.type });
		return r.set(e, t), rr(t, e, n, r, i), t;
	}
	if (e instanceof Error) {
		let t = structuredClone(e);
		return r.set(e, t), t.message = e.message, t.name = e.name, t.stack = e.stack, t.cause = e.cause, t.constructor = e.constructor, rr(t, e, n, r, i), t;
	}
	if (e instanceof Boolean) {
		let t = new Boolean(e.valueOf());
		return r.set(e, t), rr(t, e, n, r, i), t;
	}
	if (e instanceof Number) {
		let t = new Number(e.valueOf());
		return r.set(e, t), rr(t, e, n, r, i), t;
	}
	if (e instanceof String) {
		let t = new String(e.valueOf());
		return r.set(e, t), rr(t, e, n, r, i), t;
	}
	if (typeof e == "object" && ir(e)) {
		let t = Object.create(Object.getPrototypeOf(e));
		return r.set(e, t), rr(t, e, n, r, i), t;
	}
	return e;
}
function rr(e, t, n = e, r, i) {
	let a = [...Object.keys(t), ...kn(t)];
	for (let o = 0; o < a.length; o++) {
		let s = a[o], c = Object.getOwnPropertyDescriptor(e, s);
		(c == null || c.writable) && (e[s] = nr(t[s], s, n, r, i));
	}
}
function ir(e) {
	switch (An(e)) {
		case Fn:
		case Bn:
		case Vn:
		case Un:
		case Pn:
		case Ln:
		case Zn:
		case Qn:
		case Jn:
		case Yn:
		case Xn:
		case Rn:
		case Nn:
		case Hn:
		case jn:
		case zn:
		case Mn:
		case In:
		case Wn:
		case Gn:
		case Kn:
		case qn: return !0;
		default: return !1;
	}
}
//#endregion
//#region node_modules/es-toolkit/dist/object/cloneDeep.mjs
function ar(e) {
	return nr(e, void 0, e, /* @__PURE__ */ new Map(), void 0);
}
//#endregion
//#region node_modules/es-toolkit/dist/_internal/isEqualsSameValueZero.mjs
function or(e, t) {
	return e === t || Number.isNaN(e) && Number.isNaN(t);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isObject.mjs
function sr(e) {
	return e !== null && (typeof e == "object" || typeof e == "function");
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isMatchWith.mjs
function cr(e, t, n) {
	return typeof n == "function" ? lr(e, t, function e(t, r, i, a, o, s) {
		let c = n(t, r, i, a, o, s);
		return c === void 0 ? lr(t, r, e, s, !1) : !!c;
	}, /* @__PURE__ */ new Map(), !0) : cr(e, t, () => void 0);
}
function lr(e, t, n, r, i = !1) {
	if (t === e) return !0;
	switch (typeof t) {
		case "object": return ur(e, t, n, r);
		case "function": return Object.keys(t).length > 0 ? lr(e, { ...t }, n, r, i) : or(e, t);
		default: return sr(e) && i ? typeof t != "string" || t === "" : or(e, t);
	}
}
function ur(e, t, n, r) {
	if (t == null) return !0;
	if (Array.isArray(t)) return fr(e, t, n, r);
	if (t instanceof Map) return dr(e, t, n, r);
	if (t instanceof Set) return pr(e, t, n, r);
	let i = Object.keys(t);
	if (e == null || Dn(e)) return i.length === 0;
	if (i.length === 0) return !0;
	if (r != null && r.has(t)) return r.get(t) === e;
	r == null || r.set(t, e);
	try {
		for (let a = 0; a < i.length; a++) {
			let o = i[a];
			if (!Dn(e) && !(o in e) || t[o] === void 0 && e[o] !== void 0 || t[o] === null && e[o] !== null || !n(e[o], t[o], o, e, t, r)) return !1;
		}
		return !0;
	} finally {
		r == null || r.delete(t);
	}
}
function dr(e, t, n, r) {
	if (t.size === 0) return !0;
	if (!(e instanceof Map)) return !1;
	for (let [i, a] of t.entries()) if (n(e.get(i), a, i, e, t, r) === !1) return !1;
	return !0;
}
function fr(e, t, n, r) {
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
function pr(e, t, n, r) {
	return t.size === 0 || e instanceof Set && fr([...e], [...t], n, r);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isMatch.mjs
function mr(e, t) {
	return cr(e, t, () => void 0);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/matches.mjs
function hr(e) {
	return e = ar(e), (t) => mr(t, e);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/object/cloneDeepWith.mjs
function gr(e, t) {
	return tr(e, (n, r, i, a) => {
		let o = t == null ? void 0 : t(n, r, i, a);
		if (o !== void 0) return o;
		if (typeof e == "object") {
			if (An(e) === "[object Object]" && typeof e.constructor != "function") {
				let t = {};
				return a.set(e, t), rr(t, e, i, a), t;
			}
			switch (Object.prototype.toString.call(e)) {
				case Nn:
				case Mn:
				case Pn: {
					let t = new e.constructor(e == null ? void 0 : e.valueOf());
					return rr(t, e), t;
				}
				case Fn: {
					let t = {};
					return rr(t, e), t.length = e.length, t[Symbol.iterator] = e[Symbol.iterator], t;
				}
				default: return;
			}
		}
	});
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/object/cloneDeep.mjs
function _r(e) {
	return gr(e);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/isIndex.mjs
var vr = /^(?:0|[1-9]\d*)$/;
function yr(e, t = 2 ** 53 - 1) {
	switch (typeof e) {
		case "number": return Number.isInteger(e) && e >= 0 && e < t;
		case "symbol": return !1;
		case "string": return vr.test(e);
	}
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isArguments.mjs
function br(e) {
	return typeof e == "object" && !!e && An(e) === "[object Arguments]";
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/object/has.mjs
function xr(e, t) {
	let n;
	if (n = Array.isArray(t) ? t : typeof t == "string" && Wt(t) && (e == null ? void 0 : e[t]) == null ? F(t) : [t], n.length === 0) return !1;
	let r = e;
	for (let e = 0; e < n.length; e++) {
		let t = n[e];
		if ((r == null || !Object.hasOwn(r, t)) && !((Array.isArray(r) || br(r)) && yr(t) && t < r.length)) return !1;
		r = r[t];
	}
	return !0;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/matchesProperty.mjs
function Sr(e, t) {
	switch (typeof e) {
		case "object":
			Object.is(e == null ? void 0 : e.valueOf(), -0) && (e = "-0");
			break;
		case "number":
			e = Gt(e);
			break;
	}
	return t = _r(t), function(n) {
		let r = qt(n, e);
		return r === void 0 ? xr(n, e) : t === void 0 ? r === void 0 : mr(r, t);
	};
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/util/iteratee.mjs
function Cr(e) {
	if (e == null) return Tn;
	switch (typeof e) {
		case "function": return e;
		case "object": return Array.isArray(e) && e.length === 2 ? Sr(e[0], e[1]) : hr(e);
		case "string":
		case "symbol":
		case "number": return En(e);
	}
}
//#endregion
//#region node_modules/es-toolkit/dist/predicate/isLength.mjs
function wr(e) {
	return Number.isSafeInteger(e) && e >= 0;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isArrayLike.mjs
function Tr(e) {
	return e != null && typeof e != "function" && wr(e.length);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isObjectLike.mjs
function Er(e) {
	return typeof e == "object" && !!e;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isArrayLikeObject.mjs
function Dr(e) {
	return Er(e) && Tr(e);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/array/uniqBy.mjs
function Or(e, t = Tn) {
	return Dr(e) ? Cn(Array.from(e), wn(Cr(t), 1)) : [];
}
//#endregion
//#region node_modules/recharts/es6/util/payload/getUniqPayload.js
function kr(e, t, n) {
	return t === !0 ? Or(e, n) : typeof t == "function" ? Or(e, t) : e;
}
//#endregion
//#region node_modules/use-sync-external-store/cjs/use-sync-external-store-shim.production.js
var Ar = /* @__PURE__ */ o(((e) => {
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
})), jr = /* @__PURE__ */ o(((e, t) => {
	t.exports = Ar();
})), Mr = /* @__PURE__ */ o(((e) => {
	var t = d(), n = jr();
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
})), Nr = /* @__PURE__ */ o(((e, t) => {
	t.exports = Mr();
})), Pr = /*#__PURE__*/ (0, C.createContext)(null), Fr = Nr(), Ir = (e) => e, Lr = () => {
	var e = (0, C.useContext)(Pr);
	return e ? e.store.dispatch : Ir;
}, Rr = () => {}, zr = () => Rr, Br = (e, t) => e === t;
function L(e) {
	var t = (0, C.useContext)(Pr), n = (0, C.useMemo)(() => t ? (t) => {
		if (t != null) return e(t);
	} : Rr, [t, e]);
	return (0, Fr.useSyncExternalStoreWithSelector)(t ? t.subscription.addNestedSub : zr, t ? t.store.getState : Rr, t ? t.store.getState : Rr, n, Br);
}
//#endregion
//#region \0@oxc-project+runtime@0.139.0/helpers/esm/typeof.js
function Vr(e) {
	"@babel/helpers - typeof";
	return Vr = typeof Symbol == "function" && typeof Symbol.iterator == "symbol" ? function(e) {
		return typeof e;
	} : function(e) {
		return e && typeof Symbol == "function" && e.constructor === Symbol && e !== Symbol.prototype ? "symbol" : typeof e;
	}, Vr(e);
}
//#endregion
//#region \0@oxc-project+runtime@0.139.0/helpers/esm/toPrimitive.js
function Hr(e, t) {
	if (Vr(e) != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (Vr(r) != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
//#endregion
//#region \0@oxc-project+runtime@0.139.0/helpers/esm/toPropertyKey.js
function Ur(e) {
	var t = Hr(e, "string");
	return Vr(t) == "symbol" ? t : t + "";
}
//#endregion
//#region \0@oxc-project+runtime@0.139.0/helpers/esm/defineProperty.js
function Wr(e, t, n) {
	return (t = Ur(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
//#endregion
//#region node_modules/reselect/dist/reselect.mjs
function Gr(e, t = `expected a function, instead received ${typeof e}`) {
	if (typeof e != "function") throw TypeError(t);
}
function Kr(e, t = "expected all items to be functions, instead received the following types: ") {
	if (!e.every((e) => typeof e == "function")) {
		let n = e.map((e) => typeof e == "function" ? `function ${e.name || "unnamed"}()` : typeof e).join(", ");
		throw TypeError(`${t}[${n}]`);
	}
}
var qr = (e) => Array.isArray(e) ? e : [e];
function Jr(e) {
	let t = Array.isArray(e[0]) ? e[0] : e;
	return Kr(t, "createSelector expects all input-selectors to be functions, but received the following types: "), t;
}
function Yr(e, t) {
	let n = [], { length: r } = e;
	for (let i = 0; i < r; i++) n.push(e[i].apply(null, t));
	return n;
}
var Xr = class {
	constructor(e) {
		this.value = e;
	}
	deref() {
		return this.value;
	}
}, Zr = typeof WeakRef > "u" ? Xr : WeakRef, Qr = 0, $r = 1;
function ei() {
	return {
		s: Qr,
		v: void 0,
		o: null,
		p: null
	};
}
function ti(e) {
	return e instanceof Zr ? e.deref() : e;
}
function ni(e, t = {}) {
	let n = ei(), { resultEqualityCheck: r } = t, i, a = 0;
	function o() {
		let t = n, { length: o } = arguments;
		for (let e = 0, n = o; e < n; e++) {
			let n = arguments[e];
			if (typeof n == "function" || typeof n == "object" && n) {
				let e = t.o;
				e === null && (t.o = e = /* @__PURE__ */ new WeakMap());
				let r = e.get(n);
				r === void 0 ? (t = ei(), e.set(n, t)) : t = r;
			} else {
				let e = t.p;
				e === null && (t.p = e = /* @__PURE__ */ new Map());
				let r = e.get(n);
				r === void 0 ? (t = ei(), e.set(n, t)) : t = r;
			}
		}
		let s = t, c;
		if (t.s === $r) c = t.v;
		else if (c = e.apply(null, arguments), a++, r) {
			let e = ti(i);
			e != null && r(e, c) && (c = e, a !== 0 && a--), i = typeof c == "object" && c || typeof c == "function" ? /* @__PURE__ */ new Zr(c) : c;
		}
		return s.s = $r, s.v = c, c;
	}
	return o.clearCache = () => {
		n = ei(), o.resetResultsCount();
	}, o.resultsCount = () => a, o.resetResultsCount = () => {
		a = 0;
	}, o;
}
function ri(e, ...t) {
	let n = typeof e == "function" ? {
		memoize: e,
		memoizeOptions: t
	} : e, r = (...e) => {
		let t = 0, r = 0, i, a = {}, o = e.pop();
		typeof o == "object" && (a = o, o = e.pop()), Gr(o, `createSelector expects an output function after the inputs, but received: [${typeof o}]`);
		let { memoize: s, memoizeOptions: c = [], argsMemoize: l = ni, argsMemoizeOptions: u = [] } = {
			...n,
			...a
		}, d = qr(c), f = qr(u), p = Jr(e), m = s(function() {
			return t++, o.apply(null, arguments);
		}, ...d), h = l(function() {
			r++;
			let e = Yr(p, arguments);
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
var R = /* @__PURE__ */ ri(ni);
//#endregion
//#region node_modules/es-toolkit/dist/array/flatten.mjs
function ii(e, t = 1) {
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
function ai(e, t, n) {
	return sr(n) && (typeof t == "number" && Tr(n) && yr(t) && t < n.length || typeof t == "string" && t in n) ? or(n[t], e) : !1;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/compareValues.mjs
function oi(e) {
	return typeof e == "symbol" ? 1 : e === null ? 2 : e === void 0 ? 3 : e === e ? 0 : 4;
}
var si = (e, t, n) => {
	if (e !== t) {
		let r = oi(e), i = oi(t);
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
function ci(e) {
	return typeof e == "symbol" || e instanceof Symbol;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/isKey.mjs
var li = /\.|\[(?:[^[\]]*|(["'])(?:(?!\1)[^\\]|\\.)*?\1)\]/, ui = /^\w*$/;
function di(e, t) {
	return Array.isArray(e) ? !1 : typeof e == "number" || typeof e == "boolean" || e == null || ci(e) ? !0 : typeof e == "string" && (ui.test(e) || !li.test(e)) || t != null && Object.hasOwn(t, e);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/array/orderBy.mjs
function fi(e, t, n, r) {
	if (e == null) return [];
	n = r ? void 0 : n, Array.isArray(e) || (e = Object.values(e)), Array.isArray(t) || (t = t == null ? [null] : [t]), t.length === 0 && (t = [null]), Array.isArray(n) || (n = n == null ? [] : [n]), n = n.map((e) => String(e));
	let i = (e, t) => {
		let n = e;
		for (let e = 0; e < t.length && n != null; ++e) n = n[t[e]];
		return n;
	}, a = (e, t) => t == null || e == null ? t : typeof e == "object" && "key" in e ? Object.hasOwn(t, e.key) ? t[e.key] : i(t, e.path) : typeof e == "function" ? e(t) : Array.isArray(e) ? i(t, e) : typeof t == "object" ? t[e] : t, o = t.map((e) => (Array.isArray(e) && e.length === 1 && (e = e[0]), e == null || typeof e == "function" || Array.isArray(e) || di(e) ? e : {
		key: e,
		path: F(e)
	}));
	return e.map((e) => ({
		original: e,
		criteria: o.map((t) => a(t, e))
	})).slice().sort((e, t) => {
		for (let r = 0; r < o.length; r++) {
			let i = si(e.criteria[r], t.criteria[r], n[r]);
			if (i !== 0) return i;
		}
		return 0;
	}).map((e) => e.original);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/array/sortBy.mjs
function pi(e, ...t) {
	let n = t.length;
	return n > 1 && ai(e, t[0], t[1]) ? t = [] : n > 2 && ai(t[0], t[1], t[2]) && (t = [t[0]]), fi(e, ii(t), ["asc"]);
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/legendSelectors.js
var mi = (e) => e.legend.settings, hi = (e) => e.legend.size;
R([(e) => e.legend.payload, mi], (e, t) => {
	var n = t.itemSorter, r = e.flat(1);
	return n ? pi(r, n) : r;
});
//#endregion
//#region node_modules/recharts/es6/util/useElementOffset.js
function gi(e, t) {
	return xi(e) || bi(e, t) || vi(e, t) || _i();
}
function _i() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function vi(e, t) {
	if (e) {
		if (typeof e == "string") return yi(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? yi(e, t) : void 0;
	}
}
function yi(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function bi(e, t) {
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
function xi(e) {
	if (Array.isArray(e)) return e;
}
var Si = 1;
function Ci(e, t) {
	return Math.abs(e.height - t.height) > Si || Math.abs(e.left - t.left) > Si || Math.abs(e.top - t.top) > Si || Math.abs(e.width - t.width) > Si;
}
function wi(e) {
	var t = e.getBoundingClientRect();
	return {
		height: t.height,
		left: t.left,
		top: t.top,
		width: t.width
	};
}
function Ti() {
	var e = arguments.length > 0 && arguments[0] !== void 0 ? arguments[0] : [], t = gi((0, C.useState)({
		height: 0,
		left: 0,
		top: 0,
		width: 0
	}), 2), n = t[0], r = t[1], i = (0, C.useRef)(null), a = (0, C.useRef)(n);
	a.current = n;
	var o = (0, C.useCallback)((e) => {
		if (i.current != null && (i.current.disconnect(), i.current = null), e != null) {
			var t = wi(e);
			if (Ci(t, a.current) && r(t), typeof ResizeObserver < "u") {
				var n = new ResizeObserver(() => {
					var t = wi(e);
					Ci(t, a.current) && r(t);
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
function Ei(e) {
	return `Minified Redux error #${e}; visit https://redux.js.org/Errors?code=${e} for the full message or use the non-minified dev environment for full errors. `;
}
var Di = typeof Symbol == "function" && Symbol.observable || "@@observable", Oi = () => Math.random().toString(36).substring(7).split("").join("."), ki = {
	INIT: `@@redux/INIT${/* @__PURE__ */ Oi()}`,
	REPLACE: `@@redux/REPLACE${/* @__PURE__ */ Oi()}`,
	PROBE_UNKNOWN_ACTION: () => `@@redux/PROBE_UNKNOWN_ACTION${Oi()}`
};
function Ai(e) {
	if (typeof e != "object" || !e) return !1;
	let t = e;
	for (; Object.getPrototypeOf(t) !== null;) t = Object.getPrototypeOf(t);
	return Object.getPrototypeOf(e) === t || Object.getPrototypeOf(e) === null;
}
function ji(e, t, n) {
	if (typeof e != "function") throw Error(Ei(2));
	if (typeof t == "function" && typeof n == "function" || typeof n == "function" && typeof arguments[3] == "function") throw Error(Ei(0));
	if (typeof t == "function" && n === void 0 && (n = t, t = void 0), n !== void 0) {
		if (typeof n != "function") throw Error(Ei(1));
		return n(ji)(e, t);
	}
	let r = e, i = t, a = /* @__PURE__ */ new Map(), o = a, s = 0, c = !1;
	function l() {
		o === a && (o = /* @__PURE__ */ new Map(), a.forEach((e, t) => {
			o.set(t, e);
		}));
	}
	function u() {
		if (c) throw Error(Ei(3));
		return i;
	}
	function d(e) {
		if (typeof e != "function") throw Error(Ei(4));
		if (c) throw Error(Ei(5));
		let t = !0;
		l();
		let n = s++;
		return o.set(n, e), function() {
			if (t) {
				if (c) throw Error(Ei(6));
				t = !1, l(), o.delete(n), a = null;
			}
		};
	}
	function f(e) {
		if (!Ai(e)) throw Error(Ei(7));
		if (e.type === void 0) throw Error(Ei(8));
		if (typeof e.type != "string") throw Error(Ei(17));
		if (c) throw Error(Ei(9));
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
		if (typeof e != "function") throw Error(Ei(10));
		r = e, f({ type: ki.REPLACE });
	}
	function m() {
		let e = d;
		return {
			subscribe(t) {
				if (typeof t != "object" || !t) throw Error(Ei(11));
				function n() {
					let e = t;
					e.next && e.next(u());
				}
				return n(), { unsubscribe: e(n) };
			},
			[Di]() {
				return this;
			}
		};
	}
	return f({ type: ki.INIT }), {
		dispatch: f,
		subscribe: d,
		getState: u,
		replaceReducer: p,
		[Di]: m
	};
}
function Mi(e) {
	Object.keys(e).forEach((t) => {
		let n = e[t];
		if (n(void 0, { type: ki.INIT }) === void 0) throw Error(Ei(12));
		if (n(void 0, { type: ki.PROBE_UNKNOWN_ACTION() }) === void 0) throw Error(Ei(13));
	});
}
function Ni(e) {
	let t = Object.keys(e), n = {};
	for (let r = 0; r < t.length; r++) {
		let i = t[r];
		typeof e[i] == "function" && (n[i] = e[i]);
	}
	let r = Object.keys(n), i;
	try {
		Mi(n);
	} catch (e) {
		i = e;
	}
	return function(e = {}, t) {
		if (i) throw i;
		let a = !1, o = {};
		for (let i = 0; i < r.length; i++) {
			let s = r[i], c = n[s], l = e[s], u = c(l, t);
			if (u === void 0) throw t && t.type, Error(Ei(14));
			o[s] = u, a = a || u !== l;
		}
		return a = a || r.length !== Object.keys(e).length, a ? o : e;
	};
}
function Pi(...e) {
	return e.length === 0 ? (e) => e : e.length === 1 ? e[0] : e.reduce((e, t) => (...n) => e(t(...n)));
}
function Fi(...e) {
	return (t) => (n, r) => {
		let i = t(n, r), a = () => {
			throw Error(Ei(15));
		}, o = {
			getState: i.getState,
			dispatch: (e, ...t) => a(e, ...t)
		};
		return a = Pi(...e.map((e) => e(o)))(i.dispatch), {
			...i,
			dispatch: a
		};
	};
}
function Ii(e) {
	return Ai(e) && "type" in e && typeof e.type == "string";
}
//#endregion
//#region node_modules/immer/dist/immer.mjs
var Li = Symbol.for("immer-nothing"), Ri = Symbol.for("immer-draftable"), zi = Symbol.for("immer-state");
function Bi(e, ...t) {
	throw Error(`[Immer] minified error nr: ${e}. Full error at: https://bit.ly/3cXEKWf`);
}
var Vi = Object, Hi = Vi.getPrototypeOf, Ui = "constructor", Wi = "prototype", Gi = "configurable", Ki = "enumerable", qi = "writable", Ji = "value", Yi = (e) => !!e && !!e[zi];
function z(e) {
	var t;
	return e ? Qi(e) || aa(e) || !!e[Ri] || !!((t = e[Ui]) != null && t[Ri]) || oa(e) || sa(e) : !1;
}
var Xi = Vi[Wi][Ui].toString(), Zi = /* @__PURE__ */ new WeakMap();
function Qi(e) {
	if (!e || !ca(e)) return !1;
	let t = Hi(e);
	if (t === null || t === Vi[Wi]) return !0;
	let n = Vi.hasOwnProperty.call(t, Ui) && t[Ui];
	if (n === Object) return !0;
	if (!la(n)) return !1;
	let r = Zi.get(n);
	return r === void 0 && (r = Function.toString.call(n), Zi.set(n, r)), r === Xi;
}
function $i(e, t, n = !0) {
	ea(e) === 0 ? (n ? Reflect.ownKeys(e) : Vi.keys(e)).forEach((n) => {
		t(n, e[n], e);
	}) : e.forEach((n, r) => t(r, n, e));
}
function ea(e) {
	let t = e[zi];
	return t ? t.type_ : aa(e) ? 1 : oa(e) ? 2 : sa(e) ? 3 : 0;
}
var ta = (e, t, n = ea(e)) => n === 2 ? e.has(t) : Vi[Wi].hasOwnProperty.call(e, t), na = (e, t, n = ea(e)) => n === 2 ? e.get(t) : e[t], ra = (e, t, n, r = ea(e)) => {
	r === 2 ? e.set(t, n) : r === 3 ? e.add(n) : e[t] = n;
};
function ia(e, t) {
	return e === t ? e !== 0 || 1 / e == 1 / t : e !== e && t !== t;
}
var aa = Array.isArray, oa = (e) => e instanceof Map, sa = (e) => e instanceof Set, ca = (e) => typeof e == "object", la = (e) => typeof e == "function", ua = (e) => typeof e == "boolean";
function da(e) {
	let t = +e;
	return Number.isInteger(t) && String(t) === e;
}
var fa = (e) => e.copy_ || e.base_, pa = (e) => e.modified_ ? e.copy_ : e.base_;
function ma(e, t) {
	if (oa(e)) return new Map(e);
	if (sa(e)) return new Set(e);
	if (aa(e)) return Array[Wi].slice.call(e);
	let n = Qi(e);
	if (t === !0 || t === "class_only" && !n) {
		let t = Vi.getOwnPropertyDescriptors(e);
		delete t[zi];
		let n = Reflect.ownKeys(t);
		for (let r = 0; r < n.length; r++) {
			let i = n[r], a = t[i];
			a[qi] === !1 && (a[qi] = !0, a[Gi] = !0), (a.get || a.set) && (t[i] = {
				[Gi]: !0,
				[qi]: !0,
				[Ki]: a[Ki],
				[Ji]: e[i]
			});
		}
		return Vi.create(Hi(e), t);
	} else {
		let t = Hi(e);
		if (t !== null && n) return { ...e };
		let r = Vi.create(t);
		return Vi.assign(r, e);
	}
}
function ha(e, t = !1) {
	return va(e) || Yi(e) || !z(e) ? e : (ea(e) > 1 && Vi.defineProperties(e, {
		set: _a,
		add: _a,
		clear: _a,
		delete: _a
	}), Vi.freeze(e), t && $i(e, (e, t) => {
		ha(t, !0);
	}, !1), e);
}
function ga() {
	Bi(2);
}
var _a = { [Ji]: ga };
function va(e) {
	return e === null || !ca(e) || Vi.isFrozen(e);
}
var ya = "MapSet", ba = "Patches", xa = "ArrayMethods", Sa = {};
function Ca(e) {
	let t = Sa[e];
	return t || Bi(0, e), t;
}
var wa = (e) => !!Sa[e], Ta, Ea = () => Ta, Da = (e, t) => ({
	drafts_: [],
	parent_: e,
	immer_: t,
	canAutoFreeze_: !0,
	unfinalizedDrafts_: 0,
	handledSet_: /* @__PURE__ */ new Set(),
	processedForPatches_: /* @__PURE__ */ new Set(),
	mapSetPlugin_: wa(ya) ? Ca(ya) : void 0,
	arrayMethodsPlugin_: wa(xa) ? Ca(xa) : void 0
});
function Oa(e, t) {
	t && (e.patchPlugin_ = Ca(ba), e.patches_ = [], e.inversePatches_ = [], e.patchListener_ = t);
}
function ka(e) {
	Aa(e), e.drafts_.forEach(Ma), e.drafts_ = null;
}
function Aa(e) {
	e === Ta && (Ta = e.parent_);
}
var ja = (e) => Ta = Da(Ta, e);
function Ma(e) {
	let t = e[zi];
	t.type_ === 0 || t.type_ === 1 ? t.revoke_() : t.revoked_ = !0;
}
function Na(e, t) {
	t.unfinalizedDrafts_ = t.drafts_.length;
	let n = t.drafts_[0];
	if (e !== void 0 && e !== n) {
		n[zi].modified_ && (ka(t), Bi(4)), z(e) && (e = Pa(t, e));
		let { patchPlugin_: r } = t;
		r && r.generateReplacementPatches_(n[zi].base_, e, t);
	} else e = Pa(t, n);
	return Fa(t, e, !0), ka(t), t.patches_ && t.patchListener_(t.patches_, t.inversePatches_), e === Li ? void 0 : e;
}
function Pa(e, t) {
	if (va(t)) return t;
	let n = t[zi];
	if (!n) return Ua(t, e.handledSet_, e);
	if (!La(n, e)) return t;
	if (!n.modified_) return n.base_;
	if (!n.finalized_) {
		let { callbacks_: t } = n;
		if (t) for (; t.length > 0;) t.pop()(e);
		Va(n, e);
	}
	return n.copy_;
}
function Fa(e, t, n = !1) {
	!e.parent_ && e.immer_.autoFreeze_ && e.canAutoFreeze_ && ha(t, n);
}
function Ia(e) {
	e.finalized_ = !0, e.scope_.unfinalizedDrafts_--;
}
var La = (e, t) => e.scope_ === t, Ra = [];
function za(e, t, n, r) {
	var i;
	let a = fa(e), o = e.type_;
	if (r !== void 0 && na(a, r, o) === t) {
		ra(a, r, n, o);
		return;
	}
	if (!e.draftLocations_) {
		let t = e.draftLocations_ = /* @__PURE__ */ new Map();
		$i(a, (e, n) => {
			if (Yi(n)) {
				let r = t.get(n) || [];
				r.push(e), t.set(n, r);
			}
		});
	}
	let s = (i = e.draftLocations_.get(t)) == null ? Ra : i;
	for (let e of s) ra(a, e, n, o);
}
function Ba(e, t, n) {
	e.callbacks_.push(function(r) {
		var i, a;
		let o = t;
		if (!o || !La(o, r)) return;
		(i = r.mapSetPlugin_) == null || i.fixSetContents(o);
		let s = pa(o);
		za(e, (a = o.draft_) == null ? o : a, s, n), Va(o, r);
	});
}
function Va(e, t) {
	var n, r;
	if (e.modified_ && !e.finalized_ && (e.type_ === 3 || e.type_ === 1 && e.allIndicesReassigned_ || ((n = (r = e.assigned_) == null ? void 0 : r.size) == null ? 0 : n) > 0)) {
		let { patchPlugin_: n } = t;
		if (n) {
			let r = n.getPath(e);
			r && n.generatePatches_(e, r, t);
		}
		Ia(e);
	}
}
function Ha(e, t, n) {
	let { scope_: r } = e;
	if (Yi(n)) {
		let i = n[zi];
		La(i, r) && i.callbacks_.push(function() {
			Qa(e), za(e, n, pa(i), t);
		});
	} else z(n) && e.callbacks_.push(function() {
		let i = fa(e);
		if (e.type_ === 3) i.has(n) && Ua(n, r.handledSet_, r);
		else if (na(i, t, e.type_) === n) {
			var a;
			r.drafts_.length > 1 && ((a = e.assigned_.get(t)) != null && a) === !0 && e.copy_ && Ua(na(e.copy_, t, e.type_), r.handledSet_, r);
		}
	});
}
function Ua(e, t, n) {
	return !n.immer_.autoFreeze_ && n.unfinalizedDrafts_ < 1 || Yi(e) || t.has(e) || !z(e) || va(e) ? e : (t.add(e), $i(e, (r, i) => {
		if (Yi(i)) {
			let t = i[zi];
			La(t, n) && (ra(e, r, pa(t), e.type_), Ia(t));
		} else z(i) && Ua(i, t, n);
	}), e);
}
function Wa(e, t) {
	let n = aa(e), r = {
		type_: +!!n,
		scope_: t ? t.scope_ : Ea(),
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
	}, i = r, a = Ga;
	n && (i = [r], a = Ka);
	let { revoke: o, proxy: s } = Proxy.revocable(i, a);
	return r.draft_ = s, r.revoke_ = o, [s, r];
}
var Ga = {
	get(e, t) {
		if (t === zi) return e;
		let n = e.scope_.arrayMethodsPlugin_, r = e.type_ === 1 && typeof t == "string";
		if (r && n != null && n.isArrayOperationMethod(t)) return n.createMethodInterceptor(e, t);
		let i = fa(e);
		if (!ta(i, t, e.type_)) return Ya(e, i, t);
		let a = i[t];
		if (e.finalized_ || !z(a) || r && e.operationMethod && n != null && n.isMutatingArrayMethod(e.operationMethod) && da(t)) return a;
		if (a === qa(e.base_, t) || Ja(e, t, a)) {
			Qa(e);
			let n = e.type_ === 1 ? +t : t, r = eo(e.scope_, a, e, n);
			return e.copy_[n] = r;
		}
		return a;
	},
	has(e, t) {
		return t in fa(e);
	},
	ownKeys(e) {
		return Reflect.ownKeys(fa(e));
	},
	set(e, t, n) {
		let r = Xa(fa(e), t);
		if (r != null && r.set) return r.set.call(e.draft_, n), !0;
		if (!e.modified_) {
			let r = qa(fa(e), t), i = r == null ? void 0 : r[zi];
			if (i && i.base_ === n) return e.copy_[t] = n, e.assigned_.set(t, !1), !0;
			if (ia(n, r) && (n !== void 0 || ta(e.base_, t, e.type_))) return !0;
			Qa(e), Za(e);
		}
		return e.copy_[t] === n && (n !== void 0 || ta(e.copy_, t, e.type_)) || Number.isNaN(n) && Number.isNaN(e.copy_[t]) ? !0 : (e.copy_[t] = n, e.assigned_.set(t, !0), Ha(e, t, n), !0);
	},
	deleteProperty(e, t) {
		return Qa(e), qa(e.base_, t) !== void 0 || t in e.base_ ? (e.assigned_.set(t, !1), Za(e)) : e.assigned_.delete(t), e.copy_ && delete e.copy_[t], !0;
	},
	getOwnPropertyDescriptor(e, t) {
		let n = fa(e), r = Reflect.getOwnPropertyDescriptor(n, t);
		return r && {
			[qi]: !0,
			[Gi]: e.type_ !== 1 || t !== "length",
			[Ki]: r[Ki],
			[Ji]: n[t]
		};
	},
	defineProperty() {
		Bi(11);
	},
	getPrototypeOf(e) {
		return Hi(e.base_);
	},
	setPrototypeOf() {
		Bi(12);
	}
}, Ka = {};
for (let e in Ga) {
	let t = Ga[e];
	Ka[e] = function() {
		let e = arguments;
		return e[0] = e[0][0], t.apply(this, e);
	};
}
Ka.deleteProperty = function(e, t) {
	return Ka.set.call(this, e, t, void 0);
}, Ka.set = function(e, t, n) {
	return Ga.set.call(this, e[0], t, n, e[0]);
};
function qa(e, t) {
	let n = e[zi];
	return (n ? fa(n) : e)[t];
}
function Ja(e, t, n) {
	var r;
	return e.type_ !== 1 || !e.allIndicesReassigned_ || (r = e.assigned_) != null && r.get(t) || !z(n) || n[zi] ? !1 : e.baseRefs_.has(n);
}
function Ya(e, t, n) {
	var r;
	let i = Xa(t, n);
	return i ? Ji in i ? i[Ji] : (r = i.get) == null ? void 0 : r.call(e.draft_) : void 0;
}
function Xa(e, t) {
	if (!(t in e)) return;
	let n = Hi(e);
	for (; n;) {
		let e = Object.getOwnPropertyDescriptor(n, t);
		if (e) return e;
		n = Hi(n);
	}
}
function Za(e) {
	e.modified_ || (e.modified_ = !0, e.parent_ && Za(e.parent_));
}
function Qa(e) {
	e.copy_ || (e.assigned_ = /* @__PURE__ */ new Map(), e.copy_ = ma(e.base_, e.scope_.immer_.useStrictShallowCopy_));
}
var $a = class {
	constructor(e) {
		this.autoFreeze_ = !0, this.useStrictShallowCopy_ = !1, this.useStrictIteration_ = !1, this.produce = (e, t, n) => {
			if (la(e) && !la(t)) {
				let n = t;
				t = e;
				let r = this;
				return function(e = n, ...i) {
					return r.produce(e, (e) => t.call(this, e, ...i));
				};
			}
			la(t) || Bi(6), n !== void 0 && !la(n) && Bi(7);
			let r;
			if (z(e)) {
				let i = ja(this), a = eo(i, e, void 0), o = !0;
				try {
					r = t(a), o = !1;
				} finally {
					o ? ka(i) : Aa(i);
				}
				return Oa(i, n), Na(r, i);
			} else if (!e || !ca(e)) {
				if (r = t(e), r === void 0 && (r = e), r === Li && (r = void 0), this.autoFreeze_ && ha(r, !0), n) {
					let t = [], i = [];
					Ca(ba).generateReplacementPatches_(e, r, {
						patches_: t,
						inversePatches_: i
					}), n(t, i);
				}
				return r;
			} else Bi(1, e);
		}, this.produceWithPatches = (e, t) => {
			if (la(e)) return (t, ...n) => this.produceWithPatches(t, (t) => e(t, ...n));
			let n, r;
			return [
				this.produce(e, t, (e, t) => {
					n = e, r = t;
				}),
				n,
				r
			];
		}, ua(e == null ? void 0 : e.autoFreeze) && this.setAutoFreeze(e.autoFreeze), ua(e == null ? void 0 : e.useStrictShallowCopy) && this.setUseStrictShallowCopy(e.useStrictShallowCopy), ua(e == null ? void 0 : e.useStrictIteration) && this.setUseStrictIteration(e.useStrictIteration);
	}
	createDraft(e) {
		z(e) || Bi(8), Yi(e) && (e = to(e));
		let t = ja(this), n = eo(t, e, void 0);
		return n[zi].isManual_ = !0, Aa(t), n;
	}
	finishDraft(e, t) {
		let n = e && e[zi];
		(!n || !n.isManual_) && Bi(9);
		let { scope_: r } = n;
		return Oa(r, t), Na(void 0, r);
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
		let r = Ca(ba).applyPatches_;
		return Yi(e) ? r(e, t) : this.produce(e, (e) => r(e, t));
	}
};
function eo(e, t, n, r) {
	var i, a;
	let [o, s] = oa(t) ? Ca(ya).proxyMap_(t, n) : sa(t) ? Ca(ya).proxySet_(t, n) : Wa(t, n);
	return ((i = n == null ? void 0 : n.scope_) == null ? Ea() : i).drafts_.push(o), s.callbacks_ = (a = n == null ? void 0 : n.callbacks_) == null ? [] : a, s.key_ = r, n && r !== void 0 ? Ba(n, s, r) : s.callbacks_.push(function(e) {
		var t;
		(t = e.mapSetPlugin_) == null || t.fixSetContents(s);
		let { patchPlugin_: n } = e;
		s.modified_ && n && n.generatePatches_(s, [], e);
	}), o;
}
function to(e) {
	return Yi(e) || Bi(10, e), no(e);
}
function no(e) {
	if (!z(e) || va(e)) return e;
	let t = e[zi], n, r = !0;
	if (t) {
		if (!t.modified_) return t.base_;
		t.finalized_ = !0, n = ma(e, t.scope_.immer_.useStrictShallowCopy_), r = t.scope_.immer_.shouldUseStrictIteration();
	} else n = ma(e, !0);
	return $i(n, (e, t) => {
		ra(n, e, no(t));
	}, r), t && (t.finalized_ = !1), n;
}
var ro = new $a().produce, B = (e) => e;
//#endregion
//#region node_modules/redux-thunk/dist/redux-thunk.mjs
function io(e) {
	return ({ dispatch: t, getState: n }) => (r) => (i) => typeof i == "function" ? i(t, n, e) : r(i);
}
var ao = io(), oo = io, so = typeof window < "u" && window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ ? window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ : function() {
	if (arguments.length !== 0) return typeof arguments[0] == "object" ? Pi : Pi.apply(null, arguments);
};
typeof window < "u" && window.__REDUX_DEVTOOLS_EXTENSION__ && window.__REDUX_DEVTOOLS_EXTENSION__;
function co(e, t) {
	function n(...n) {
		if (t) {
			let r = t(...n);
			if (!r) throw Error(gs(0));
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
	return n.toString = () => `${e}`, n.type = e, n.match = (t) => Ii(t) && t.type === e, n;
}
var lo = class e extends Array {
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
function uo(e) {
	return z(e) ? ro(e, () => {}) : e;
}
function fo(e, t, n) {
	return e.has(t) ? e.get(t) : e.set(t, n(t)).get(t);
}
function po(e) {
	return typeof e == "boolean";
}
var mo = () => function(e) {
	let { thunk: t = !0, immutableCheck: n = !0, serializableCheck: r = !0, actionCreatorCheck: i = !0 } = e == null ? {} : e, a = new lo();
	return t && (po(t) ? a.push(ao) : a.push(oo(t.extraArgument))), a;
}, ho = "RTK_autoBatch", V = () => (e) => ({
	payload: e,
	meta: { [ho]: !0 }
}), go = (e) => (t) => {
	setTimeout(t, e);
}, _o = (e, t) => (n) => {
	let r = !1, i = () => {
		r || (r = !0, cancelAnimationFrame(a), clearTimeout(o), n());
	}, a = e(i), o = setTimeout(i, t);
}, vo = (e = { type: "raf" }) => (t) => (...n) => {
	let r = t(...n), i = !0, a = !1, o = !1, s = /* @__PURE__ */ new Set(), c = e.type === "tick" ? queueMicrotask : e.type === "raf" ? typeof window < "u" && window.requestAnimationFrame ? _o(window.requestAnimationFrame, 100) : go(10) : e.type === "callback" ? e.queueNotification : go(e.timeout), l = () => {
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
				return i = !(!(e == null || (t = e.meta) == null) && t[ho]), a = !i, a && (o || (o = !0, c(l))), r.dispatch(e);
			} finally {
				i = !0;
			}
		}
	});
}, yo = (e) => function(t) {
	let { autoBatch: n = !0 } = t == null ? {} : t, r = new lo(e);
	return n && r.push(vo(typeof n == "object" ? n : void 0)), r;
};
function bo(e) {
	let t = mo(), { reducer: n = void 0, middleware: r, devTools: i = !0, duplicateMiddlewareCheck: a = !0, preloadedState: o = void 0, enhancers: s = void 0 } = e || {}, c;
	if (typeof n == "function") c = n;
	else if (Ai(n)) c = Ni(n);
	else throw Error(gs(1));
	let l;
	l = typeof r == "function" ? r(t) : t();
	let u = Pi;
	i && (u = so({
		trace: !1,
		...typeof i == "object" && i
	}));
	let d = yo(Fi(...l)), f = typeof s == "function" ? s(d) : d(), p = u(...f);
	return ji(c, o, p);
}
function xo(e) {
	let t = {}, n = [], r, i = {
		addCase(e, n) {
			let r = typeof e == "string" ? e : e.type;
			if (!r) throw Error(gs(28));
			if (r in t) throw Error(gs(29));
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
function So(e) {
	return typeof e == "function";
}
function Co(e, t) {
	let [n, r, i] = xo(t), a;
	if (So(e)) a = () => uo(e());
	else {
		let t = uo(e);
		a = () => t;
	}
	function o(e = a(), t) {
		let o = [n[t.type], ...r.filter(({ matcher: e }) => e(t)).map(({ reducer: e }) => e)];
		return o.filter((e) => !!e).length === 0 && (o = [i]), o.reduce((e, n) => {
			if (n) if (Yi(e)) {
				let r = n(e, t);
				return r === void 0 ? e : r;
			} else if (z(e)) return ro(e, (e) => n(e, t));
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
var wo = "ModuleSymbhasOwnPr-0123456789ABCDEFGHNRVfgctiUvz_KqYTJkLxpZXIjQW", To = (e = 21) => {
	let t = "", n = e;
	for (; n--;) t += wo[Math.random() * 64 | 0];
	return t;
}, Eo = /* @__PURE__ */ Symbol.for("rtk-slice-createasyncthunk");
function Do(e, t) {
	return `${e}/${t}`;
}
function Oo({ creators: e } = {}) {
	var t;
	let n = e == null || (t = e.asyncThunk) == null ? void 0 : t[Eo];
	return function(e) {
		let { name: t, reducerPath: r = t } = e;
		if (!t) throw Error(gs(11));
		let i = (typeof e.reducers == "function" ? e.reducers(Ao()) : e.reducers) || {}, a = Object.keys(i), o = {
			sliceCaseReducersByName: {},
			sliceCaseReducersByType: {},
			actionCreators: {},
			sliceMatchers: []
		}, s = {
			addCase(e, t) {
				let n = typeof e == "string" ? e : e.type;
				if (!n) throw Error(gs(12));
				if (n in o.sliceCaseReducersByType) throw Error(gs(13));
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
				type: Do(t, r),
				createNotation: typeof e.reducers == "function"
			};
			Mo(a) ? Po(o, a, s, n) : jo(o, a, s);
		});
		function c() {
			let [t = {}, n = [], r = void 0] = typeof e.extraReducers == "function" ? xo(e.extraReducers) : [e.extraReducers], i = {
				...t,
				...o.sliceCaseReducersByType
			};
			return Co(e.initialState, (e) => {
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
				return i === void 0 && n && (i = fo(d, r, m)), i;
			}
			function i(t = l) {
				return fo(fo(u, n, () => /* @__PURE__ */ new WeakMap()), t, () => {
					var r;
					let i = {};
					for (let [a, o] of Object.entries((r = e.selectors) == null ? {} : r)) i[a] = ko(o, t, () => fo(d, t, m), n);
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
function ko(e, t, n, r) {
	function i(i, ...a) {
		let o = t(i);
		return o === void 0 && r && (o = n()), e(o, ...a);
	}
	return i.unwrapped = e, i;
}
var H = /* @__PURE__ */ Oo();
function Ao() {
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
function jo({ type: e, reducerName: t, createNotation: n }, r, i) {
	let a, o;
	if ("reducer" in r) {
		if (n && !No(r)) throw Error(gs(17));
		a = r.reducer, o = r.prepare;
	} else a = r;
	i.addCase(e, a).exposeCaseReducer(t, a).exposeAction(t, o ? co(e, o) : co(e));
}
function Mo(e) {
	return e._reducerDefinitionType === "asyncThunk";
}
function No(e) {
	return e._reducerDefinitionType === "reducerWithPrepare";
}
function Po({ type: e, reducerName: t }, n, r, i) {
	if (!i) throw Error(gs(18));
	let { payloadCreator: a, fulfilled: o, pending: s, rejected: c, settled: l, options: u } = n, d = i(e, a, u);
	r.exposeAction(t, d), o && r.addCase(d.fulfilled, o), s && r.addCase(d.pending, s), c && r.addCase(d.rejected, c), l && r.addMatcher(d.settled, l), r.exposeCaseReducer(t, {
		fulfilled: o || Fo,
		pending: s || Fo,
		rejected: c || Fo,
		settled: l || Fo
	});
}
function Fo() {}
var Io = "task", Lo = "listener", Ro = "completed", zo = "cancelled", Bo = `task-${zo}`, Vo = `task-${Ro}`, Ho = `${Lo}-${zo}`, Uo = `${Lo}-${Ro}`, Wo = class {
	constructor(e) {
		Wr(this, "code", void 0), Wr(this, "name", "TaskAbortError"), Wr(this, "message", void 0), this.code = e, this.message = `${Io} ${zo} (reason: ${e})`;
	}
}, Go = (e, t) => {
	if (typeof e != "function") throw TypeError(gs(32));
}, Ko = () => {}, qo = (e, t = Ko) => (e.catch(t), e), Jo = (e, t) => (e.addEventListener("abort", t, { once: !0 }), () => e.removeEventListener("abort", t)), Yo = (e) => {
	if (e.aborted) throw new Wo(e.reason);
};
function Xo(e, t) {
	let n = Ko;
	return new Promise((r, i) => {
		let a = () => i(new Wo(e.reason));
		if (e.aborted) {
			a();
			return;
		}
		n = Jo(e, a), t.finally(() => n()).then(r, i);
	}).finally(() => {
		n = Ko;
	});
}
var Zo = async (e, t) => {
	try {
		return await Promise.resolve(), {
			status: "ok",
			value: await e()
		};
	} catch (e) {
		return {
			status: e instanceof Wo ? "cancelled" : "rejected",
			error: e
		};
	} finally {
		t == null || t();
	}
}, Qo = (e) => (t) => qo(Xo(e, t).then((t) => (Yo(e), t))), $o = (e) => {
	let t = Qo(e);
	return (e) => t(new Promise((t) => setTimeout(t, e)));
}, { assign: es } = Object, ts = {}, ns = "listenerMiddleware", rs = (e, t) => {
	let n = (t) => Jo(e, () => t.abort(e.reason));
	return (r, i) => {
		Go(r, "taskExecutor");
		let a = new AbortController();
		n(a);
		let o = Zo(async () => {
			Yo(e), Yo(a.signal);
			let t = await r({
				pause: Qo(a.signal),
				delay: $o(a.signal),
				signal: a.signal
			});
			return Yo(a.signal), t;
		}, () => a.abort(Vo));
		return i != null && i.autoJoin && t.push(o.catch(Ko)), {
			result: Qo(e)(o),
			cancel() {
				a.abort(Bo);
			}
		};
	};
}, is = (e, t) => {
	let n = async (n, r) => {
		Yo(t);
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
			let e = await Xo(t, Promise.race(a));
			return Yo(t), e;
		} finally {
			i();
		}
	};
	return ((e, t) => qo(n(e, t)));
}, as = (e) => {
	let { type: t, actionCreator: n, matcher: r, predicate: i, effect: a } = e;
	if (t) i = co(t).match;
	else if (n) t = n.type, i = n.match;
	else if (r) i = r;
	else if (!i) throw Error(gs(21));
	return Go(a, "options.listener"), {
		predicate: i,
		type: t,
		effect: a
	};
}, os = /* @__PURE__ */ es((e) => {
	let { type: t, predicate: n, effect: r } = as(e);
	return {
		id: To(),
		effect: r,
		type: t,
		predicate: n,
		pending: /* @__PURE__ */ new Set(),
		unsubscribe: () => {
			throw Error(gs(22));
		}
	};
}, { withTypes: () => os }), ss = (e, t) => {
	let { type: n, effect: r, predicate: i } = as(t);
	return Array.from(e.values()).find((e) => (typeof n == "string" ? e.type === n : e.predicate === i) && e.effect === r);
}, cs = (e) => {
	e.pending.forEach((e) => {
		e.abort(Ho);
	});
}, ls = (e, t) => () => {
	for (let e of t.keys()) cs(e);
	e.clear();
}, us = (e, t, n) => {
	try {
		e(t, n);
	} catch (e) {
		setTimeout(() => {
			throw e;
		}, 0);
	}
}, ds = /* @__PURE__ */ es(/* @__PURE__ */ co(`${ns}/add`), { withTypes: () => ds }), fs = /* @__PURE__ */ co(`${ns}/removeAll`), ps = /* @__PURE__ */ es(/* @__PURE__ */ co(`${ns}/remove`), { withTypes: () => ps }), ms = (...e) => {
	console.error(`${ns}/error`, ...e);
}, hs = (e = {}) => {
	let t = /* @__PURE__ */ new Map(), n = /* @__PURE__ */ new Map(), r = (e) => {
		var t;
		let r = (t = n.get(e)) == null ? 0 : t;
		n.set(e, r + 1);
	}, i = (e) => {
		var t;
		let r = (t = n.get(e)) == null ? 1 : t;
		r === 1 ? n.delete(e) : n.set(e, r - 1);
	}, { extra: a, onError: o = ms } = e;
	Go(o, "onError");
	let s = (e) => (e.unsubscribe = () => t.delete(e.id), t.set(e.id, e), (t) => {
		e.unsubscribe(), t != null && t.cancelActive && cs(e);
	}), c = ((e) => {
		var n;
		let r = (n = ss(t, e)) == null ? os(e) : n;
		return s(r);
	});
	es(c, { withTypes: () => c });
	let l = (e) => {
		let n = ss(t, e);
		return n && (n.unsubscribe(), e.cancelActive && cs(n)), !!n;
	};
	es(l, { withTypes: () => l });
	let u = async (e, n, s, l) => {
		let u = new AbortController(), d = is(c, u.signal), f = [];
		try {
			e.pending.add(u), r(e), await Promise.resolve(e.effect(n, es({}, s, {
				getOriginalState: l,
				condition: (e, t) => d(e, t).then(Boolean),
				take: d,
				delay: $o(u.signal),
				pause: Qo(u.signal),
				extra: a,
				signal: u.signal,
				fork: rs(u.signal, f),
				unsubscribe: e.unsubscribe,
				subscribe: () => {
					t.set(e.id, e);
				},
				cancelActiveListeners: () => {
					e.pending.forEach((e, t, n) => {
						e !== u && (e.abort(Ho), n.delete(e));
					});
				},
				cancel: () => {
					u.abort(Ho), e.pending.delete(u);
				},
				throwIfCancelled: () => {
					Yo(u.signal);
				}
			})));
		} catch (e) {
			e instanceof Wo || us(o, e, { raisedBy: "effect" });
		} finally {
			await Promise.all(f), u.abort(Uo), i(e), e.pending.delete(u);
		}
	}, d = ls(t, n);
	return {
		middleware: (e) => (n) => (r) => {
			if (!Ii(r)) return n(r);
			if (ds.match(r)) return c(r.payload);
			if (fs.match(r)) {
				d();
				return;
			}
			if (ps.match(r)) return l(r.payload);
			let i = e.getState(), a = () => {
				if (i === ts) throw Error(gs(23));
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
							s = !1, us(o, e, { raisedBy: "predicate" });
						}
						s && u(t, r, e, a);
					}
				}
			} finally {
				i = ts;
			}
			return s;
		},
		startListening: c,
		stopListening: l,
		clearListeners: d
	};
};
function gs(e) {
	return `Minified Redux Toolkit error #${e}; visit https://redux-toolkit.js.org/Errors?code=${e} for the full message or use the non-minified dev environment for full errors. `;
}
//#endregion
//#region node_modules/recharts/es6/state/layoutSlice.js
var _s = H({
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
}), vs = _s.actions, ys = vs.setMargin, bs = vs.setLayout, xs = vs.setChartSize, Ss = vs.setScale, Cs = _s.reducer;
//#endregion
//#region node_modules/recharts/es6/util/getSliced.js
function ws(e, t, n) {
	return Array.isArray(e) && e && t + n !== 0 ? e.slice(t, n + 1) : e;
}
//#endregion
//#region node_modules/recharts/es6/util/isWellBehavedNumber.js
function U(e) {
	return Number.isFinite(e);
}
function Ts(e) {
	return typeof e == "number" && e > 0 && Number.isFinite(e);
}
//#endregion
//#region node_modules/recharts/es6/util/ChartUtils.js
function Es(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Ds(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Es(Object(n), !0).forEach(function(t) {
			Os(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Es(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Os(e, t, n) {
	return (t = ks(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function ks(e) {
	var t = As(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function As(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function js(e, t, n) {
	return ln(e) || ln(t) ? n : tn(t) ? qt(e, t, n) : typeof t == "function" ? t(e) : n;
}
var Ms = (e, t, n) => {
	if (t && n) {
		var r = n.width, i = n.height, a = t.align, o = t.verticalAlign, s = t.layout;
		if ((s === "vertical" || s === "horizontal" && o === "middle") && a !== "center" && I(e[a])) return Ds(Ds({}, e), {}, { [a]: e[a] + (r || 0) });
		if ((s === "horizontal" || s === "vertical" && a === "center") && o !== "middle" && I(e[o])) return Ds(Ds({}, e), {}, { [o]: e[o] + (i || 0) });
	}
	return e;
}, Ns = (e, t) => e === "horizontal" && t === "xAxis" || e === "vertical" && t === "yAxis" || e === "centric" && t === "angleAxis" || e === "radial" && t === "radiusAxis", Ps = (e, t) => {
	if (!t || t.length !== 2 || !I(t[0]) || !I(t[1])) return e;
	var n = Math.min(t[0], t[1]), r = Math.max(t[0], t[1]), i = [e[0], e[1]];
	return (!I(e[0]) || e[0] < n) && (i[0] = n), (!I(e[1]) || e[1] > r) && (i[1] = r), i[0] > r && (i[0] = r), i[1] < n && (i[1] = n), i;
}, Fs = {
	sign: (e) => {
		var t, n = e.length;
		if (!(n <= 0)) {
			var r = (t = e[0]) == null ? void 0 : t.length;
			if (!(r == null || r <= 0)) for (var i = 0; i < r; ++i) for (var a = 0, o = 0, s = 0; s < n; ++s) {
				var c = e[s], l = c == null ? void 0 : c[i];
				if (l != null) {
					var u = l[1], d = l[0], f = $t(u) ? d : u;
					f >= 0 ? (l[0] = a, a += f, l[1] = a) : (l[0] = o, o += f, l[1] = o);
				}
			}
		}
	},
	expand: Bt,
	none: Ft,
	silhouette: Vt,
	wiggle: Ht,
	positive: (e) => {
		var t, n = e.length;
		if (!(n <= 0)) {
			var r = (t = e[0]) == null ? void 0 : t.length;
			if (!(r == null || r <= 0)) for (var i = 0; i < r; ++i) for (var a = 0, o = 0; o < n; ++o) {
				var s = e[o], c = s == null ? void 0 : s[i];
				if (c != null) {
					var l = $t(c[1]) ? c[0] : c[1];
					l >= 0 ? (c[0] = a, a += l, c[1] = a) : (c[0] = 0, c[1] = 0);
				}
			}
		}
	}
}, Is = (e, t, n) => {
	var r, i = (r = Fs[n]) == null ? Ft : r, a = zt().keys(t).value((e, t) => Number(js(e, t, 0))).order(It).offset(i)(e);
	return a.forEach((n, r) => {
		n.forEach((n, i) => {
			var a = js(e[i], t[r], 0);
			Array.isArray(a) && a.length === 2 && I(a[0]) && I(a[1]) && (n[0] = a[0], n[1] = a[1]);
		});
	}), a;
};
function Ls(e) {
	return e == null ? void 0 : String(e);
}
var Rs = (e) => {
	var t = e.axis, n = e.ticks, r = e.offset, i = e.bandSize, a = e.entry, o = e.index;
	if (t.type === "category") return n[o] ? n[o].coordinate + r : null;
	var s = js(a, t.dataKey, t.scale.domain()[o]);
	if (ln(s)) return null;
	var c = t.scale.map(s);
	return I(c) ? c - i / 2 + r : null;
}, zs = (e) => {
	var t = e.numericAxis, n = t.scale.domain();
	if (t.type === "number") {
		var r = Math.min(n[0], n[1]), i = Math.max(n[0], n[1]);
		return r <= 0 && i >= 0 ? 0 : i < 0 ? i : r;
	}
	return n[0];
}, Bs = (e) => {
	var t = e.flat(2).filter(I);
	return [Math.min(...t), Math.max(...t)];
}, Vs = (e) => [e[0] === Infinity ? 0 : e[0], e[1] === -Infinity ? 0 : e[1]], Hs = (e, t, n) => {
	if (!(e == null || Object.keys(e).length === 0)) return Vs(Object.keys(e).reduce((r, i) => {
		var a = e[i];
		if (!a) return r;
		var o = a.stackedData.reduce((e, r) => {
			var i = Bs(ws(r, t, n));
			return !U(i[0]) || !U(i[1]) ? e : [Math.min(e[0], i[0]), Math.max(e[1], i[1])];
		}, [Infinity, -Infinity]);
		return [Math.min(o[0], r[0]), Math.max(o[1], r[1])];
	}, [Infinity, -Infinity]));
}, Us = /^dataMin[\s]*-[\s]*([0-9]+([.]{1}[0-9]+){0,1})$/, Ws = /^dataMax[\s]*\+[\s]*([0-9]+([.]{1}[0-9]+){0,1})$/, Gs = (e, t, n) => {
	if (e && e.scale && e.scale.bandwidth) {
		var r = e.scale.bandwidth();
		if (!n || r > 0) return r;
	}
	if (e && t && t.length >= 2) {
		for (var i = pi(t, (e) => e.coordinate), a = Infinity, o = 1, s = i.length; o < s; o++) {
			var c = i[o], l = i[o - 1];
			a = Math.min(((c == null ? void 0 : c.coordinate) || 0) - ((l == null ? void 0 : l.coordinate) || 0), a);
		}
		return a === Infinity ? 0 : a;
	}
	return n ? void 0 : 0;
};
function Ks(e) {
	var t = e.tooltipEntrySettings, n = e.dataKey, r = e.payload, i = e.value, a = e.name;
	return Ds(Ds({}, t), {}, {
		dataKey: n,
		payload: r,
		value: i,
		name: a
	});
}
function qs(e, t) {
	if (e != null) return String(e);
	if (typeof t == "string") return t;
}
var Js = (e, t) => {
	if (t === "horizontal") return e.relativeX;
	if (t === "vertical") return e.relativeY;
}, Ys = (e, t) => t === "centric" ? e.angle : e.radius, Xs = (e) => e.layout.width, Zs = (e) => e.layout.height, Qs = (e) => e.layout.scale, $s = (e) => e.layout.margin, ec = R((e) => e.cartesianAxis.xAxis, (e) => Object.values(e)), tc = R((e) => e.cartesianAxis.yAxis, (e) => Object.values(e)), nc = "data-recharts-item-index";
//#endregion
//#region node_modules/recharts/es6/state/selectors/selectChartOffsetInternal.js
function rc(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function ic(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? rc(Object(n), !0).forEach(function(t) {
			ac(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : rc(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function ac(e, t, n) {
	return (t = oc(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function oc(e) {
	var t = sc(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function sc(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var cc = (e) => e.brush.height;
function lc(e) {
	return tc(e).reduce((e, t) => t.orientation === "left" && !t.mirror && !t.hide ? e + (typeof t.width == "number" ? t.width : 60) : e, 0);
}
function uc(e) {
	return tc(e).reduce((e, t) => t.orientation === "right" && !t.mirror && !t.hide ? e + (typeof t.width == "number" ? t.width : 60) : e, 0);
}
function dc(e) {
	return ec(e).reduce((e, t) => t.orientation === "top" && !t.mirror && !t.hide ? e + t.height : e, 0);
}
function fc(e) {
	return ec(e).reduce((e, t) => t.orientation === "bottom" && !t.mirror && !t.hide ? e + t.height : e, 0);
}
var pc = R([
	Xs,
	Zs,
	$s,
	cc,
	lc,
	uc,
	dc,
	fc,
	mi,
	hi
], (e, t, n, r, i, a, o, s, c, l) => {
	var u = {
		left: (n.left || 0) + i,
		right: (n.right || 0) + a
	}, d = ic(ic({}, {
		top: (n.top || 0) + o,
		bottom: (n.bottom || 0) + s
	}), u), f = d.bottom;
	d.bottom += r, d = Ms(d, c, l);
	var p = e - d.left - d.right, m = t - d.top - d.bottom;
	return ic(ic({ brushBottom: f }, d), {}, {
		width: Math.max(p, 0),
		height: Math.max(m, 0)
	});
}), mc = R(pc, (e) => ({
	x: e.left,
	y: e.top,
	width: e.width,
	height: e.height
})), hc = R(Xs, Zs, (e, t) => ({
	x: 0,
	y: 0,
	width: e,
	height: t
})), gc = /*#__PURE__*/ (0, C.createContext)(null), _c = () => (0, C.useContext)(gc) != null, vc = (e) => e.brush, yc = R([
	vc,
	pc,
	$s
], (e, t, n) => ({
	height: e.height,
	x: I(e.x) ? e.x : t.left,
	y: I(e.y) ? e.y : t.top + t.height + t.brushBottom - ((n == null ? void 0 : n.bottom) || 0),
	width: I(e.width) ? e.width : t.width
}));
//#endregion
//#region node_modules/es-toolkit/dist/function/debounce.mjs
function W(e, t, { signal: n, edges: r } = {}) {
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
function bc(e, t = 0, n = {}) {
	typeof n != "object" && (n = {});
	let { leading: r = !1, trailing: i = !0, maxWait: a } = n, o = [, ,];
	r && (o[0] = "leading"), i && (o[1] = "trailing");
	let s, c = null, l = W(function(...t) {
		s = e.apply(this, t), c = null;
	}, t, { edges: o }), u = function(...t) {
		return a != null && (c === null && (c = Date.now()), Date.now() - c >= a) ? (s = e.apply(this, t), c = Date.now(), l.cancel(), l.schedule(), s) : (l.apply(this, t), s);
	};
	return u.cancel = l.cancel, u.flush = () => (l.flush(), s), u;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/function/throttle.mjs
function xc(e, t = 0, n = {}) {
	let { leading: r = !0, trailing: i = !0 } = n;
	return bc(e, t, {
		leading: r,
		maxWait: t,
		trailing: i
	});
}
//#endregion
//#region node_modules/recharts/es6/util/LogUtils.js
var Sc = function(e, t) {
	var n = [...arguments].slice(2);
	if (typeof console < "u" && console.warn && (t === void 0 && console.warn("LogUtils requires an error message argument"), !e)) if (t === void 0) console.warn("Minified exception occurred; use the non-minified dev environment for the full error message and additional helpful warnings.");
	else {
		var r = 0;
		console.warn(t.replace(/%s/g, () => n[r++]));
	}
}, Cc = {
	width: "100%",
	height: "100%",
	debounce: 0,
	minWidth: 0,
	initialDimension: {
		width: -1,
		height: -1
	}
}, wc = (e, t, n) => {
	var r = n.width, i = r === void 0 ? Cc.width : r, a = n.height, o = a === void 0 ? Cc.height : a, s = n.aspect, c = n.maxHeight, l = en(i) ? e : Number(i), u = en(o) ? t : Number(o);
	return s && s > 0 && (l ? u = l / s : u && (l = u * s), c && u != null && u > c && (u = c)), {
		calculatedWidth: l,
		calculatedHeight: u
	};
}, Tc = {
	width: 0,
	height: 0,
	overflow: "visible"
}, Ec = {
	width: 0,
	overflowX: "visible"
}, Dc = {
	height: 0,
	overflowY: "visible"
}, Oc = {}, kc = (e) => {
	var t = e.width, n = e.height, r = en(t), i = en(n);
	return r && i ? Tc : r ? Ec : i ? Dc : Oc;
};
function Ac(e) {
	var t = e.width, n = e.height, r = e.aspect, i = t, a = n;
	return i === void 0 && a === void 0 ? (i = Cc.width, a = Cc.height) : i === void 0 ? i = r && r > 0 ? void 0 : Cc.width : a === void 0 && (a = r && r > 0 ? void 0 : Cc.height), {
		width: i,
		height: a
	};
}
//#endregion
//#region node_modules/recharts/es6/component/ResponsiveContainer.js
var jc = [
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
function Mc() {
	return Mc = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, Mc.apply(null, arguments);
}
function Nc(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Pc(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Nc(Object(n), !0).forEach(function(t) {
			Fc(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Nc(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Fc(e, t, n) {
	return (t = Ic(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function Ic(e) {
	var t = Lc(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Lc(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function Rc(e, t) {
	return Uc(e) || Hc(e, t) || Bc(e, t) || zc();
}
function zc() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function Bc(e, t) {
	if (e) {
		if (typeof e == "string") return Vc(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? Vc(e, t) : void 0;
	}
}
function Vc(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function Hc(e, t) {
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
function Uc(e) {
	if (Array.isArray(e)) return e;
}
function Wc(e, t) {
	if (e == null) return {};
	var n, r, i = Gc(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function Gc(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var Kc = /*#__PURE__*/ (0, C.createContext)(Cc.initialDimension);
function qc(e) {
	return Ts(e.width) && Ts(e.height);
}
function Jc(e) {
	var t = e.children, n = e.width, r = e.height, i = (0, C.useMemo)(() => ({
		width: n,
		height: r
	}), [n, r]);
	return qc(i) ? /*#__PURE__*/ C.createElement(Kc.Provider, { value: i }, t) : null;
}
var G = () => (0, C.useContext)(Kc), Yc = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.aspect, r = e.initialDimension, i = r === void 0 ? Cc.initialDimension : r, a = e.width, o = e.height, s = e.minWidth, c = s === void 0 ? Cc.minWidth : s, l = e.minHeight, u = e.maxHeight, d = e.children, f = e.debounce, p = f === void 0 ? Cc.debounce : f, m = e.id, h = e.className, g = e.onResize, _ = e.style, v = _ === void 0 ? {} : _, y = Wc(e, jc), b = (0, C.useRef)(null), x = (0, C.useRef)();
	x.current = g, (0, C.useImperativeHandle)(t, () => b.current);
	var S = Rc((0, C.useState)({
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
		if (b.current == null || typeof ResizeObserver > "u") return fn;
		var e = (e) => {
			var t, n = e[0];
			if (n != null) {
				var r = n.contentRect, i = r.width, a = r.height;
				E(i, a), (t = x.current) == null || t.call(x, i, a);
			}
		};
		p > 0 && (e = xc(e, p, {
			trailing: !0,
			leading: !1
		}));
		var t = new ResizeObserver(e), n = b.current.getBoundingClientRect(), r = n.width, i = n.height;
		return E(r, i), t.observe(b.current), () => {
			t.disconnect();
		};
	}, [E, p]);
	var D = w.containerWidth, O = w.containerHeight;
	Sc(!n || n > 0, "The aspect(%s) must be greater than zero.", n);
	var k = wc(D, O, {
		width: a,
		height: o,
		aspect: n,
		maxHeight: u
	}), A = k.calculatedWidth, j = k.calculatedHeight;
	return Sc(D < 0 || O < 0 || A != null && A > 0 || j != null && j > 0, "The width(%s) and height(%s) of chart should be greater than 0,\n       please check the style of container, or the props width(%s) and height(%s),\n       or add a minWidth(%s) or minHeight(%s) or use aspect(%s) to control the\n       height and width.", A, j, a, o, c, l, n), /*#__PURE__*/ C.createElement("div", Mc({
		id: m ? `${m}` : void 0,
		className: Ce("recharts-responsive-container", h),
		style: Pc(Pc({}, v), {}, {
			width: a,
			height: o,
			minWidth: c,
			minHeight: l,
			maxHeight: u
		}),
		ref: b
	}, y), /*#__PURE__*/ C.createElement("div", { style: kc({
		width: a,
		height: o
	}) }, /*#__PURE__*/ C.createElement(Jc, {
		width: A,
		height: j
	}, d)));
}), Xc = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = G();
	if (Ts(n.width) && Ts(n.height)) return e.children;
	var r = Ac({
		width: e.width,
		height: e.height,
		aspect: e.aspect
	}), i = r.width, a = r.height, o = wc(void 0, void 0, {
		width: i,
		height: a,
		aspect: e.aspect,
		maxHeight: e.maxHeight
	}), s = o.calculatedWidth, c = o.calculatedHeight;
	return I(s) && I(c) ? /*#__PURE__*/ C.createElement(Jc, {
		width: s,
		height: c
	}, e.children) : /*#__PURE__*/ C.createElement(Yc, Mc({}, e, {
		width: i,
		height: a,
		ref: t
	}));
});
//#endregion
//#region node_modules/recharts/es6/context/chartLayoutContext.js
function Zc(e) {
	if (e) return {
		x: e.x,
		y: e.y,
		upperWidth: "upperWidth" in e ? e.upperWidth : e.width,
		lowerWidth: "lowerWidth" in e ? e.lowerWidth : e.width,
		width: e.width,
		height: e.height
	};
}
var Qc = () => {
	var e, t = _c(), n = L(mc), r = L(yc), i = (e = L(vc)) == null ? void 0 : e.padding;
	return !t || !r || !i ? n : {
		width: r.width - i.left - i.right,
		height: r.height - i.top - i.bottom,
		x: i.left,
		y: i.top
	};
}, $c = {
	top: 0,
	bottom: 0,
	left: 0,
	right: 0,
	width: 0,
	height: 0,
	brushBottom: 0
}, el = () => {
	var e;
	return (e = L(pc)) == null ? $c : e;
}, tl = () => L(Xs), nl = () => L(Zs), K = (e) => e.layout.layoutType, rl = () => L(K), il = () => {
	var e = rl();
	if (e === "horizontal" || e === "vertical") return e;
}, al = (e) => {
	var t = e.layout.layoutType;
	if (t === "centric" || t === "radial") return t;
}, ol = () => rl() !== void 0, sl = (e) => {
	var t = Lr(), n = _c(), r = e.width, i = e.height, a = G(), o = r, s = i;
	return a && (o = a.width > 0 ? a.width : r, s = a.height > 0 ? a.height : i), (0, C.useEffect)(() => {
		!n && Ts(o) && Ts(s) && t(xs({
			width: o,
			height: s
		}));
	}, [
		t,
		n,
		o,
		s
	]), null;
}, cl = H({
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
				e.payload.push(B(t.payload));
			},
			prepare: V()
		},
		replaceLegendPayload: {
			reducer(e, t) {
				var n = t.payload, r = n.prev, i = n.next, a = to(e).payload.indexOf(B(r));
				a > -1 && (e.payload[a] = B(i));
			},
			prepare: V()
		},
		removeLegendPayload: {
			reducer(e, t) {
				var n = to(e).payload.indexOf(B(t.payload));
				n > -1 && e.payload.splice(n, 1);
			},
			prepare: V()
		}
	}
}), ll = cl.actions;
ll.setLegendSize, ll.setLegendSettings;
var ul = ll.addLegendPayload, dl = ll.replaceLegendPayload, fl = ll.removeLegendPayload, pl = cl.reducer, ml = /* @__PURE__ */ o(((e) => {
	var t = d();
	t.useSyncExternalStore, t.useRef, t.useEffect, t.useMemo, t.useDebugValue;
}));
(/* @__PURE__ */ o(((e, t) => {
	t.exports = ml();
})))();
function hl(e) {
	e();
}
function gl() {
	let e = null, t = null;
	return {
		clear() {
			e = null, t = null;
		},
		notify() {
			hl(() => {
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
var _l = {
	notify() {},
	get: () => []
};
function vl(e, t) {
	let n, r = _l, i = 0, a = !1;
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
		i++, n || (n = t ? t.addNestedSub(c) : e.subscribe(c), r = gl());
	}
	function d() {
		i--, n && i === 0 && (n(), n = void 0, r.clear(), r = _l);
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
var yl = typeof window < "u" && window.document !== void 0 && window.document.createElement !== void 0, bl = typeof navigator < "u" && navigator.product === "ReactNative", xl = yl || bl ? C.useLayoutEffect : C.useEffect;
function Sl(e, t) {
	return e === t ? e !== 0 || t !== 0 || 1 / e == 1 / t : e !== e && t !== t;
}
function Cl(e, t) {
	if (Sl(e, t)) return !0;
	if (typeof e != "object" || !e || typeof t != "object" || !t) return !1;
	let n = Object.keys(e), r = Object.keys(t);
	if (n.length !== r.length) return !1;
	for (let r = 0; r < n.length; r++) if (!Object.prototype.hasOwnProperty.call(t, n[r]) || !Sl(e[n[r]], t[n[r]])) return !1;
	return !0;
}
var wl = /* @__PURE__ */ Symbol.for("react-redux-context"), Tl = typeof globalThis < "u" ? globalThis : {};
function El() {
	var e;
	if (!C.createContext) return {};
	let t = (e = Tl[wl]) == null ? Tl[wl] = /* @__PURE__ */ new Map() : e, n = t.get(C.createContext);
	return n || (n = C.createContext(null), t.set(C.createContext, n)), n;
}
var Dl = /* @__PURE__ */ El();
function Ol(e) {
	let { children: t, context: n, serverState: r, store: i } = e, a = C.useMemo(() => {
		let e = vl(i);
		return {
			store: i,
			subscription: e,
			getServerState: r ? () => r : void 0
		};
	}, [i, r]), o = C.useMemo(() => i.getState(), [i]);
	xl(() => {
		let { subscription: e } = a;
		return e.onStateChange = e.notifyNestedSubs, e.trySubscribe(), o !== i.getState() && e.notifyNestedSubs(), () => {
			e.tryUnsubscribe(), e.onStateChange = void 0;
		};
	}, [a, o]);
	let s = n || Dl;
	return /* @__PURE__ */ C.createElement(s.Provider, { value: a }, t);
}
var kl = Ol, Al = /* @__PURE__ */ new Set([
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
function jl(e, t) {
	return e == null && t == null ? !0 : typeof e == "number" && typeof t == "number" ? e === t || e !== e && t !== t : e === t;
}
function Ml(e, t) {
	for (var n of /* @__PURE__ */ new Set([...Object.keys(e), ...Object.keys(t)])) if (Al.has(n)) {
		if (e[n] == null && t[n] == null) continue;
		if (!Cl(e[n], t[n])) return !1;
	} else if (!jl(e[n], t[n])) return !1;
	return !0;
}
//#endregion
//#region node_modules/recharts/es6/component/DefaultTooltipContent.js
function Nl() {
	return Nl = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, Nl.apply(null, arguments);
}
function Pl(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Fl(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Pl(Object(n), !0).forEach(function(t) {
			Il(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Pl(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Il(e, t, n) {
	return (t = Ll(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function Ll(e) {
	var t = Rl(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Rl(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function zl(e, t) {
	return Wl(e) || Ul(e, t) || Vl(e, t) || Bl();
}
function Bl() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function Vl(e, t) {
	if (e) {
		if (typeof e == "string") return Hl(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? Hl(e, t) : void 0;
	}
}
function Hl(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function Ul(e, t) {
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
function Wl(e) {
	if (Array.isArray(e)) return e;
}
function Gl(e) {
	return Array.isArray(e) && tn(e[0]) && tn(e[1]) ? e.join(" ~ ") : e;
}
var Kl = {
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
function ql(e, t) {
	return t == null ? e : pi(e, t);
}
var Jl = (e) => {
	var t = e.separator, n = t === void 0 ? Kl.separator : t, r = e.contentStyle, i = e.itemStyle, a = e.labelStyle, o = a === void 0 ? Kl.labelStyle : a, s = e.payload, c = e.formatter, l = e.itemSorter, u = e.wrapperClassName, d = e.labelClassName, f = e.label, p = e.labelFormatter, m = e.accessibilityLayer, h = m === void 0 ? Kl.accessibilityLayer : m, g = () => {
		if (s && s.length) {
			var e = {
				padding: 0,
				margin: 0
			}, t = ql(s, l).map((e, t) => {
				if (!e || e.type === "none") return null;
				var r = e.formatter || c || Gl, a = e.value, o = e.name, l = a, u = o;
				if (r) {
					var d = r(a, o, e, t, s);
					if (Array.isArray(d)) {
						var f = zl(d, 2);
						l = f[0], u = f[1];
					} else if (d != null) l = d;
					else return null;
				}
				var p = Fl(Fl({}, Kl.itemStyle), {}, { color: e.color || Kl.itemStyle.color }, i);
				return /*#__PURE__*/ C.createElement("li", {
					className: "recharts-tooltip-item",
					key: `tooltip-item-${t}`,
					style: p
				}, tn(u) ? /*#__PURE__*/ C.createElement("span", { className: "recharts-tooltip-item-name" }, u) : null, tn(u) ? /*#__PURE__*/ C.createElement("span", { className: "recharts-tooltip-item-separator" }, n) : null, /*#__PURE__*/ C.createElement("span", { className: "recharts-tooltip-item-value" }, l), /*#__PURE__*/ C.createElement("span", { className: "recharts-tooltip-item-unit" }, e.unit || ""));
			});
			return /*#__PURE__*/ C.createElement("ul", {
				className: "recharts-tooltip-item-list",
				style: e
			}, t);
		}
		return null;
	}, _ = Fl(Fl({}, Kl.contentStyle), r), v = Fl({ margin: 0 }, o), y = !ln(f), b = y ? f : "", x = Ce("recharts-default-tooltip", u), S = Ce("recharts-tooltip-label", d);
	y && p && s != null && (b = p(f, s));
	var w = h ? {
		role: "status",
		"aria-live": "assertive"
	} : {};
	return /*#__PURE__*/ C.createElement("div", Nl({
		className: x,
		style: _
	}, w), /*#__PURE__*/ C.createElement("p", {
		className: S,
		style: v
	}, /*#__PURE__*/ C.isValidElement(b) ? b : `${b}`), g());
}, Yl = "recharts-tooltip-wrapper", Xl = { visibility: "hidden" };
function Zl(e) {
	var t = e.coordinate, n = e.translateX, r = e.translateY;
	return Ce(Yl, {
		[`${Yl}-right`]: I(n) && t && I(t.x) && n >= t.x,
		[`${Yl}-left`]: I(n) && t && I(t.x) && n < t.x,
		[`${Yl}-bottom`]: I(r) && t && I(t.y) && r >= t.y,
		[`${Yl}-top`]: I(r) && t && I(t.y) && r < t.y
	});
}
function Ql(e) {
	var t = e.allowEscapeViewBox, n = e.coordinate, r = e.key, i = e.offset, a = e.position, o = e.reverseDirection, s = e.tooltipDimension, c = e.viewBox, l = e.viewBoxDimension;
	if (a && I(a[r])) return a[r];
	var u = n[r] - s - (i > 0 ? i : 0), d = n[r] + i;
	if (t[r]) return o[r] ? u : d;
	var f = c[r];
	return f == null ? 0 : o[r] ? Math.max(u < f ? d : u, f) : l == null ? 0 : d + s > f + l ? Math.max(u, f) : Math.max(d, f);
}
function $l(e) {
	var t = e.translateX, n = e.translateY;
	return { transform: e.useTranslate3d ? `translate3d(${t}px, ${n}px, 0)` : `translate(${t}px, ${n}px)` };
}
function eu(e) {
	var t = e.allowEscapeViewBox, n = e.coordinate, r = e.offsetTop, i = e.offsetLeft, a = e.position, o = e.reverseDirection, s = e.tooltipBox, c = e.useTranslate3d, l = e.viewBox, u, d, f;
	return s.height > 0 && s.width > 0 && n ? (d = Ql({
		allowEscapeViewBox: t,
		coordinate: n,
		key: "x",
		offset: i,
		position: a,
		reverseDirection: o,
		tooltipDimension: s.width,
		viewBox: l,
		viewBoxDimension: l.width
	}), f = Ql({
		allowEscapeViewBox: t,
		coordinate: n,
		key: "y",
		offset: r,
		position: a,
		reverseDirection: o,
		tooltipDimension: s.height,
		viewBox: l,
		viewBoxDimension: l.height
	}), u = $l({
		translateX: d,
		translateY: f,
		useTranslate3d: c
	})) : u = Xl, {
		cssProperties: u,
		cssClasses: Zl({
			translateX: d,
			translateY: f,
			coordinate: n
		})
	};
}
var tu = {
	devToolsEnabled: !0,
	isSsr: !(typeof window < "u" && window.document && window.document.createElement && window.setTimeout)
};
//#endregion
//#region node_modules/recharts/es6/util/usePrefersReducedMotion.js
function nu(e, t) {
	return su(e) || ou(e, t) || iu(e, t) || ru();
}
function ru() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function iu(e, t) {
	if (e) {
		if (typeof e == "string") return au(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? au(e, t) : void 0;
	}
}
function au(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function ou(e, t) {
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
function su(e) {
	if (Array.isArray(e)) return e;
}
function cu() {
	var e = nu((0, C.useState)(() => tu.isSsr || !window.matchMedia ? !1 : window.matchMedia("(prefers-reduced-motion: reduce)").matches), 2), t = e[0], n = e[1];
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
function lu(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function uu(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? lu(Object(n), !0).forEach(function(t) {
			du(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : lu(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function du(e, t, n) {
	return (t = fu(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function fu(e) {
	var t = pu(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function pu(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function mu(e, t) {
	return yu(e) || vu(e, t) || gu(e, t) || hu();
}
function hu() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function gu(e, t) {
	if (e) {
		if (typeof e == "string") return _u(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? _u(e, t) : void 0;
	}
}
function _u(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function vu(e, t) {
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
function yu(e) {
	if (Array.isArray(e)) return e;
}
function bu(e) {
	if (!(e.prefersReducedMotion && e.isAnimationActive === "auto") && e.isAnimationActive && e.active) {
		var t = typeof e.animationEasing == "string" ? e.animationEasing : "ease";
		return `transform ${e.animationDuration}ms ${t}`;
	}
}
function xu(e) {
	var t, n, r, i, a, o, s = cu(), c = mu(C.useState(() => ({
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
	}, [(t = e.coordinate) == null ? void 0 : t.x, (n = e.coordinate) == null ? void 0 : n.y]), l.dismissed && (((r = (i = e.coordinate) == null ? void 0 : i.x) == null ? 0 : r) !== l.dismissedAtCoordinate.x || ((a = (o = e.coordinate) == null ? void 0 : o.y) == null ? 0 : a) !== l.dismissedAtCoordinate.y) && u(uu(uu({}, l), {}, { dismissed: !1 }));
	var d = eu({
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
	}), f = d.cssClasses, p = d.cssProperties, m = uu(uu({}, e.hasPortalFromProps ? {} : uu(uu({ transition: bu({
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
var Su = /*#__PURE__*/ C.memo(xu), Cu = () => {
	var e;
	return (e = L((e) => e.rootProps.accessibilityLayer)) == null || e;
};
//#endregion
//#region node_modules/recharts/es6/shape/Curve.js
function wu() {
	return wu = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, wu.apply(null, arguments);
}
function Tu(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Eu(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Tu(Object(n), !0).forEach(function(t) {
			Du(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Tu(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Du(e, t, n) {
	return (t = Ou(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function Ou(e) {
	var t = ku(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function ku(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var Au = {
	curveBasisClosed: mt,
	curveBasisOpen: gt,
	curveBasis: ft,
	curveBumpX: st,
	curveBumpY: ct,
	curveLinearClosed: vt,
	curveLinear: tt,
	curveMonotoneX: Et,
	curveMonotoneY: Dt,
	curveNatural: At,
	curveStep: Mt,
	curveStepAfter: Pt,
	curveStepBefore: Nt
}, ju = (e) => U(e.x) && U(e.y), Mu = (e) => e.base != null && ju(e.base) && ju(e), Nu = (e) => e.x, Pu = (e) => e.y, Fu = (e, t) => {
	if (typeof e == "function") return e;
	var n = `curve${un(e)}`;
	if ((n === "curveMonotone" || n === "curveBump") && t) {
		var r = Au[`${n}${t === "vertical" ? "Y" : "X"}`];
		if (r) return r;
	}
	return Au[n] || tt;
}, Iu = {
	connectNulls: !1,
	type: "linear"
}, Lu = (e) => {
	var t = e.type, n = t === void 0 ? Iu.type : t, r = e.points, i = r === void 0 ? [] : r, a = e.baseLine, o = e.layout, s = e.connectNulls, c = s === void 0 ? Iu.connectNulls : s, l = Fu(n, o), u = c ? i.filter(ju) : i;
	if (Array.isArray(a)) {
		var d, f = i.map((e, t) => Eu(Eu({}, e), {}, { base: a[t] }));
		return d = o === "vertical" ? at().y(Pu).x1(Nu).x0((e) => e.base.x) : at().x(Nu).y1(Pu).y0((e) => e.base.y), d.defined(Mu).curve(l)(c ? f.filter(Mu) : f);
	}
	return (o === "vertical" && I(a) ? at().y(Pu).x1(Nu).x0(a) : I(a) ? at().x(Nu).y1(Pu).y0(a) : it().x(Nu).y(Pu)).defined(ju).curve(l)(u);
}, Ru = (e) => {
	var t = e.className, n = e.points, r = e.path, i = e.pathRef, a = rl();
	if ((!n || !n.length) && !r) return null;
	var o = {
		type: e.type,
		points: e.points,
		baseLine: e.baseLine,
		layout: e.layout || a,
		connectNulls: e.connectNulls
	}, s = n && n.length ? Lu(o) : r;
	return /*#__PURE__*/ C.createElement("path", wu({}, ke(e), mn(e), {
		className: Ce("recharts-curve", t),
		d: s === null ? void 0 : s,
		ref: i
	}));
}, zu = [
	"x",
	"y",
	"top",
	"left",
	"width",
	"height",
	"className"
];
function Bu() {
	return Bu = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, Bu.apply(null, arguments);
}
function Vu(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Hu(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Vu(Object(n), !0).forEach(function(t) {
			Uu(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Vu(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Uu(e, t, n) {
	return (t = Wu(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function Wu(e) {
	var t = Gu(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Gu(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function Ku(e, t) {
	if (e == null) return {};
	var n, r, i = qu(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function qu(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var Ju = (e, t, n, r, i, a) => `M${e},${i}v${r}M${a},${t}h${n}`, Yu = (e) => {
	var t = e.x, n = t === void 0 ? 0 : t, r = e.y, i = r === void 0 ? 0 : r, a = e.top, o = a === void 0 ? 0 : a, s = e.left, c = s === void 0 ? 0 : s, l = e.width, u = l === void 0 ? 0 : l, d = e.height, f = d === void 0 ? 0 : d, p = e.className, m = Ku(e, zu), h = Hu({
		x: n,
		y: i,
		top: o,
		left: c,
		width: u,
		height: f
	}, m);
	return !I(n) || !I(i) || !I(u) || !I(f) || !I(o) || !I(c) ? null : /*#__PURE__*/ C.createElement("path", Bu({}, je(h), {
		className: Ce("recharts-cross", p),
		d: Ju(n, i, u, f, o, c)
	}));
};
//#endregion
//#region node_modules/recharts/es6/util/cursor/getCursorRectangle.js
function Xu(e, t, n, r) {
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
var Zu = (e, t) => [
	0,
	3 * e,
	3 * t - 6 * e,
	3 * e - 3 * t + 1
], Qu = (e, t) => e.map((e, n) => e * t ** n).reduce((e, t) => e + t), $u = (e, t) => (n) => Qu(Zu(e, t), n), ed = (e, t) => (n) => Qu([...Zu(e, t).map((e, t) => e * t).slice(1), 0], n), td = (e) => {
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
}, nd = function() {
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
			var t = td(e[0]);
			if (t) return t;
	}
	return e.length === 4 ? e : [
		0,
		0,
		1,
		1
	];
}, rd = (e, t, n, r) => {
	var i = $u(e, n), a = $u(t, r), o = ed(e, n), s = (e) => e > 1 ? 1 : e < 0 ? 0 : e, c = (e) => {
		for (var t = e > 1 ? 1 : e, n = t, r = 0; r < 8; ++r) {
			var c = i(n) - t, l = o(n);
			if (Math.abs(c - t) < 1e-4 || l < 1e-4) return a(n);
			n = s(n - c / l);
		}
		return a(n);
	};
	return c.isStepper = !1, c;
}, id = function() {
	return rd(...nd(...arguments));
}, ad = function() {
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
}, od = (e) => {
	if (typeof e == "string") switch (e) {
		case "ease":
		case "ease-in-out":
		case "ease-out":
		case "ease-in":
		case "linear": return id(e);
		case "spring": return ad();
		default: if (e.split("(")[0] === "cubic-bezier") return id(e);
	}
	return typeof e == "function" ? e : null;
}, sd = /*#__PURE__*/ (0, C.createContext)((e, t, n) => {
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
sd.Provider;
function cd(e) {
	var t = (0, C.useContext)(sd);
	return (0, C.useMemo)(() => e == null ? t : e, [e, t]);
}
//#endregion
//#region node_modules/recharts/es6/animation/AnimationHandle.js
function ld(e, t, n) {
	return (t = ud(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function ud(e) {
	var t = dd(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function dd(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var fd = "init", pd = "pending", md = "active", hd = "completed";
function gd(e) {
	return Math.max(0, e);
}
var _d = class {
	getAnimationStartedTime() {
		return this.animationStartedTime;
	}
	getBeginStartedTime() {
		return this.beginStartedTime;
	}
	constructor(e) {
		var t;
		ld(this, "state", fd), this.animationId = e.animationId, this.onAnimationEnd = e.onAnimationEnd, this.animationDuration = gd(e.animationDuration), this.animationBegin = gd(e.animationBegin), this.progress = 0, this.from = e.from, this.to = e.to, this.easing = e.easing, (t = e.onAnimationStart) == null || t.call(e);
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
		if (this.getState() === fd) return this.state = pd, this.beginStartedTime = e, this.animationBegin;
		if (this.getState() === pd) {
			if (this.beginStartedTime == null) throw Error();
			var t = e - this.beginStartedTime;
			return t >= this.animationBegin ? (this.state = md, this.animationStartedTime = e, this.nextAnimationUpdate(0)) : gd(this.animationBegin - t);
		}
		if (this.getState() === md) {
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
		this.state = hd;
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
}, vd = class extends _d {
	nextAnimationUpdate() {
		return 0;
	}
	getInterpolated() {
		return this.easing(sn(this.getFrom(), this.getTo(), this.getProgress()));
	}
}, yd = class {
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
function bd(e, t) {
	return Td(e) || wd(e, t) || Sd(e, t) || xd();
}
function xd() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function Sd(e, t) {
	if (e) {
		if (typeof e == "string") return Cd(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? Cd(e, t) : void 0;
	}
}
function Cd(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function wd(e, t) {
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
function Td(e) {
	if (Array.isArray(e)) return e;
}
var Ed = {
	begin: 0,
	duration: 1e3,
	easing: "ease",
	isActive: !0,
	canBegin: !0,
	onAnimationEnd: () => {},
	onAnimationStart: () => {}
}, Dd = 0, Od = 1;
function kd(e) {
	var t = Sn(e, Ed), n = t.animationId, r = t.isActive, i = t.canBegin, a = t.duration, o = t.easing, s = t.begin, c = t.onAnimationEnd, l = t.onAnimationStart, u = t.children, d = cu(), f = r === "auto" ? !tu.isSsr && !d : r, p = cd(t.animationController), m = bd((0, C.useState)(f ? Dd : Od), 2), h = m[0], g = m[1];
	return (0, C.useEffect)(() => {
		f || g(Od);
	}, [f]), (0, C.useEffect)(() => {
		var e = od(o);
		return !f || !i || e == null ? fn : p(new yd(), new vd({
			animationId: n,
			easing: e,
			animationDuration: a,
			animationBegin: s,
			onAnimationStart: l,
			onAnimationEnd: c,
			from: Dd,
			to: Od
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
function Ad(e) {
	var t = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : "animation-", n = (0, C.useRef)(rn(t)), r = (0, C.useRef)(e);
	return r.current !== e && (n.current = rn(t), r.current = e), n.current;
}
//#endregion
//#region node_modules/recharts/es6/animation/util.js
var jd = (e) => e.replace(/([A-Z])/g, (e) => `-${e.toLowerCase()}`), Md = (e, t, n) => e.map((e) => `${jd(e)} ${t}ms ${n}`).join(","), Nd = ["radius"], Pd = ["radius"], Fd, Id, Ld, Rd, zd, Bd, Vd, Hd, Ud, Wd;
function Gd(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Kd(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Gd(Object(n), !0).forEach(function(t) {
			qd(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Gd(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function qd(e, t, n) {
	return (t = Jd(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function Jd(e) {
	var t = Yd(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Yd(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function Xd() {
	return Xd = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, Xd.apply(null, arguments);
}
function Zd(e, t) {
	if (e == null) return {};
	var n, r, i = Qd(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function Qd(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function $d(e, t) {
	return af(e) || rf(e, t) || tf(e, t) || ef();
}
function ef() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function tf(e, t) {
	if (e) {
		if (typeof e == "string") return nf(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? nf(e, t) : void 0;
	}
}
function nf(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function rf(e, t) {
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
function af(e) {
	if (Array.isArray(e)) return e;
}
function of(e, t) {
	return t || (t = e.slice(0)), Object.freeze(Object.defineProperties(e, { raw: { value: Object.freeze(t) } }));
}
var sf = (e, t, n, r, i) => {
	var a = Xt(n), o = Xt(r), s = Math.min(Math.abs(a) / 2, Math.abs(o) / 2), c = o >= 0 ? 1 : -1, l = a >= 0 ? 1 : -1, u = +(o >= 0 && a >= 0 || o < 0 && a < 0), d;
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
		d = Zt(Fd || (Fd = of([
			"M",
			",",
			""
		])), e, t + c * f[0]), f[0] > 0 && (d += Zt(Id || (Id = of([
			"A ",
			",",
			",0,0,",
			",",
			",",
			""
		])), f[0], f[0], u, e + l * f[0], t)), d += Zt(Ld || (Ld = of([
			"L ",
			",",
			""
		])), e + n - l * f[1], t), f[1] > 0 && (d += Zt(Rd || (Rd = of([
			"A ",
			",",
			",0,0,",
			",\n        ",
			",",
			""
		])), f[1], f[1], u, e + n, t + c * f[1])), d += Zt(zd || (zd = of([
			"L ",
			",",
			""
		])), e + n, t + r - c * f[2]), f[2] > 0 && (d += Zt(Bd || (Bd = of([
			"A ",
			",",
			",0,0,",
			",\n        ",
			",",
			""
		])), f[2], f[2], u, e + n - l * f[2], t + r)), d += Zt(Vd || (Vd = of([
			"L ",
			",",
			""
		])), e + l * f[3], t + r), f[3] > 0 && (d += Zt(Hd || (Hd = of([
			"A ",
			",",
			",0,0,",
			",\n        ",
			",",
			""
		])), f[3], f[3], u, e, t + r - c * f[3])), d += "Z";
	} else if (s > 0 && i === +i && i > 0) {
		var _ = Math.min(s, i);
		d = Zt(Ud || (Ud = of(/* @__PURE__ */ "M .,.\n            A .,.,0,0,.,.,.\n            L .,.\n            A .,.,0,0,.,.,.\n            L .,.\n            A .,.,0,0,.,.,.\n            L .,.\n            A .,.,0,0,.,.,. Z".split("."))), e, t + c * _, _, _, u, e + l * _, t, e + n - l * _, t, _, _, u, e + n, t + c * _, e + n, t + r - c * _, _, _, u, e + n - l * _, t + r, e + l * _, t + r, _, _, u, e, t + r - c * _);
	} else d = Zt(Wd || (Wd = of([
		"M ",
		",",
		" h ",
		" v ",
		" h ",
		" Z"
	])), e, t, n, r, -n);
	return d;
}, cf = {
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
}, lf = (e) => {
	var t = Sn(e, cf), n = (0, C.useRef)(null), r = $d((0, C.useState)(-1), 2), i = r[0], a = r[1];
	(0, C.useEffect)(() => {
		if (n.current && n.current.getTotalLength) try {
			var e = n.current.getTotalLength();
			e && a(e);
		} catch (e) {}
	}, []);
	var o = t.x, s = t.y, c = t.width, l = t.height, u = t.radius, d = t.className, f = t.animationEasing, p = t.animationDuration, m = t.animationBegin, h = t.isAnimationActive, g = t.isUpdateAnimationActive, _ = (0, C.useRef)(c), v = (0, C.useRef)(l), y = (0, C.useRef)(o), b = (0, C.useRef)(s), x = Ad((0, C.useMemo)(() => ({
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
	var S = Ce("recharts-rectangle", d);
	if (!g) {
		var w = je(t);
		w.radius;
		var T = Zd(w, Nd);
		return /*#__PURE__*/ C.createElement("path", Xd({}, T, {
			x: Xt(o),
			y: Xt(s),
			width: Xt(c),
			height: Xt(l),
			radius: typeof u == "number" ? u : void 0,
			className: S,
			d: sf(o, s, c, l, u)
		}));
	}
	var E = _.current, D = v.current, O = y.current, k = b.current, A = `0px ${i === -1 ? 1 : i}px`, j = `${i}px ${i}px`, M = Md(["strokeDasharray"], p, typeof f == "string" ? f : cf.animationEasing);
	return /*#__PURE__*/ C.createElement(kd, {
		animationId: x,
		key: x,
		canBegin: i > 0,
		duration: p,
		easing: f,
		isActive: g,
		begin: m
	}, (e) => {
		var r = sn(E, c, e), i = sn(D, l, e), a = sn(O, o, e), d = sn(k, s, e);
		n.current && (_.current = r, v.current = i, y.current = a, b.current = d);
		var f = h ? e > 0 ? {
			transition: M,
			strokeDasharray: j
		} : { strokeDasharray: A } : { strokeDasharray: j }, p = je(t);
		p.radius;
		var m = Zd(p, Pd);
		return /*#__PURE__*/ C.createElement("path", Xd({}, m, {
			radius: typeof u == "number" ? u : void 0,
			className: S,
			d: sf(a, d, r, i, u),
			ref: n,
			style: Kd(Kd({}, f), t.style)
		}));
	});
};
//#endregion
//#region node_modules/recharts/es6/util/PolarUtils.js
function uf(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function df(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? uf(Object(n), !0).forEach(function(t) {
			ff(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : uf(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function ff(e, t, n) {
	return (t = pf(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function pf(e) {
	var t = mf(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function mf(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var hf = Math.PI / 180, gf = (e) => e * 180 / Math.PI, _f = (e, t, n, r) => ({
	x: e + Math.cos(-hf * r) * n,
	y: t + Math.sin(-hf * r) * n
}), vf = function(e, t) {
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
}, yf = (e, t) => {
	var n = e.x, r = e.y, i = t.x, a = t.y;
	return Math.sqrt((n - i) ** 2 + (r - a) ** 2);
}, bf = (e, t) => {
	var n = e.x, r = e.y, i = t.cx, a = t.cy, o = yf({
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
		angle: gf(c),
		angleInRadian: c
	};
}, xf = (e) => {
	var t = e.startAngle, n = e.endAngle, r = Math.floor(t / 360), i = Math.floor(n / 360), a = Math.min(r, i);
	return {
		startAngle: t - a * 360,
		endAngle: n - a * 360
	};
}, Sf = (e, t) => {
	var n = t.startAngle, r = t.endAngle, i = Math.floor(n / 360), a = Math.floor(r / 360);
	return e + Math.min(i, a) * 360;
}, Cf = (e, t) => {
	var n = e.relativeX, r = e.relativeY, i = bf({
		x: n,
		y: r
	}, t), a = i.radius, o = i.angle, s = t.innerRadius, c = t.outerRadius;
	if (a < s || a > c || a === 0) return null;
	var l = xf(t), u = l.startAngle, d = l.endAngle, f = o, p;
	if (u <= d) {
		for (; f > d;) f -= 360;
		for (; f < u;) f += 360;
		p = f >= u && f <= d;
	} else {
		for (; f > u;) f -= 360;
		for (; f < d;) f += 360;
		p = f >= d && f <= u;
	}
	return p ? df(df({}, t), {}, {
		radius: a,
		angle: Sf(f, t)
	}) : null;
};
//#endregion
//#region node_modules/recharts/es6/util/cursor/getRadialCursorPoints.js
function wf(e) {
	var t = e.cx, n = e.cy, r = e.radius, i = e.startAngle, a = e.endAngle;
	return {
		points: [_f(t, n, r, i), _f(t, n, r, a)],
		cx: t,
		cy: n,
		radius: r,
		startAngle: i,
		endAngle: a
	};
}
//#endregion
//#region node_modules/recharts/es6/shape/Sector.js
var Tf, Ef, Df, Of, kf, Af, jf;
function Mf() {
	return Mf = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, Mf.apply(null, arguments);
}
function Nf(e, t) {
	return t || (t = e.slice(0)), Object.freeze(Object.defineProperties(e, { raw: { value: Object.freeze(t) } }));
}
var Pf = (e, t) => Qt(t - e) * Math.min(Math.abs(t - e), 359.999), Ff = (e) => {
	var t = e.cx, n = e.cy, r = e.radius, i = e.angle, a = e.sign, o = e.isExternal, s = e.cornerRadius, c = e.cornerIsExternal, l = s * (o ? 1 : -1) + r, u = Math.asin(s / l) / hf, d = c ? i : i + a * u, f = _f(t, n, l, d), p = _f(t, n, r, d), m = c ? i - a * u : i;
	return {
		center: f,
		circleTangency: p,
		lineTangency: _f(t, n, l * Math.cos(u * hf), m),
		theta: u
	};
}, If = (e) => {
	var t = e.cx, n = e.cy, r = e.innerRadius, i = e.outerRadius, a = e.startAngle, o = e.endAngle, s = Pf(a, o), c = a + s, l = _f(t, n, i, a), u = _f(t, n, i, c), d = Zt(Tf || (Tf = Nf([
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
		var f = _f(t, n, r, a), p = _f(t, n, r, c);
		d += Zt(Ef || (Ef = Nf([
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
	} else d += Zt(Df || (Df = Nf([
		"L ",
		",",
		" Z"
	])), t, n);
	return d;
}, Lf = (e) => {
	var t = e.cx, n = e.cy, r = e.innerRadius, i = e.outerRadius, a = e.cornerRadius, o = e.forceCornerRadius, s = e.cornerIsExternal, c = e.startAngle, l = e.endAngle, u = Qt(l - c), d = Ff({
		cx: t,
		cy: n,
		radius: i,
		angle: c,
		sign: u,
		cornerRadius: a,
		cornerIsExternal: s
	}), f = d.circleTangency, p = d.lineTangency, m = d.theta, h = Ff({
		cx: t,
		cy: n,
		radius: i,
		angle: l,
		sign: -u,
		cornerRadius: a,
		cornerIsExternal: s
	}), g = h.circleTangency, _ = h.lineTangency, v = h.theta, y = s ? Math.abs(c - l) : Math.abs(c - l) - m - v;
	if (y < 0) return o ? Zt(Of || (Of = Nf([
		"M ",
		",",
		"\n        a",
		",",
		",0,0,1,",
		",0\n        a",
		",",
		",0,0,1,",
		",0\n      "
	])), p.x, p.y, a, a, a * 2, a, a, -a * 2) : If({
		cx: t,
		cy: n,
		innerRadius: r,
		outerRadius: i,
		startAngle: c,
		endAngle: l
	});
	var b = Zt(kf || (kf = Nf([
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
		var x = Ff({
			cx: t,
			cy: n,
			radius: r,
			angle: c,
			sign: u,
			isExternal: !0,
			cornerRadius: a,
			cornerIsExternal: s
		}), S = x.circleTangency, C = x.lineTangency, w = x.theta, T = Ff({
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
		b += Zt(Af || (Af = Nf([
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
	} else b += Zt(jf || (jf = Nf([
		"L",
		",",
		"Z"
	])), t, n);
	return b;
}, Rf = {
	cx: 0,
	cy: 0,
	innerRadius: 0,
	outerRadius: 0,
	startAngle: 0,
	endAngle: 0,
	cornerRadius: 0,
	forceCornerRadius: !1,
	cornerIsExternal: !1
}, zf = (e) => {
	var t = Sn(e, Rf), n = t.cx, r = t.cy, i = t.innerRadius, a = t.outerRadius, o = t.cornerRadius, s = t.forceCornerRadius, c = t.cornerIsExternal, l = t.startAngle, u = t.endAngle, d = t.className;
	if (a < i || l === u) return null;
	var f = Ce("recharts-sector", d), p = a - i, m = an(o, p, 0, !0), h = m > 0 && Math.abs(l - u) < 360 ? Lf({
		cx: n,
		cy: r,
		innerRadius: i,
		outerRadius: a,
		cornerRadius: Math.min(m, p / 2),
		forceCornerRadius: s,
		cornerIsExternal: c,
		startAngle: l,
		endAngle: u
	}) : If({
		cx: n,
		cy: r,
		innerRadius: i,
		outerRadius: a,
		startAngle: l,
		endAngle: u
	});
	return /*#__PURE__*/ C.createElement("path", Mf({}, je(t), {
		className: f,
		d: h
	}));
};
//#endregion
//#region node_modules/recharts/es6/util/cursor/getCursorPoints.js
function Bf(e, t, n) {
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
	if (pn(t)) {
		if (e === "centric") {
			var r = t.cx, i = t.cy, a = t.innerRadius, o = t.outerRadius, s = t.angle, c = _f(r, i, a, s), l = _f(r, i, o, s);
			return [{
				x: c.x,
				y: c.y
			}, {
				x: l.x,
				y: l.y
			}];
		}
		return wf(t);
	}
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/util/toNumber.mjs
function Vf(e) {
	return ci(e) ? NaN : Number(e);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/util/toFinite.mjs
function Hf(e) {
	return e ? (e = Vf(e), e === Infinity || e === -Infinity ? (e < 0 ? -1 : 1) * Number.MAX_VALUE : e === e ? e : 0) : e === 0 ? e : 0;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/math/range.mjs
function Uf(e, t, n) {
	n && typeof n != "number" && ai(e, t, n) && (t = n = void 0), e = Hf(e), t === void 0 ? (t = e, e = 0) : t = Hf(t), n = n === void 0 ? e < t ? 1 : -1 : Hf(n);
	let r = Math.max(Math.ceil((t - e) / (n || 1)), 0), i = Array(r);
	for (let t = 0; t < r; t++) i[t] = e, e += n;
	return i;
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/dataSelectors.js
var Wf = (e) => e.chartData, Gf = R([Wf], (e) => {
	var t = e.chartData == null ? 0 : e.chartData.length - 1;
	return {
		chartData: e.chartData,
		computedData: e.computedData,
		dataEndIndex: t,
		dataStartIndex: 0
	};
}), Kf = (e, t, n, r) => r ? Gf(e) : Wf(e), qf = (e, t, n) => n ? Gf(e) : Wf(e), Jf = R([Kf], (e) => {
	var t = e.chartData, n = e.dataStartIndex, r = e.dataEndIndex;
	return t == null ? [] : t.slice(n, r + 1);
});
R([Gf], (e) => {
	var t = e.chartData, n = e.dataStartIndex, r = e.dataEndIndex;
	return t == null ? [] : t.slice(n, r + 1);
});
var Yf = R([Wf], (e) => {
	var t = e.chartData, n = e.dataStartIndex, r = e.dataEndIndex;
	return t == null ? [] : t.slice(n, r + 1);
});
//#endregion
//#region node_modules/recharts/es6/util/isDomainSpecifiedByUser.js
function Xf(e, t) {
	return tp(e) || ep(e, t) || Qf(e, t) || Zf();
}
function Zf() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function Qf(e, t) {
	if (e) {
		if (typeof e == "string") return $f(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? $f(e, t) : void 0;
	}
}
function $f(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function ep(e, t) {
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
function tp(e) {
	if (Array.isArray(e)) return e;
}
function np(e) {
	if (Array.isArray(e) && e.length === 2) {
		var t = Xf(e, 2), n = t[0], r = t[1];
		if (U(n) && U(r)) return !0;
	}
	return !1;
}
function rp(e, t, n) {
	return n ? e : [Math.min(e[0], t[0]), Math.max(e[1], t[1])];
}
function ip(e, t) {
	if (t && typeof e != "function" && Array.isArray(e) && e.length === 2) {
		var n = Xf(e, 2), r = n[0], i = n[1], a, o;
		if (U(r)) a = r;
		else if (typeof r == "function") return;
		if (U(i)) o = i;
		else if (typeof i == "function") return;
		var s = [a, o];
		if (np(s)) return s;
	}
}
function ap(e, t, n) {
	if (!(!n && t == null)) {
		if (typeof e == "function" && t != null) try {
			var r = e(t, n);
			if (np(r)) return rp(r, t, n);
		} catch (e) {}
		if (Array.isArray(e) && e.length === 2) {
			var i = Xf(e, 2), a = i[0], o = i[1], s, c;
			if (a === "auto") t != null && (s = Math.min(...t));
			else if (I(a)) s = a;
			else if (typeof a == "function") try {
				t != null && (s = a(t == null ? void 0 : t[0]));
			} catch (e) {}
			else if (typeof a == "string" && Us.test(a)) {
				var l = Us.exec(a);
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
			else if (typeof o == "string" && Ws.test(o)) {
				var d = Ws.exec(o);
				if (d == null || d[1] == null || t == null) c = void 0;
				else {
					var f = +d[1];
					c = t[1] + f;
				}
			} else c = t == null ? void 0 : t[1];
			var p = [s, c];
			if (np(p)) return t == null ? p : rp(p, t, n);
		}
	}
}
//#endregion
//#region node_modules/recharts/es6/util/scale/util/arithmetic.js
var q = /* @__PURE__ */ l((/* @__PURE__ */ o(((e, t) => {
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
function op(e) {
	return e === 0 ? 1 : Math.floor(new q.default(e).abs().log(10).toNumber()) + 1;
}
function sp(e, t, n) {
	for (var r = new q.default(e), i = 0, a = []; r.lt(t) && i < 1e5;) a.push(r.toNumber()), r = r.add(n), i++;
	return a;
}
//#endregion
//#region node_modules/recharts/es6/util/scale/getNiceTickValues.js
function cp(e, t) {
	return pp(e) || fp(e, t) || up(e, t) || lp();
}
function lp() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function up(e, t) {
	if (e) {
		if (typeof e == "string") return dp(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? dp(e, t) : void 0;
	}
}
function dp(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function fp(e, t) {
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
function pp(e) {
	if (Array.isArray(e)) return e;
}
var mp = (e) => {
	var t = cp(e, 2), n = t[0], r = t[1], i = n, a = r;
	return n > r && (i = r, a = n), [i, a];
}, hp = (e, t, n) => {
	if (e.lte(0)) return new q.default(0);
	var r = op(e.toNumber()), i = new q.default(10).pow(r), a = e.div(i), o = r === 1 ? .1 : .05, s = new q.default(Math.ceil(a.div(o).toNumber())).add(n).mul(o).mul(i);
	return t ? new q.default(s.toNumber()) : new q.default(Math.ceil(s.toNumber()));
}, gp = (e, t, n) => {
	var r;
	if (e.lte(0)) return new q.default(0);
	var i = [
		1,
		2,
		2.5,
		5
	], a = e.toNumber(), o = Math.floor(new q.default(a).abs().log(10).toNumber()), s = new q.default(10).pow(o), c = e.div(s).toNumber(), l = i.findIndex((e) => e >= c - 1e-10);
	if (l === -1 && (s = s.mul(10), l = 0), l += n, l >= i.length) {
		var u = Math.floor(l / i.length);
		l %= i.length, s = s.mul(new q.default(10).pow(u));
	}
	var d = new q.default((r = i[l]) == null ? 1 : r).mul(s);
	return t ? d : new q.default(Math.ceil(d.toNumber()));
}, _p = (e, t, n) => {
	var r = new q.default(1), i = new q.default(e);
	if (!i.isint() && n) {
		var a = Math.abs(e);
		a < 1 ? (r = new q.default(10).pow(op(e) - 1), i = new q.default(Math.floor(i.div(r).toNumber())).mul(r)) : a > 1 && (i = new q.default(Math.floor(e)));
	} else e === 0 ? i = new q.default(Math.floor((t - 1) / 2)) : n || (i = new q.default(Math.floor(e)));
	for (var o = Math.floor((t - 1) / 2), s = [], c = 0; c < t; c++) s.push(i.add(new q.default(c - o).mul(r)).toNumber());
	return s;
}, vp = function(e, t, n, r) {
	var i = arguments.length > 4 && arguments[4] !== void 0 ? arguments[4] : 0, a = arguments.length > 5 && arguments[5] !== void 0 ? arguments[5] : hp;
	if (!Number.isFinite((t - e) / (n - 1))) return {
		step: new q.default(0),
		tickMin: new q.default(0),
		tickMax: new q.default(0)
	};
	var o = a(new q.default(t).sub(e).div(n - 1), r, i), s;
	e <= 0 && t >= 0 ? s = new q.default(0) : (s = new q.default(e).add(t).div(2), s = s.sub(new q.default(s).mod(o)));
	var c = Math.ceil(s.sub(e).div(o).toNumber()), l = Math.ceil(new q.default(t).sub(s).div(o).toNumber()), u = c + l + 1;
	return u > n ? vp(e, t, n, r, i + 1, a) : (u < n && (l = t > 0 ? l + (n - u) : l, c = t > 0 ? c : c + (n - u)), {
		step: o,
		tickMin: s.sub(new q.default(c).mul(o)),
		tickMax: s.add(new q.default(l).mul(o))
	});
}, yp = function(e) {
	var t = cp(e, 2), n = t[0], r = t[1], i = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : 6, a = arguments.length > 2 && arguments[2] !== void 0 ? arguments[2] : !0, o = arguments.length > 3 && arguments[3] !== void 0 ? arguments[3] : "auto", s = Math.max(i, 2), c = cp(mp([n, r]), 2), l = c[0], u = c[1];
	if (l === -Infinity || u === Infinity) {
		var d = u === Infinity ? [l, ...Array(i - 1).fill(Infinity)] : [...Array(i - 1).fill(-Infinity), u];
		return n > r ? d.reverse() : d;
	}
	if (l === u) return _p(l, i, a);
	var f = vp(l, u, s, a, 0, o === "snap125" ? gp : hp), p = f.step, m = f.tickMin, h = f.tickMax, g = sp(m, h.add(new q.default(.1).mul(p)), p);
	return n > r ? g.reverse() : g;
}, bp = function(e, t) {
	var n = cp(e, 2), r = n[0], i = n[1], a = arguments.length > 2 && arguments[2] !== void 0 ? arguments[2] : !0, o = arguments.length > 3 && arguments[3] !== void 0 ? arguments[3] : "auto", s = cp(mp([r, i]), 2), c = s[0], l = s[1];
	if (c === -Infinity || l === Infinity) return [r, i];
	if (c === l) return [c];
	var u = o === "snap125" ? gp : hp, d = Math.max(t, 2), f = u(new q.default(l).sub(c).div(d - 1), a, 0), p = [...sp(new q.default(c), new q.default(l), f), l];
	if (a === !1) {
		p = p.map((e) => Math.round(e));
		var m = p.length - 1;
		m > 0 && p[m] === p[m - 1] && (p = p.slice(0, m));
	}
	return r > i ? p.reverse() : p;
}, xp = (e) => e.rootProps.maxBarSize, Sp = (e) => e.rootProps.barGap, Cp = (e) => e.rootProps.barCategoryGap, wp = (e) => e.rootProps.barSize, Tp = (e) => e.rootProps.stackOffset, Ep = (e) => e.rootProps.reverseStackOrder, Dp = (e) => e.options.chartName, Op = (e) => e.rootProps.syncId, kp = (e) => e.rootProps.syncMethod, Ap = (e) => e.options.eventEmitter, jp = {
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
}, Mp = {
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
	zIndex: jp.axis
}, Np = {
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
	zIndex: jp.axis
}, Pp = (e, t) => {
	if (!(!e || !t)) return e != null && e.reversed ? [t[1], t[0]] : t;
};
//#endregion
//#region node_modules/recharts/es6/util/getAxisTypeBasedOnLayout.js
function Fp(e, t, n) {
	if (n !== "auto") return n;
	if (e != null) return Ns(e, t) ? "category" : "number";
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/polarAxisSelectors.js
function Ip(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Lp(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Ip(Object(n), !0).forEach(function(t) {
			Rp(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Ip(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Rp(e, t, n) {
	return (t = zp(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function zp(e) {
	var t = Bp(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Bp(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var Vp = {
	allowDataOverflow: Mp.allowDataOverflow,
	allowDecimals: Mp.allowDecimals,
	allowDuplicatedCategory: !1,
	dataKey: void 0,
	domain: void 0,
	id: Mp.angleAxisId,
	includeHidden: !1,
	name: void 0,
	reversed: Mp.reversed,
	scale: Mp.scale,
	tick: Mp.tick,
	tickCount: void 0,
	ticks: void 0,
	type: Mp.type,
	unit: void 0,
	niceTicks: "auto"
}, Hp = {
	allowDataOverflow: Np.allowDataOverflow,
	allowDecimals: Np.allowDecimals,
	allowDuplicatedCategory: Np.allowDuplicatedCategory,
	dataKey: void 0,
	domain: void 0,
	id: Np.radiusAxisId,
	includeHidden: Np.includeHidden,
	name: void 0,
	reversed: Np.reversed,
	scale: Np.scale,
	tick: Np.tick,
	tickCount: Np.tickCount,
	ticks: void 0,
	type: Np.type,
	unit: void 0,
	niceTicks: "auto"
}, Up = R([(e, t) => {
	if (t != null) return e.polarAxis.angleAxis[t];
}, al], (e, t) => {
	var n;
	if (e != null) return e;
	var r = (n = Fp(t, "angleAxis", Vp.type)) == null ? "category" : n;
	return Lp(Lp({}, Vp), {}, { type: r });
}), Wp = R([(e, t) => e.polarAxis.radiusAxis[t], al], (e, t) => {
	var n;
	if (e != null) return e;
	var r = (n = Fp(t, "radiusAxis", Hp.type)) == null ? "category" : n;
	return Lp(Lp({}, Hp), {}, { type: r });
}), Gp = (e) => e.polarOptions, Kp = R([
	Xs,
	Zs,
	pc
], vf), qp = R([Gp, Kp], (e, t) => {
	if (e != null) return an(e.innerRadius, t, 0);
}), Jp = R([Gp, Kp], (e, t) => {
	if (e != null) return an(e.outerRadius, t, t * .8);
}), Yp = R([Gp], (e) => e == null ? [0, 0] : [e.startAngle, e.endAngle]);
R([Up, Yp], Pp);
var Xp = R([
	Kp,
	qp,
	Jp
], (e, t, n) => {
	if (!(e == null || t == null || n == null)) return [t, n];
});
R([Wp, Xp], Pp);
var Zp = R([
	K,
	Gp,
	qp,
	Jp,
	Xs,
	Zs
], (e, t, n, r, i, a) => {
	if (!(e !== "centric" && e !== "radial" || t == null || n == null || r == null)) {
		var o = t.cx, s = t.cy, c = t.startAngle, l = t.endAngle;
		return {
			cx: an(o, i, i / 2),
			cy: an(s, a, a / 2),
			innerRadius: n,
			outerRadius: r,
			startAngle: c,
			endAngle: l,
			clockWise: !1
		};
	}
}), Qp = (e, t) => t, $p = (e, t, n) => n;
//#endregion
//#region node_modules/recharts/es6/util/stacks/getStackSeriesIdentifier.js
function em(e) {
	return e == null ? void 0 : e.id;
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineDisplayedStackedData.js
function tm(e, t, n) {
	var r = t.chartData, i = r === void 0 ? [] : r, a = n.allowDuplicatedCategory, o = n.dataKey, s = /* @__PURE__ */ new Map();
	return e.forEach((e) => {
		var t, n = (t = e.data) == null ? i : t;
		if (!(n == null || n.length === 0)) {
			var r = em(e);
			n.forEach((t, n) => {
				var i = o == null || a ? n : String(js(t, o, null)), c = js(t, e.dataKey, 0), l = s.has(i) ? s.get(i) : {};
				Object.assign(l, { [r]: c }), s.set(i, l);
			});
		}
	}), Array.from(s.values());
}
//#endregion
//#region node_modules/recharts/es6/state/types/StackedGraphicalItem.js
function nm(e) {
	return "stackId" in e && e.stackId != null && e.dataKey != null;
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/numberDomainEqualityCheck.js
var rm = (e, t) => e === t ? !0 : e == null || t == null ? !1 : e[0] === t[0] && e[1] === t[1];
//#endregion
//#region node_modules/recharts/es6/state/selectors/arrayEqualityCheck.js
function im(e, t) {
	return Array.isArray(e) && Array.isArray(t) && e.length === 0 && t.length === 0 ? !0 : e === t;
}
function am(e, t) {
	if (e.length === t.length) {
		for (var n = 0; n < e.length; n++) if (e[n] !== t[n]) return !1;
		return !0;
	}
	return !1;
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/selectTooltipAxisType.js
var om = (e) => {
	var t = K(e);
	return t === "horizontal" ? "xAxis" : t === "vertical" ? "yAxis" : t === "centric" ? "angleAxis" : "radiusAxis";
}, sm = (e) => e.tooltip.settings.axisId;
//#endregion
//#region node_modules/recharts/es6/util/scale/RechartsScale.js
function cm(e) {
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
var lm = (e, t) => {
	if (t != null) switch (e) {
		case "linear":
			if (!np(t)) {
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
function um(e, t) {
	return e == null || t == null ? NaN : e < t ? -1 : e > t ? 1 : e >= t ? 0 : NaN;
}
//#endregion
//#region node_modules/d3-array/src/descending.js
function dm(e, t) {
	return e == null || t == null ? NaN : t < e ? -1 : t > e ? 1 : t >= e ? 0 : NaN;
}
//#endregion
//#region node_modules/d3-array/src/bisector.js
function fm(e) {
	let t, n, r;
	e.length === 2 ? (t = e === um || e === dm ? e : pm, n = e, r = e) : (t = um, n = (t, n) => um(e(t), n), r = (t, n) => e(t) - n);
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
function pm() {
	return 0;
}
//#endregion
//#region node_modules/d3-array/src/number.js
function mm(e) {
	return e === null ? NaN : +e;
}
function* hm(e, t) {
	if (t === void 0) for (let t of e) t != null && (t = +t) >= t && (yield t);
	else {
		let n = -1;
		for (let r of e) (r = t(r, ++n, e)) != null && (r = +r) >= r && (yield r);
	}
}
//#endregion
//#region node_modules/d3-array/src/bisect.js
var gm = fm(um), _m = gm.right;
gm.left, fm(mm).center;
//#endregion
//#region node_modules/internmap/src/index.js
var vm = class extends Map {
	constructor(e, t = Sm) {
		if (super(), Object.defineProperties(this, {
			_intern: { value: /* @__PURE__ */ new Map() },
			_key: { value: t }
		}), e != null) for (let [t, n] of e) this.set(t, n);
	}
	get(e) {
		return super.get(ym(this, e));
	}
	has(e) {
		return super.has(ym(this, e));
	}
	set(e, t) {
		return super.set(bm(this, e), t);
	}
	delete(e) {
		return super.delete(xm(this, e));
	}
};
function ym({ _intern: e, _key: t }, n) {
	let r = t(n);
	return e.has(r) ? e.get(r) : n;
}
function bm({ _intern: e, _key: t }, n) {
	let r = t(n);
	return e.has(r) ? e.get(r) : (e.set(r, n), n);
}
function xm({ _intern: e, _key: t }, n) {
	let r = t(n);
	return e.has(r) && (n = e.get(r), e.delete(r)), n;
}
function Sm(e) {
	return typeof e == "object" && e ? e.valueOf() : e;
}
//#endregion
//#region node_modules/d3-array/src/sort.js
function Cm(e = um) {
	if (e === um) return wm;
	if (typeof e != "function") throw TypeError("compare is not a function");
	return (t, n) => {
		let r = e(t, n);
		return r || r === 0 ? r : (e(n, n) === 0) - (e(t, t) === 0);
	};
}
function wm(e, t) {
	return (e == null || !(e >= e)) - (t == null || !(t >= t)) || (e < t ? -1 : +(e > t));
}
//#endregion
//#region node_modules/d3-array/src/ticks.js
var Tm = Math.sqrt(50), Em = Math.sqrt(10), Dm = Math.sqrt(2);
function Om(e, t, n) {
	let r = (t - e) / Math.max(0, n), i = Math.floor(Math.log10(r)), a = r / 10 ** i, o = a >= Tm ? 10 : a >= Em ? 5 : a >= Dm ? 2 : 1, s, c, l;
	return i < 0 ? (l = 10 ** -i / o, s = Math.round(e * l), c = Math.round(t * l), s / l < e && ++s, c / l > t && --c, l = -l) : (l = 10 ** i * o, s = Math.round(e / l), c = Math.round(t / l), s * l < e && ++s, c * l > t && --c), c < s && .5 <= n && n < 2 ? Om(e, t, n * 2) : [
		s,
		c,
		l
	];
}
function km(e, t, n) {
	if (t = +t, e = +e, n = +n, !(n > 0)) return [];
	if (e === t) return [e];
	let r = t < e, [i, a, o] = r ? Om(t, e, n) : Om(e, t, n);
	if (!(a >= i)) return [];
	let s = a - i + 1, c = Array(s);
	if (r) if (o < 0) for (let e = 0; e < s; ++e) c[e] = (a - e) / -o;
	else for (let e = 0; e < s; ++e) c[e] = (a - e) * o;
	else if (o < 0) for (let e = 0; e < s; ++e) c[e] = (i + e) / -o;
	else for (let e = 0; e < s; ++e) c[e] = (i + e) * o;
	return c;
}
function Am(e, t, n) {
	return t = +t, e = +e, n = +n, Om(e, t, n)[2];
}
function jm(e, t, n) {
	t = +t, e = +e, n = +n;
	let r = t < e, i = r ? Am(t, e, n) : Am(e, t, n);
	return (r ? -1 : 1) * (i < 0 ? 1 / -i : i);
}
//#endregion
//#region node_modules/d3-array/src/max.js
function Mm(e, t) {
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
function Nm(e, t) {
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
function Pm(e, t, n = 0, r = Infinity, i) {
	if (t = Math.floor(t), n = Math.floor(Math.max(0, n)), r = Math.floor(Math.min(e.length - 1, r)), !(n <= t && t <= r)) return e;
	for (i = i === void 0 ? wm : Cm(i); r > n;) {
		if (r - n > 600) {
			let a = r - n + 1, o = t - n + 1, s = Math.log(a), c = .5 * Math.exp(2 * s / 3), l = .5 * Math.sqrt(s * c * (a - c) / a) * (o - a / 2 < 0 ? -1 : 1), u = Math.max(n, Math.floor(t - o * c / a + l)), d = Math.min(r, Math.floor(t + (a - o) * c / a + l));
			Pm(e, t, u, d, i);
		}
		let a = e[t], o = n, s = r;
		for (Fm(e, n, t), i(e[r], a) > 0 && Fm(e, n, r); o < s;) {
			for (Fm(e, o, s), ++o, --s; i(e[o], a) < 0;) ++o;
			for (; i(e[s], a) > 0;) --s;
		}
		i(e[n], a) === 0 ? Fm(e, n, s) : (++s, Fm(e, s, r)), s <= t && (n = s + 1), t <= s && (r = s - 1);
	}
	return e;
}
function Fm(e, t, n) {
	let r = e[t];
	e[t] = e[n], e[n] = r;
}
//#endregion
//#region node_modules/d3-array/src/quantile.js
function Im(e, t, n) {
	if (e = Float64Array.from(hm(e, n)), !(!(r = e.length) || isNaN(t = +t))) {
		if (t <= 0 || r < 2) return Nm(e);
		if (t >= 1) return Mm(e);
		var r, i = (r - 1) * t, a = Math.floor(i), o = Mm(Pm(e, a).subarray(0, a + 1));
		return o + (Nm(e.subarray(a + 1)) - o) * (i - a);
	}
}
function Lm(e, t, n = mm) {
	if (!(!(r = e.length) || isNaN(t = +t))) {
		if (t <= 0 || r < 2) return +n(e[0], 0, e);
		if (t >= 1) return +n(e[r - 1], r - 1, e);
		var r, i = (r - 1) * t, a = Math.floor(i), o = +n(e[a], a, e);
		return o + (+n(e[a + 1], a + 1, e) - o) * (i - a);
	}
}
//#endregion
//#region node_modules/d3-array/src/range.js
function Rm(e, t, n) {
	e = +e, t = +t, n = (i = arguments.length) < 2 ? (t = e, e = 0, 1) : i < 3 ? 1 : +n;
	for (var r = -1, i = Math.max(0, Math.ceil((t - e) / n)) | 0, a = Array(i); ++r < i;) a[r] = e + r * n;
	return a;
}
//#endregion
//#region node_modules/d3-scale/src/init.js
function zm(e, t) {
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
function Bm(e, t) {
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
var Vm = Symbol("implicit");
function Hm() {
	var e = new vm(), t = [], n = [], r = Vm;
	function i(i) {
		let a = e.get(i);
		if (a === void 0) {
			if (r !== Vm) return r;
			e.set(i, a = t.push(i) - 1);
		}
		return n[a % n.length];
	}
	return i.domain = function(n) {
		if (!arguments.length) return t.slice();
		t = [], e = new vm();
		for (let r of n) e.has(r) || e.set(r, t.push(r) - 1);
		return i;
	}, i.range = function(e) {
		return arguments.length ? (n = Array.from(e), i) : n.slice();
	}, i.unknown = function(e) {
		return arguments.length ? (r = e, i) : r;
	}, i.copy = function() {
		return Hm(t, n).unknown(r);
	}, zm.apply(i, arguments), i;
}
//#endregion
//#region node_modules/d3-scale/src/band.js
function Um() {
	var e = Hm().unknown(void 0), t = e.domain, n = e.range, r = 0, i = 1, a, o, s = !1, c = 0, l = 0, u = .5;
	delete e.unknown;
	function d() {
		var e = t().length, d = i < r, f = d ? i : r, p = d ? r : i;
		a = (p - f) / Math.max(1, e - c + l * 2), s && (a = Math.floor(a)), f += (p - f - a * (e - c)) * u, o = a * (1 - c), s && (f = Math.round(f), o = Math.round(o));
		var m = Rm(e).map(function(e) {
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
		return Um(t(), [r, i]).round(s).paddingInner(c).paddingOuter(l).align(u);
	}, zm.apply(d(), arguments);
}
function Wm(e) {
	var t = e.copy;
	return e.padding = e.paddingOuter, delete e.paddingInner, delete e.paddingOuter, e.copy = function() {
		return Wm(t());
	}, e;
}
function Gm() {
	return Wm(Um.apply(null, arguments).paddingInner(1));
}
//#endregion
//#region node_modules/d3-color/src/define.js
function Km(e, t, n) {
	e.prototype = t.prototype = n, n.constructor = e;
}
function qm(e, t) {
	var n = Object.create(e.prototype);
	for (var r in t) n[r] = t[r];
	return n;
}
//#endregion
//#region node_modules/d3-color/src/color.js
function Jm() {}
var Ym = .7, Xm = 1 / Ym, Zm = "\\s*([+-]?\\d+)\\s*", Qm = "\\s*([+-]?(?:\\d*\\.)?\\d+(?:[eE][+-]?\\d+)?)\\s*", $m = "\\s*([+-]?(?:\\d*\\.)?\\d+(?:[eE][+-]?\\d+)?)%\\s*", eh = /^#([0-9a-f]{3,8})$/, th = RegExp(`^rgb\\(${Zm},${Zm},${Zm}\\)$`), nh = RegExp(`^rgb\\(${$m},${$m},${$m}\\)$`), rh = RegExp(`^rgba\\(${Zm},${Zm},${Zm},${Qm}\\)$`), ih = RegExp(`^rgba\\(${$m},${$m},${$m},${Qm}\\)$`), ah = RegExp(`^hsl\\(${Qm},${$m},${$m}\\)$`), oh = RegExp(`^hsla\\(${Qm},${$m},${$m},${Qm}\\)$`), sh = {
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
Km(Jm, fh, {
	copy(e) {
		return Object.assign(new this.constructor(), this, e);
	},
	displayable() {
		return this.rgb().displayable();
	},
	hex: ch,
	formatHex: ch,
	formatHex8: lh,
	formatHsl: uh,
	formatRgb: dh,
	toString: dh
});
function ch() {
	return this.rgb().formatHex();
}
function lh() {
	return this.rgb().formatHex8();
}
function uh() {
	return Th(this).formatHsl();
}
function dh() {
	return this.rgb().formatRgb();
}
function fh(e) {
	var t, n;
	return e = (e + "").trim().toLowerCase(), (t = eh.exec(e)) ? (n = t[1].length, t = parseInt(t[1], 16), n === 6 ? ph(t) : n === 3 ? new _h(t >> 8 & 15 | t >> 4 & 240, t >> 4 & 15 | t & 240, (t & 15) << 4 | t & 15, 1) : n === 8 ? mh(t >> 24 & 255, t >> 16 & 255, t >> 8 & 255, (t & 255) / 255) : n === 4 ? mh(t >> 12 & 15 | t >> 8 & 240, t >> 8 & 15 | t >> 4 & 240, t >> 4 & 15 | t & 240, ((t & 15) << 4 | t & 15) / 255) : null) : (t = th.exec(e)) ? new _h(t[1], t[2], t[3], 1) : (t = nh.exec(e)) ? new _h(t[1] * 255 / 100, t[2] * 255 / 100, t[3] * 255 / 100, 1) : (t = rh.exec(e)) ? mh(t[1], t[2], t[3], t[4]) : (t = ih.exec(e)) ? mh(t[1] * 255 / 100, t[2] * 255 / 100, t[3] * 255 / 100, t[4]) : (t = ah.exec(e)) ? wh(t[1], t[2] / 100, t[3] / 100, 1) : (t = oh.exec(e)) ? wh(t[1], t[2] / 100, t[3] / 100, t[4]) : sh.hasOwnProperty(e) ? ph(sh[e]) : e === "transparent" ? new _h(NaN, NaN, NaN, 0) : null;
}
function ph(e) {
	return new _h(e >> 16 & 255, e >> 8 & 255, e & 255, 1);
}
function mh(e, t, n, r) {
	return r <= 0 && (e = t = n = NaN), new _h(e, t, n, r);
}
function hh(e) {
	return e instanceof Jm || (e = fh(e)), e ? (e = e.rgb(), new _h(e.r, e.g, e.b, e.opacity)) : new _h();
}
function gh(e, t, n, r) {
	return arguments.length === 1 ? hh(e) : new _h(e, t, n, r == null ? 1 : r);
}
function _h(e, t, n, r) {
	this.r = +e, this.g = +t, this.b = +n, this.opacity = +r;
}
Km(_h, gh, qm(Jm, {
	brighter(e) {
		return e = e == null ? Xm : Xm ** +e, new _h(this.r * e, this.g * e, this.b * e, this.opacity);
	},
	darker(e) {
		return e = e == null ? Ym : Ym ** +e, new _h(this.r * e, this.g * e, this.b * e, this.opacity);
	},
	rgb() {
		return this;
	},
	clamp() {
		return new _h(Sh(this.r), Sh(this.g), Sh(this.b), xh(this.opacity));
	},
	displayable() {
		return -.5 <= this.r && this.r < 255.5 && -.5 <= this.g && this.g < 255.5 && -.5 <= this.b && this.b < 255.5 && 0 <= this.opacity && this.opacity <= 1;
	},
	hex: vh,
	formatHex: vh,
	formatHex8: yh,
	formatRgb: bh,
	toString: bh
}));
function vh() {
	return `#${Ch(this.r)}${Ch(this.g)}${Ch(this.b)}`;
}
function yh() {
	return `#${Ch(this.r)}${Ch(this.g)}${Ch(this.b)}${Ch((isNaN(this.opacity) ? 1 : this.opacity) * 255)}`;
}
function bh() {
	let e = xh(this.opacity);
	return `${e === 1 ? "rgb(" : "rgba("}${Sh(this.r)}, ${Sh(this.g)}, ${Sh(this.b)}${e === 1 ? ")" : `, ${e})`}`;
}
function xh(e) {
	return isNaN(e) ? 1 : Math.max(0, Math.min(1, e));
}
function Sh(e) {
	return Math.max(0, Math.min(255, Math.round(e) || 0));
}
function Ch(e) {
	return e = Sh(e), (e < 16 ? "0" : "") + e.toString(16);
}
function wh(e, t, n, r) {
	return r <= 0 ? e = t = n = NaN : n <= 0 || n >= 1 ? e = t = NaN : t <= 0 && (e = NaN), new Dh(e, t, n, r);
}
function Th(e) {
	if (e instanceof Dh) return new Dh(e.h, e.s, e.l, e.opacity);
	if (e instanceof Jm || (e = fh(e)), !e) return new Dh();
	if (e instanceof Dh) return e;
	e = e.rgb();
	var t = e.r / 255, n = e.g / 255, r = e.b / 255, i = Math.min(t, n, r), a = Math.max(t, n, r), o = NaN, s = a - i, c = (a + i) / 2;
	return s ? (o = t === a ? (n - r) / s + (n < r) * 6 : n === a ? (r - t) / s + 2 : (t - n) / s + 4, s /= c < .5 ? a + i : 2 - a - i, o *= 60) : s = c > 0 && c < 1 ? 0 : o, new Dh(o, s, c, e.opacity);
}
function Eh(e, t, n, r) {
	return arguments.length === 1 ? Th(e) : new Dh(e, t, n, r == null ? 1 : r);
}
function Dh(e, t, n, r) {
	this.h = +e, this.s = +t, this.l = +n, this.opacity = +r;
}
Km(Dh, Eh, qm(Jm, {
	brighter(e) {
		return e = e == null ? Xm : Xm ** +e, new Dh(this.h, this.s, this.l * e, this.opacity);
	},
	darker(e) {
		return e = e == null ? Ym : Ym ** +e, new Dh(this.h, this.s, this.l * e, this.opacity);
	},
	rgb() {
		var e = this.h % 360 + (this.h < 0) * 360, t = isNaN(e) || isNaN(this.s) ? 0 : this.s, n = this.l, r = n + (n < .5 ? n : 1 - n) * t, i = 2 * n - r;
		return new _h(Ah(e >= 240 ? e - 240 : e + 120, i, r), Ah(e, i, r), Ah(e < 120 ? e + 240 : e - 120, i, r), this.opacity);
	},
	clamp() {
		return new Dh(Oh(this.h), kh(this.s), kh(this.l), xh(this.opacity));
	},
	displayable() {
		return (0 <= this.s && this.s <= 1 || isNaN(this.s)) && 0 <= this.l && this.l <= 1 && 0 <= this.opacity && this.opacity <= 1;
	},
	formatHsl() {
		let e = xh(this.opacity);
		return `${e === 1 ? "hsl(" : "hsla("}${Oh(this.h)}, ${kh(this.s) * 100}%, ${kh(this.l) * 100}%${e === 1 ? ")" : `, ${e})`}`;
	}
}));
function Oh(e) {
	return e = (e || 0) % 360, e < 0 ? e + 360 : e;
}
function kh(e) {
	return Math.max(0, Math.min(1, e || 0));
}
function Ah(e, t, n) {
	return (e < 60 ? t + (n - t) * e / 60 : e < 180 ? n : e < 240 ? t + (n - t) * (240 - e) / 60 : t) * 255;
}
//#endregion
//#region node_modules/d3-interpolate/src/constant.js
var jh = (e) => () => e;
//#endregion
//#region node_modules/d3-interpolate/src/color.js
function Mh(e, t) {
	return function(n) {
		return e + n * t;
	};
}
function Nh(e, t, n) {
	return e **= +n, t = t ** +n - e, n = 1 / n, function(r) {
		return (e + r * t) ** +n;
	};
}
function Ph(e) {
	return (e = +e) == 1 ? Fh : function(t, n) {
		return n - t ? Nh(t, n, e) : jh(isNaN(t) ? n : t);
	};
}
function Fh(e, t) {
	var n = t - e;
	return n ? Mh(e, n) : jh(isNaN(e) ? t : e);
}
//#endregion
//#region node_modules/d3-interpolate/src/rgb.js
var Ih = (function e(t) {
	var n = Ph(t);
	function r(e, t) {
		var r = n((e = gh(e)).r, (t = gh(t)).r), i = n(e.g, t.g), a = n(e.b, t.b), o = Fh(e.opacity, t.opacity);
		return function(t) {
			return e.r = r(t), e.g = i(t), e.b = a(t), e.opacity = o(t), e + "";
		};
	}
	return r.gamma = e, r;
})(1);
//#endregion
//#region node_modules/d3-interpolate/src/numberArray.js
function Lh(e, t) {
	t || (t = []);
	var n = e ? Math.min(t.length, e.length) : 0, r = t.slice(), i;
	return function(a) {
		for (i = 0; i < n; ++i) r[i] = e[i] * (1 - a) + t[i] * a;
		return r;
	};
}
function Rh(e) {
	return ArrayBuffer.isView(e) && !(e instanceof DataView);
}
//#endregion
//#region node_modules/d3-interpolate/src/array.js
function zh(e, t) {
	var n = t ? t.length : 0, r = e ? Math.min(n, e.length) : 0, i = Array(r), a = Array(n), o;
	for (o = 0; o < r; ++o) i[o] = Jh(e[o], t[o]);
	for (; o < n; ++o) a[o] = t[o];
	return function(e) {
		for (o = 0; o < r; ++o) a[o] = i[o](e);
		return a;
	};
}
//#endregion
//#region node_modules/d3-interpolate/src/date.js
function Bh(e, t) {
	var n = /* @__PURE__ */ new Date();
	return e = +e, t = +t, function(r) {
		return n.setTime(e * (1 - r) + t * r), n;
	};
}
//#endregion
//#region node_modules/d3-interpolate/src/number.js
function Vh(e, t) {
	return e = +e, t = +t, function(n) {
		return e * (1 - n) + t * n;
	};
}
//#endregion
//#region node_modules/d3-interpolate/src/object.js
function Hh(e, t) {
	var n = {}, r = {}, i;
	for (i in (typeof e != "object" || !e) && (e = {}), (typeof t != "object" || !t) && (t = {}), t) i in e ? n[i] = Jh(e[i], t[i]) : r[i] = t[i];
	return function(e) {
		for (i in n) r[i] = n[i](e);
		return r;
	};
}
//#endregion
//#region node_modules/d3-interpolate/src/string.js
var Uh = /[-+]?(?:\d+\.?\d*|\.?\d+)(?:[eE][-+]?\d+)?/g, Wh = new RegExp(Uh.source, "g");
function Gh(e) {
	return function() {
		return e;
	};
}
function Kh(e) {
	return function(t) {
		return e(t) + "";
	};
}
function qh(e, t) {
	var n = Uh.lastIndex = Wh.lastIndex = 0, r, i, a, o = -1, s = [], c = [];
	for (e += "", t += ""; (r = Uh.exec(e)) && (i = Wh.exec(t));) (a = i.index) > n && (a = t.slice(n, a), s[o] ? s[o] += a : s[++o] = a), (r = r[0]) === (i = i[0]) ? s[o] ? s[o] += i : s[++o] = i : (s[++o] = null, c.push({
		i: o,
		x: Vh(r, i)
	})), n = Wh.lastIndex;
	return n < t.length && (a = t.slice(n), s[o] ? s[o] += a : s[++o] = a), s.length < 2 ? c[0] ? Kh(c[0].x) : Gh(t) : (t = c.length, function(e) {
		for (var n = 0, r; n < t; ++n) s[(r = c[n]).i] = r.x(e);
		return s.join("");
	});
}
//#endregion
//#region node_modules/d3-interpolate/src/value.js
function Jh(e, t) {
	var n = typeof t, r;
	return t == null || n === "boolean" ? jh(t) : (n === "number" ? Vh : n === "string" ? (r = fh(t)) ? (t = r, Ih) : qh : t instanceof fh ? Ih : t instanceof Date ? Bh : Rh(t) ? Lh : Array.isArray(t) ? zh : typeof t.valueOf != "function" && typeof t.toString != "function" || isNaN(t) ? Hh : Vh)(e, t);
}
//#endregion
//#region node_modules/d3-interpolate/src/round.js
function Yh(e, t) {
	return e = +e, t = +t, function(n) {
		return Math.round(e * (1 - n) + t * n);
	};
}
//#endregion
//#region node_modules/d3-interpolate/src/piecewise.js
function Xh(e, t) {
	t === void 0 && (t = e, e = Jh);
	for (var n = 0, r = t.length - 1, i = t[0], a = Array(r < 0 ? 0 : r); n < r;) a[n] = e(i, i = t[++n]);
	return function(e) {
		var t = Math.max(0, Math.min(r - 1, Math.floor(e *= r)));
		return a[t](e - t);
	};
}
//#endregion
//#region node_modules/d3-scale/src/constant.js
function Zh(e) {
	return function() {
		return e;
	};
}
//#endregion
//#region node_modules/d3-scale/src/number.js
function Qh(e) {
	return +e;
}
//#endregion
//#region node_modules/d3-scale/src/continuous.js
var $h = [0, 1];
function eg(e) {
	return e;
}
function tg(e, t) {
	return (t -= e = +e) ? function(n) {
		return (n - e) / t;
	} : Zh(isNaN(t) ? NaN : .5);
}
function ng(e, t) {
	var n;
	return e > t && (n = e, e = t, t = n), function(n) {
		return Math.max(e, Math.min(t, n));
	};
}
function rg(e, t, n) {
	var r = e[0], i = e[1], a = t[0], o = t[1];
	return i < r ? (r = tg(i, r), a = n(o, a)) : (r = tg(r, i), a = n(a, o)), function(e) {
		return a(r(e));
	};
}
function ig(e, t, n) {
	var r = Math.min(e.length, t.length) - 1, i = Array(r), a = Array(r), o = -1;
	for (e[r] < e[0] && (e = e.slice().reverse(), t = t.slice().reverse()); ++o < r;) i[o] = tg(e[o], e[o + 1]), a[o] = n(t[o], t[o + 1]);
	return function(t) {
		var n = _m(e, t, 1, r) - 1;
		return a[n](i[n](t));
	};
}
function ag(e, t) {
	return t.domain(e.domain()).range(e.range()).interpolate(e.interpolate()).clamp(e.clamp()).unknown(e.unknown());
}
function og() {
	var e = $h, t = $h, n = Jh, r, i, a, o = eg, s, c, l;
	function u() {
		var n = Math.min(e.length, t.length);
		return o !== eg && (o = ng(e[0], e[n - 1])), s = n > 2 ? ig : rg, c = l = null, d;
	}
	function d(i) {
		return i == null || isNaN(i = +i) ? a : (c || (c = s(e.map(r), t, n)))(r(o(i)));
	}
	return d.invert = function(n) {
		return o(i((l || (l = s(t, e.map(r), Vh)))(n)));
	}, d.domain = function(t) {
		return arguments.length ? (e = Array.from(t, Qh), u()) : e.slice();
	}, d.range = function(e) {
		return arguments.length ? (t = Array.from(e), u()) : t.slice();
	}, d.rangeRound = function(e) {
		return t = Array.from(e), n = Yh, u();
	}, d.clamp = function(e) {
		return arguments.length ? (o = e ? !0 : eg, u()) : o !== eg;
	}, d.interpolate = function(e) {
		return arguments.length ? (n = e, u()) : n;
	}, d.unknown = function(e) {
		return arguments.length ? (a = e, d) : a;
	}, function(e, t) {
		return r = e, i = t, u();
	};
}
function sg() {
	return og()(eg, eg);
}
//#endregion
//#region node_modules/d3-format/src/formatDecimal.js
function cg(e) {
	return Math.abs(e = Math.round(e)) >= 1e21 ? e.toLocaleString("en").replace(/,/g, "") : e.toString(10);
}
function lg(e, t) {
	if (!isFinite(e) || e === 0) return null;
	var n = (e = t ? e.toExponential(t - 1) : e.toExponential()).indexOf("e"), r = e.slice(0, n);
	return [r.length > 1 ? r[0] + r.slice(2) : r, +e.slice(n + 1)];
}
//#endregion
//#region node_modules/d3-format/src/exponent.js
function ug(e) {
	return e = lg(Math.abs(e)), e ? e[1] : NaN;
}
//#endregion
//#region node_modules/d3-format/src/formatGroup.js
function dg(e, t) {
	return function(n, r) {
		for (var i = n.length, a = [], o = 0, s = e[0], c = 0; i > 0 && s > 0 && (c + s + 1 > r && (s = Math.max(1, r - c)), a.push(n.substring(i -= s, i + s)), !((c += s + 1) > r));) s = e[o = (o + 1) % e.length];
		return a.reverse().join(t);
	};
}
//#endregion
//#region node_modules/d3-format/src/formatNumerals.js
function fg(e) {
	return function(t) {
		return t.replace(/[0-9]/g, function(t) {
			return e[+t];
		});
	};
}
//#endregion
//#region node_modules/d3-format/src/formatSpecifier.js
var pg = /^(?:(.)?([<>=^]))?([+\-( ])?([$#])?(0)?(\d+)?(,)?(\.\d+)?(~)?([a-z%])?$/i;
function mg(e) {
	if (!(t = pg.exec(e))) throw Error("invalid format: " + e);
	var t;
	return new hg({
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
mg.prototype = hg.prototype;
function hg(e) {
	this.fill = e.fill === void 0 ? " " : e.fill + "", this.align = e.align === void 0 ? ">" : e.align + "", this.sign = e.sign === void 0 ? "-" : e.sign + "", this.symbol = e.symbol === void 0 ? "" : e.symbol + "", this.zero = !!e.zero, this.width = e.width === void 0 ? void 0 : +e.width, this.comma = !!e.comma, this.precision = e.precision === void 0 ? void 0 : +e.precision, this.trim = !!e.trim, this.type = e.type === void 0 ? "" : e.type + "";
}
hg.prototype.toString = function() {
	return this.fill + this.align + this.sign + this.symbol + (this.zero ? "0" : "") + (this.width === void 0 ? "" : Math.max(1, this.width | 0)) + (this.comma ? "," : "") + (this.precision === void 0 ? "" : "." + Math.max(0, this.precision | 0)) + (this.trim ? "~" : "") + this.type;
};
//#endregion
//#region node_modules/d3-format/src/formatTrim.js
function gg(e) {
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
var _g;
function vg(e, t) {
	var n = lg(e, t);
	if (!n) return _g = void 0, e.toPrecision(t);
	var r = n[0], i = n[1], a = i - (_g = Math.max(-8, Math.min(8, Math.floor(i / 3))) * 3) + 1, o = r.length;
	return a === o ? r : a > o ? r + Array(a - o + 1).join("0") : a > 0 ? r.slice(0, a) + "." + r.slice(a) : "0." + Array(1 - a).join("0") + lg(e, Math.max(0, t + a - 1))[0];
}
//#endregion
//#region node_modules/d3-format/src/formatRounded.js
function yg(e, t) {
	var n = lg(e, t);
	if (!n) return e + "";
	var r = n[0], i = n[1];
	return i < 0 ? "0." + Array(-i).join("0") + r : r.length > i + 1 ? r.slice(0, i + 1) + "." + r.slice(i + 1) : r + Array(i - r.length + 2).join("0");
}
//#endregion
//#region node_modules/d3-format/src/formatTypes.js
var bg = {
	"%": (e, t) => (e * 100).toFixed(t),
	b: (e) => Math.round(e).toString(2),
	c: (e) => e + "",
	d: cg,
	e: (e, t) => e.toExponential(t),
	f: (e, t) => e.toFixed(t),
	g: (e, t) => e.toPrecision(t),
	o: (e) => Math.round(e).toString(8),
	p: (e, t) => yg(e * 100, t),
	r: yg,
	s: vg,
	X: (e) => Math.round(e).toString(16).toUpperCase(),
	x: (e) => Math.round(e).toString(16)
};
//#endregion
//#region node_modules/d3-format/src/identity.js
function xg(e) {
	return e;
}
//#endregion
//#region node_modules/d3-format/src/locale.js
var Sg = Array.prototype.map, Cg = [
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
function wg(e) {
	var t = e.grouping === void 0 || e.thousands === void 0 ? xg : dg(Sg.call(e.grouping, Number), e.thousands + ""), n = e.currency === void 0 ? "" : e.currency[0] + "", r = e.currency === void 0 ? "" : e.currency[1] + "", i = e.decimal === void 0 ? "." : e.decimal + "", a = e.numerals === void 0 ? xg : fg(Sg.call(e.numerals, String)), o = e.percent === void 0 ? "%" : e.percent + "", s = e.minus === void 0 ? "−" : e.minus + "", c = e.nan === void 0 ? "NaN" : e.nan + "";
	function l(e, l) {
		e = mg(e);
		var u = e.fill, d = e.align, f = e.sign, p = e.symbol, m = e.zero, h = e.width, g = e.comma, _ = e.precision, v = e.trim, y = e.type;
		y === "n" ? (g = !0, y = "g") : bg[y] || (_ === void 0 && (_ = 12), v = !0, y = "g"), (m || u === "0" && d === "=") && (m = !0, u = "0", d = "=");
		var b = (l && l.prefix !== void 0 ? l.prefix : "") + (p === "$" ? n : p === "#" && /[boxX]/.test(y) ? "0" + y.toLowerCase() : ""), x = (p === "$" ? r : /[%p]/.test(y) ? o : "") + (l && l.suffix !== void 0 ? l.suffix : ""), S = bg[y], C = /[defgprs%]/.test(y);
		_ = _ === void 0 ? 6 : /[gprs]/.test(y) ? Math.max(1, Math.min(21, _)) : Math.max(0, Math.min(20, _));
		function w(e) {
			var n = b, r = x, o, l, p;
			if (y === "c") r = S(e) + r, e = "";
			else {
				e = +e;
				var w = e < 0 || 1 / e < 0;
				if (e = isNaN(e) ? c : S(Math.abs(e), _), v && (e = gg(e)), w && +e == 0 && f !== "+" && (w = !1), n = (w ? f === "(" ? f : s : f === "-" || f === "(" ? "" : f) + n, r = (y === "s" && !isNaN(e) && _g !== void 0 ? Cg[8 + _g / 3] : "") + r + (w && f === "(" ? ")" : ""), C) {
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
		var n = Math.max(-8, Math.min(8, Math.floor(ug(t) / 3))) * 3, r = 10 ** -n, i = l((e = mg(e), e.type = "f", e), { suffix: Cg[8 + n / 3] });
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
var Tg, Eg, Dg;
Og({
	thousands: ",",
	grouping: [3],
	currency: ["$", ""]
});
function Og(e) {
	return Tg = wg(e), Eg = Tg.format, Dg = Tg.formatPrefix, Tg;
}
//#endregion
//#region node_modules/d3-format/src/precisionFixed.js
function kg(e) {
	return Math.max(0, -ug(Math.abs(e)));
}
//#endregion
//#region node_modules/d3-format/src/precisionPrefix.js
function Ag(e, t) {
	return Math.max(0, Math.max(-8, Math.min(8, Math.floor(ug(t) / 3))) * 3 - ug(Math.abs(e)));
}
//#endregion
//#region node_modules/d3-format/src/precisionRound.js
function jg(e, t) {
	return e = Math.abs(e), t = Math.abs(t) - e, Math.max(0, ug(t) - ug(e)) + 1;
}
//#endregion
//#region node_modules/d3-scale/src/tickFormat.js
function Mg(e, t, n, r) {
	var i = jm(e, t, n), a;
	switch (r = mg(r == null ? ",f" : r), r.type) {
		case "s":
			var o = Math.max(Math.abs(e), Math.abs(t));
			return r.precision == null && !isNaN(a = Ag(i, o)) && (r.precision = a), Dg(r, o);
		case "":
		case "e":
		case "g":
		case "p":
		case "r":
			r.precision == null && !isNaN(a = jg(i, Math.max(Math.abs(e), Math.abs(t)))) && (r.precision = a - (r.type === "e"));
			break;
		case "f":
		case "%":
			r.precision == null && !isNaN(a = kg(i)) && (r.precision = a - (r.type === "%") * 2);
			break;
	}
	return Eg(r);
}
//#endregion
//#region node_modules/d3-scale/src/linear.js
function Ng(e) {
	var t = e.domain;
	return e.ticks = function(e) {
		var n = t();
		return km(n[0], n[n.length - 1], e == null ? 10 : e);
	}, e.tickFormat = function(e, n) {
		var r = t();
		return Mg(r[0], r[r.length - 1], e == null ? 10 : e, n);
	}, e.nice = function(n) {
		n == null && (n = 10);
		var r = t(), i = 0, a = r.length - 1, o = r[i], s = r[a], c, l, u = 10;
		for (s < o && (l = o, o = s, s = l, l = i, i = a, a = l); u-- > 0;) {
			if (l = Am(o, s, n), l === c) return r[i] = o, r[a] = s, t(r);
			if (l > 0) o = Math.floor(o / l) * l, s = Math.ceil(s / l) * l;
			else if (l < 0) o = Math.ceil(o * l) / l, s = Math.floor(s * l) / l;
			else break;
			c = l;
		}
		return e;
	}, e;
}
function Pg() {
	var e = sg();
	return e.copy = function() {
		return ag(e, Pg());
	}, zm.apply(e, arguments), Ng(e);
}
//#endregion
//#region node_modules/d3-scale/src/identity.js
function Fg(e) {
	var t;
	function n(e) {
		return e == null || isNaN(e = +e) ? t : e;
	}
	return n.invert = n, n.domain = n.range = function(t) {
		return arguments.length ? (e = Array.from(t, Qh), n) : e.slice();
	}, n.unknown = function(e) {
		return arguments.length ? (t = e, n) : t;
	}, n.copy = function() {
		return Fg(e).unknown(t);
	}, e = arguments.length ? Array.from(e, Qh) : [0, 1], Ng(n);
}
//#endregion
//#region node_modules/d3-scale/src/nice.js
function Ig(e, t) {
	e = e.slice();
	var n = 0, r = e.length - 1, i = e[n], a = e[r], o;
	return a < i && (o = n, n = r, r = o, o = i, i = a, a = o), e[n] = t.floor(i), e[r] = t.ceil(a), e;
}
//#endregion
//#region node_modules/d3-scale/src/log.js
function Lg(e) {
	return Math.log(e);
}
function Rg(e) {
	return Math.exp(e);
}
function zg(e) {
	return -Math.log(-e);
}
function Bg(e) {
	return -Math.exp(-e);
}
function Vg(e) {
	return isFinite(e) ? +("1e" + e) : e < 0 ? 0 : e;
}
function Hg(e) {
	return e === 10 ? Vg : e === Math.E ? Math.exp : (t) => e ** +t;
}
function Ug(e) {
	return e === Math.E ? Math.log : e === 10 && Math.log10 || e === 2 && Math.log2 || (e = Math.log(e), (t) => Math.log(t) / e);
}
function Wg(e) {
	return (t, n) => -e(-t, n);
}
function Gg(e) {
	let t = e(Lg, Rg), n = t.domain, r = 10, i, a;
	function o() {
		return i = Ug(r), a = Hg(r), n()[0] < 0 ? (i = Wg(i), a = Wg(a), e(zg, Bg)) : e(Lg, Rg), t;
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
			m.length * 2 < p && (m = km(o, s, p));
		} else m = km(l, u, Math.min(u - l, p)).map(a);
		return c ? m.reverse() : m;
	}, t.tickFormat = (e, n) => {
		if (e == null && (e = 10), n == null && (n = r === 10 ? "s" : ","), typeof n != "function" && (!(r % 1) && (n = mg(n)).precision == null && (n.trim = !0), n = Eg(n)), e === Infinity) return n;
		let o = Math.max(1, r * e / t.ticks().length);
		return (e) => {
			let t = e / a(Math.round(i(e)));
			return t * r < r - .5 && (t *= r), t <= o ? n(e) : "";
		};
	}, t.nice = () => n(Ig(n(), {
		floor: (e) => a(Math.floor(i(e))),
		ceil: (e) => a(Math.ceil(i(e)))
	})), t;
}
function Kg() {
	let e = Gg(og()).domain([1, 10]);
	return e.copy = () => ag(e, Kg()).base(e.base()), zm.apply(e, arguments), e;
}
//#endregion
//#region node_modules/d3-scale/src/symlog.js
function qg(e) {
	return function(t) {
		return Math.sign(t) * Math.log1p(Math.abs(t / e));
	};
}
function Jg(e) {
	return function(t) {
		return Math.sign(t) * Math.expm1(Math.abs(t)) * e;
	};
}
function Yg(e) {
	var t = 1, n = e(qg(t), Jg(t));
	return n.constant = function(n) {
		return arguments.length ? e(qg(t = +n), Jg(t)) : t;
	}, Ng(n);
}
function Xg() {
	var e = Yg(og());
	return e.copy = function() {
		return ag(e, Xg()).constant(e.constant());
	}, zm.apply(e, arguments);
}
//#endregion
//#region node_modules/d3-scale/src/pow.js
function Zg(e) {
	return function(t) {
		return t < 0 ? -((-t) ** +e) : t ** +e;
	};
}
function Qg(e) {
	return e < 0 ? -Math.sqrt(-e) : Math.sqrt(e);
}
function $g(e) {
	return e < 0 ? -e * e : e * e;
}
function e_(e) {
	var t = e(eg, eg), n = 1;
	function r() {
		return n === 1 ? e(eg, eg) : n === .5 ? e(Qg, $g) : e(Zg(n), Zg(1 / n));
	}
	return t.exponent = function(e) {
		return arguments.length ? (n = +e, r()) : n;
	}, Ng(t);
}
function t_() {
	var e = e_(og());
	return e.copy = function() {
		return ag(e, t_()).exponent(e.exponent());
	}, zm.apply(e, arguments), e;
}
function n_() {
	return t_.apply(null, arguments).exponent(.5);
}
//#endregion
//#region node_modules/d3-scale/src/radial.js
function r_(e) {
	return Math.sign(e) * e * e;
}
function i_(e) {
	return Math.sign(e) * Math.sqrt(Math.abs(e));
}
function a_() {
	var e = sg(), t = [0, 1], n = !1, r;
	function i(t) {
		var i = i_(e(t));
		return isNaN(i) ? r : n ? Math.round(i) : i;
	}
	return i.invert = function(t) {
		return e.invert(r_(t));
	}, i.domain = function(t) {
		return arguments.length ? (e.domain(t), i) : e.domain();
	}, i.range = function(n) {
		return arguments.length ? (e.range((t = Array.from(n, Qh)).map(r_)), i) : t.slice();
	}, i.rangeRound = function(e) {
		return i.range(e).round(!0);
	}, i.round = function(e) {
		return arguments.length ? (n = !!e, i) : n;
	}, i.clamp = function(t) {
		return arguments.length ? (e.clamp(t), i) : e.clamp();
	}, i.unknown = function(e) {
		return arguments.length ? (r = e, i) : r;
	}, i.copy = function() {
		return a_(e.domain(), t).round(n).clamp(e.clamp()).unknown(r);
	}, zm.apply(i, arguments), Ng(i);
}
//#endregion
//#region node_modules/d3-scale/src/quantile.js
function o_() {
	var e = [], t = [], n = [], r;
	function i() {
		var r = 0, i = Math.max(1, t.length);
		for (n = Array(i - 1); ++r < i;) n[r - 1] = Lm(e, r / i);
		return a;
	}
	function a(e) {
		return e == null || isNaN(e = +e) ? r : t[_m(n, e)];
	}
	return a.invertExtent = function(r) {
		var i = t.indexOf(r);
		return i < 0 ? [NaN, NaN] : [i > 0 ? n[i - 1] : e[0], i < n.length ? n[i] : e[e.length - 1]];
	}, a.domain = function(t) {
		if (!arguments.length) return e.slice();
		e = [];
		for (let n of t) n != null && !isNaN(n = +n) && e.push(n);
		return e.sort(um), i();
	}, a.range = function(e) {
		return arguments.length ? (t = Array.from(e), i()) : t.slice();
	}, a.unknown = function(e) {
		return arguments.length ? (r = e, a) : r;
	}, a.quantiles = function() {
		return n.slice();
	}, a.copy = function() {
		return o_().domain(e).range(t).unknown(r);
	}, zm.apply(a, arguments);
}
//#endregion
//#region node_modules/d3-scale/src/quantize.js
function s_() {
	var e = 0, t = 1, n = 1, r = [.5], i = [0, 1], a;
	function o(e) {
		return e != null && e <= e ? i[_m(r, e, 0, n)] : a;
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
		return s_().domain([e, t]).range(i).unknown(a);
	}, zm.apply(Ng(o), arguments);
}
//#endregion
//#region node_modules/d3-scale/src/threshold.js
function c_() {
	var e = [.5], t = [0, 1], n, r = 1;
	function i(i) {
		return i != null && i <= i ? t[_m(e, i, 0, r)] : n;
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
		return c_().domain(e).range(t).unknown(n);
	}, zm.apply(i, arguments);
}
//#endregion
//#region node_modules/d3-time/src/interval.js
var l_ = /* @__PURE__ */ new Date(), u_ = /* @__PURE__ */ new Date();
function d_(e, t, n, r) {
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
	}, i.filter = (n) => d_((t) => {
		if (t >= t) for (; e(t), !n(t);) t.setTime(t - 1);
	}, (e, r) => {
		if (e >= e) if (r < 0) for (; ++r <= 0;) for (; t(e, -1), !n(e););
		else for (; --r >= 0;) for (; t(e, 1), !n(e););
	}), n && (i.count = (t, r) => (l_.setTime(+t), u_.setTime(+r), e(l_), e(u_), Math.floor(n(l_, u_))), i.every = (e) => (e = Math.floor(e), !isFinite(e) || !(e > 0) ? null : e > 1 ? i.filter(r ? (t) => r(t) % e === 0 : (t) => i.count(0, t) % e === 0) : i)), i;
}
//#endregion
//#region node_modules/d3-time/src/millisecond.js
var f_ = d_(() => {}, (e, t) => {
	e.setTime(+e + t);
}, (e, t) => t - e);
f_.every = (e) => (e = Math.floor(e), !isFinite(e) || !(e > 0) ? null : e > 1 ? d_((t) => {
	t.setTime(Math.floor(t / e) * e);
}, (t, n) => {
	t.setTime(+t + n * e);
}, (t, n) => (n - t) / e) : f_), f_.range;
//#endregion
//#region node_modules/d3-time/src/duration.js
var p_ = 1e3, m_ = p_ * 60, h_ = m_ * 60, g_ = h_ * 24, __ = g_ * 7, v_ = g_ * 30, y_ = g_ * 365, b_ = d_((e) => {
	e.setTime(e - e.getMilliseconds());
}, (e, t) => {
	e.setTime(+e + t * p_);
}, (e, t) => (t - e) / p_, (e) => e.getUTCSeconds());
b_.range;
//#endregion
//#region node_modules/d3-time/src/minute.js
var x_ = d_((e) => {
	e.setTime(e - e.getMilliseconds() - e.getSeconds() * p_);
}, (e, t) => {
	e.setTime(+e + t * m_);
}, (e, t) => (t - e) / m_, (e) => e.getMinutes());
x_.range;
var S_ = d_((e) => {
	e.setUTCSeconds(0, 0);
}, (e, t) => {
	e.setTime(+e + t * m_);
}, (e, t) => (t - e) / m_, (e) => e.getUTCMinutes());
S_.range;
//#endregion
//#region node_modules/d3-time/src/hour.js
var C_ = d_((e) => {
	e.setTime(e - e.getMilliseconds() - e.getSeconds() * p_ - e.getMinutes() * m_);
}, (e, t) => {
	e.setTime(+e + t * h_);
}, (e, t) => (t - e) / h_, (e) => e.getHours());
C_.range;
var w_ = d_((e) => {
	e.setUTCMinutes(0, 0, 0);
}, (e, t) => {
	e.setTime(+e + t * h_);
}, (e, t) => (t - e) / h_, (e) => e.getUTCHours());
w_.range;
//#endregion
//#region node_modules/d3-time/src/day.js
var T_ = d_((e) => e.setHours(0, 0, 0, 0), (e, t) => e.setDate(e.getDate() + t), (e, t) => (t - e - (t.getTimezoneOffset() - e.getTimezoneOffset()) * m_) / g_, (e) => e.getDate() - 1);
T_.range;
var E_ = d_((e) => {
	e.setUTCHours(0, 0, 0, 0);
}, (e, t) => {
	e.setUTCDate(e.getUTCDate() + t);
}, (e, t) => (t - e) / g_, (e) => e.getUTCDate() - 1);
E_.range;
var D_ = d_((e) => {
	e.setUTCHours(0, 0, 0, 0);
}, (e, t) => {
	e.setUTCDate(e.getUTCDate() + t);
}, (e, t) => (t - e) / g_, (e) => Math.floor(e / g_));
D_.range;
//#endregion
//#region node_modules/d3-time/src/week.js
function O_(e) {
	return d_((t) => {
		t.setDate(t.getDate() - (t.getDay() + 7 - e) % 7), t.setHours(0, 0, 0, 0);
	}, (e, t) => {
		e.setDate(e.getDate() + t * 7);
	}, (e, t) => (t - e - (t.getTimezoneOffset() - e.getTimezoneOffset()) * m_) / __);
}
var k_ = O_(0), A_ = O_(1), j_ = O_(2), M_ = O_(3), N_ = O_(4), P_ = O_(5), F_ = O_(6);
k_.range, A_.range, j_.range, M_.range, N_.range, P_.range, F_.range;
function I_(e) {
	return d_((t) => {
		t.setUTCDate(t.getUTCDate() - (t.getUTCDay() + 7 - e) % 7), t.setUTCHours(0, 0, 0, 0);
	}, (e, t) => {
		e.setUTCDate(e.getUTCDate() + t * 7);
	}, (e, t) => (t - e) / __);
}
var L_ = I_(0), R_ = I_(1), z_ = I_(2), B_ = I_(3), V_ = I_(4), H_ = I_(5), U_ = I_(6);
L_.range, R_.range, z_.range, B_.range, V_.range, H_.range, U_.range;
//#endregion
//#region node_modules/d3-time/src/month.js
var W_ = d_((e) => {
	e.setDate(1), e.setHours(0, 0, 0, 0);
}, (e, t) => {
	e.setMonth(e.getMonth() + t);
}, (e, t) => t.getMonth() - e.getMonth() + (t.getFullYear() - e.getFullYear()) * 12, (e) => e.getMonth());
W_.range;
var G_ = d_((e) => {
	e.setUTCDate(1), e.setUTCHours(0, 0, 0, 0);
}, (e, t) => {
	e.setUTCMonth(e.getUTCMonth() + t);
}, (e, t) => t.getUTCMonth() - e.getUTCMonth() + (t.getUTCFullYear() - e.getUTCFullYear()) * 12, (e) => e.getUTCMonth());
G_.range;
//#endregion
//#region node_modules/d3-time/src/year.js
var K_ = d_((e) => {
	e.setMonth(0, 1), e.setHours(0, 0, 0, 0);
}, (e, t) => {
	e.setFullYear(e.getFullYear() + t);
}, (e, t) => t.getFullYear() - e.getFullYear(), (e) => e.getFullYear());
K_.every = (e) => !isFinite(e = Math.floor(e)) || !(e > 0) ? null : d_((t) => {
	t.setFullYear(Math.floor(t.getFullYear() / e) * e), t.setMonth(0, 1), t.setHours(0, 0, 0, 0);
}, (t, n) => {
	t.setFullYear(t.getFullYear() + n * e);
}), K_.range;
var q_ = d_((e) => {
	e.setUTCMonth(0, 1), e.setUTCHours(0, 0, 0, 0);
}, (e, t) => {
	e.setUTCFullYear(e.getUTCFullYear() + t);
}, (e, t) => t.getUTCFullYear() - e.getUTCFullYear(), (e) => e.getUTCFullYear());
q_.every = (e) => !isFinite(e = Math.floor(e)) || !(e > 0) ? null : d_((t) => {
	t.setUTCFullYear(Math.floor(t.getUTCFullYear() / e) * e), t.setUTCMonth(0, 1), t.setUTCHours(0, 0, 0, 0);
}, (t, n) => {
	t.setUTCFullYear(t.getUTCFullYear() + n * e);
}), q_.range;
//#endregion
//#region node_modules/d3-time/src/ticks.js
function J_(e, t, n, r, i, a) {
	let o = [
		[
			b_,
			1,
			p_
		],
		[
			b_,
			5,
			5 * p_
		],
		[
			b_,
			15,
			15 * p_
		],
		[
			b_,
			30,
			30 * p_
		],
		[
			a,
			1,
			m_
		],
		[
			a,
			5,
			5 * m_
		],
		[
			a,
			15,
			15 * m_
		],
		[
			a,
			30,
			30 * m_
		],
		[
			i,
			1,
			h_
		],
		[
			i,
			3,
			3 * h_
		],
		[
			i,
			6,
			6 * h_
		],
		[
			i,
			12,
			12 * h_
		],
		[
			r,
			1,
			g_
		],
		[
			r,
			2,
			2 * g_
		],
		[
			n,
			1,
			__
		],
		[
			t,
			1,
			v_
		],
		[
			t,
			3,
			3 * v_
		],
		[
			e,
			1,
			y_
		]
	];
	function s(e, t, n) {
		let r = t < e;
		r && ([e, t] = [t, e]);
		let i = n && typeof n.range == "function" ? n : c(e, t, n), a = i ? i.range(e, +t + 1) : [];
		return r ? a.reverse() : a;
	}
	function c(t, n, r) {
		let i = Math.abs(n - t) / r, a = fm(([, , e]) => e).right(o, i);
		if (a === o.length) return e.every(jm(t / y_, n / y_, r));
		if (a === 0) return f_.every(Math.max(jm(t, n, r), 1));
		let [s, c] = o[i / o[a - 1][2] < o[a][2] / i ? a - 1 : a];
		return s.every(c);
	}
	return [s, c];
}
var [Y_, X_] = J_(q_, G_, L_, D_, w_, S_), [Z_, Q_] = J_(K_, W_, k_, T_, C_, x_);
//#endregion
//#region node_modules/d3-time-format/src/locale.js
function $_(e) {
	if (0 <= e.y && e.y < 100) {
		var t = new Date(-1, e.m, e.d, e.H, e.M, e.S, e.L);
		return t.setFullYear(e.y), t;
	}
	return new Date(e.y, e.m, e.d, e.H, e.M, e.S, e.L);
}
function ev(e) {
	if (0 <= e.y && e.y < 100) {
		var t = new Date(Date.UTC(-1, e.m, e.d, e.H, e.M, e.S, e.L));
		return t.setUTCFullYear(e.y), t;
	}
	return new Date(Date.UTC(e.y, e.m, e.d, e.H, e.M, e.S, e.L));
}
function tv(e, t, n) {
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
function nv(e) {
	var t = e.dateTime, n = e.date, r = e.time, i = e.periods, a = e.days, o = e.shortDays, s = e.months, c = e.shortMonths, l = cv(i), u = lv(i), d = cv(a), f = lv(a), p = cv(o), m = lv(o), h = cv(s), g = lv(s), _ = cv(c), v = lv(c), y = {
		a: N,
		A: P,
		b: ee,
		B: te,
		c: null,
		d: Av,
		e: Av,
		f: Fv,
		g: Kv,
		G: Jv,
		H: jv,
		I: Mv,
		j: Nv,
		L: Pv,
		m: Iv,
		M: Lv,
		p: ne,
		q: re,
		Q: _y,
		s: vy,
		S: Rv,
		u: zv,
		U: Bv,
		V: Hv,
		w: Uv,
		W: Wv,
		x: null,
		X: null,
		y: Gv,
		Y: qv,
		Z: Yv,
		"%": gy
	}, b = {
		a: ie,
		A: ae,
		b: oe,
		B: se,
		c: null,
		d: Xv,
		e: Xv,
		f: ty,
		g: fy,
		G: my,
		H: Zv,
		I: Qv,
		j: $v,
		L: ey,
		m: ny,
		M: ry,
		p: ce,
		q: le,
		Q: _y,
		s: vy,
		S: iy,
		u: ay,
		U: oy,
		V: cy,
		w: ly,
		W: uy,
		x: null,
		X: null,
		y: dy,
		Y: py,
		Z: hy,
		"%": gy
	}, x = {
		a: E,
		A: D,
		b: O,
		B: k,
		c: A,
		d: bv,
		e: bv,
		f: Ev,
		g: gv,
		G: hv,
		H: Sv,
		I: Sv,
		j: xv,
		L: Tv,
		m: yv,
		M: Cv,
		p: T,
		q: vv,
		Q: Ov,
		s: kv,
		S: wv,
		u: dv,
		U: fv,
		V: pv,
		w: uv,
		W: mv,
		x: j,
		X: M,
		y: gv,
		Y: hv,
		Z: _v,
		"%": Dv
	};
	y.x = S(n, y), y.X = S(r, y), y.c = S(t, y), b.x = S(n, b), b.X = S(r, b), b.c = S(t, b);
	function S(e, t) {
		return function(n) {
			var r = [], i = -1, a = 0, o = e.length, s, c, l;
			for (n instanceof Date || (n = /* @__PURE__ */ new Date(+n)); ++i < o;) e.charCodeAt(i) === 37 && (r.push(e.slice(a, i)), (c = rv[s = e.charAt(++i)]) == null ? c = s === "e" ? " " : "0" : s = e.charAt(++i), (l = t[s]) && (s = l(n, c)), r.push(s), a = i + 1);
			return r.push(e.slice(a, i)), r.join("");
		};
	}
	function C(e, t) {
		return function(n) {
			var r = tv(1900, void 0, 1), i = w(r, e, n += "", 0), a, o;
			if (i != n.length) return null;
			if ("Q" in r) return new Date(r.Q);
			if ("s" in r) return new Date(r.s * 1e3 + ("L" in r ? r.L : 0));
			if (t && !("Z" in r) && (r.Z = 0), "p" in r && (r.H = r.H % 12 + r.p * 12), r.m === void 0 && (r.m = "q" in r ? r.q : 0), "V" in r) {
				if (r.V < 1 || r.V > 53) return null;
				"w" in r || (r.w = 1), "Z" in r ? (a = ev(tv(r.y, 0, 1)), o = a.getUTCDay(), a = o > 4 || o === 0 ? R_.ceil(a) : R_(a), a = E_.offset(a, (r.V - 1) * 7), r.y = a.getUTCFullYear(), r.m = a.getUTCMonth(), r.d = a.getUTCDate() + (r.w + 6) % 7) : (a = $_(tv(r.y, 0, 1)), o = a.getDay(), a = o > 4 || o === 0 ? A_.ceil(a) : A_(a), a = T_.offset(a, (r.V - 1) * 7), r.y = a.getFullYear(), r.m = a.getMonth(), r.d = a.getDate() + (r.w + 6) % 7);
			} else ("W" in r || "U" in r) && ("w" in r || (r.w = "u" in r ? r.u % 7 : +("W" in r)), o = "Z" in r ? ev(tv(r.y, 0, 1)).getUTCDay() : $_(tv(r.y, 0, 1)).getDay(), r.m = 0, r.d = "W" in r ? (r.w + 6) % 7 + r.W * 7 - (o + 5) % 7 : r.w + r.U * 7 - (o + 6) % 7);
			return "Z" in r ? (r.H += r.Z / 100 | 0, r.M += r.Z % 100, ev(r)) : $_(r);
		};
	}
	function w(e, t, n, r) {
		for (var i = 0, a = t.length, o = n.length, s, c; i < a;) {
			if (r >= o) return -1;
			if (s = t.charCodeAt(i++), s === 37) {
				if (s = t.charAt(i++), c = x[s in rv ? t.charAt(i++) : s], !c || (r = c(e, n, r)) < 0) return -1;
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
var rv = {
	"-": "",
	_: " ",
	0: "0"
}, iv = /^\s*\d+/, av = /^%/, ov = /[\\^$*+?|[\]().{}]/g;
function J(e, t, n) {
	var r = e < 0 ? "-" : "", i = (r ? -e : e) + "", a = i.length;
	return r + (a < n ? Array(n - a + 1).join(t) + i : i);
}
function sv(e) {
	return e.replace(ov, "\\$&");
}
function cv(e) {
	return RegExp("^(?:" + e.map(sv).join("|") + ")", "i");
}
function lv(e) {
	return new Map(e.map((e, t) => [e.toLowerCase(), t]));
}
function uv(e, t, n) {
	var r = iv.exec(t.slice(n, n + 1));
	return r ? (e.w = +r[0], n + r[0].length) : -1;
}
function dv(e, t, n) {
	var r = iv.exec(t.slice(n, n + 1));
	return r ? (e.u = +r[0], n + r[0].length) : -1;
}
function fv(e, t, n) {
	var r = iv.exec(t.slice(n, n + 2));
	return r ? (e.U = +r[0], n + r[0].length) : -1;
}
function pv(e, t, n) {
	var r = iv.exec(t.slice(n, n + 2));
	return r ? (e.V = +r[0], n + r[0].length) : -1;
}
function mv(e, t, n) {
	var r = iv.exec(t.slice(n, n + 2));
	return r ? (e.W = +r[0], n + r[0].length) : -1;
}
function hv(e, t, n) {
	var r = iv.exec(t.slice(n, n + 4));
	return r ? (e.y = +r[0], n + r[0].length) : -1;
}
function gv(e, t, n) {
	var r = iv.exec(t.slice(n, n + 2));
	return r ? (e.y = +r[0] + (+r[0] > 68 ? 1900 : 2e3), n + r[0].length) : -1;
}
function _v(e, t, n) {
	var r = /^(Z)|([+-]\d\d)(?::?(\d\d))?/.exec(t.slice(n, n + 6));
	return r ? (e.Z = r[1] ? 0 : -(r[2] + (r[3] || "00")), n + r[0].length) : -1;
}
function vv(e, t, n) {
	var r = iv.exec(t.slice(n, n + 1));
	return r ? (e.q = r[0] * 3 - 3, n + r[0].length) : -1;
}
function yv(e, t, n) {
	var r = iv.exec(t.slice(n, n + 2));
	return r ? (e.m = r[0] - 1, n + r[0].length) : -1;
}
function bv(e, t, n) {
	var r = iv.exec(t.slice(n, n + 2));
	return r ? (e.d = +r[0], n + r[0].length) : -1;
}
function xv(e, t, n) {
	var r = iv.exec(t.slice(n, n + 3));
	return r ? (e.m = 0, e.d = +r[0], n + r[0].length) : -1;
}
function Sv(e, t, n) {
	var r = iv.exec(t.slice(n, n + 2));
	return r ? (e.H = +r[0], n + r[0].length) : -1;
}
function Cv(e, t, n) {
	var r = iv.exec(t.slice(n, n + 2));
	return r ? (e.M = +r[0], n + r[0].length) : -1;
}
function wv(e, t, n) {
	var r = iv.exec(t.slice(n, n + 2));
	return r ? (e.S = +r[0], n + r[0].length) : -1;
}
function Tv(e, t, n) {
	var r = iv.exec(t.slice(n, n + 3));
	return r ? (e.L = +r[0], n + r[0].length) : -1;
}
function Ev(e, t, n) {
	var r = iv.exec(t.slice(n, n + 6));
	return r ? (e.L = Math.floor(r[0] / 1e3), n + r[0].length) : -1;
}
function Dv(e, t, n) {
	var r = av.exec(t.slice(n, n + 1));
	return r ? n + r[0].length : -1;
}
function Ov(e, t, n) {
	var r = iv.exec(t.slice(n));
	return r ? (e.Q = +r[0], n + r[0].length) : -1;
}
function kv(e, t, n) {
	var r = iv.exec(t.slice(n));
	return r ? (e.s = +r[0], n + r[0].length) : -1;
}
function Av(e, t) {
	return J(e.getDate(), t, 2);
}
function jv(e, t) {
	return J(e.getHours(), t, 2);
}
function Mv(e, t) {
	return J(e.getHours() % 12 || 12, t, 2);
}
function Nv(e, t) {
	return J(1 + T_.count(K_(e), e), t, 3);
}
function Pv(e, t) {
	return J(e.getMilliseconds(), t, 3);
}
function Fv(e, t) {
	return Pv(e, t) + "000";
}
function Iv(e, t) {
	return J(e.getMonth() + 1, t, 2);
}
function Lv(e, t) {
	return J(e.getMinutes(), t, 2);
}
function Rv(e, t) {
	return J(e.getSeconds(), t, 2);
}
function zv(e) {
	var t = e.getDay();
	return t === 0 ? 7 : t;
}
function Bv(e, t) {
	return J(k_.count(K_(e) - 1, e), t, 2);
}
function Vv(e) {
	var t = e.getDay();
	return t >= 4 || t === 0 ? N_(e) : N_.ceil(e);
}
function Hv(e, t) {
	return e = Vv(e), J(N_.count(K_(e), e) + (K_(e).getDay() === 4), t, 2);
}
function Uv(e) {
	return e.getDay();
}
function Wv(e, t) {
	return J(A_.count(K_(e) - 1, e), t, 2);
}
function Gv(e, t) {
	return J(e.getFullYear() % 100, t, 2);
}
function Kv(e, t) {
	return e = Vv(e), J(e.getFullYear() % 100, t, 2);
}
function qv(e, t) {
	return J(e.getFullYear() % 1e4, t, 4);
}
function Jv(e, t) {
	var n = e.getDay();
	return e = n >= 4 || n === 0 ? N_(e) : N_.ceil(e), J(e.getFullYear() % 1e4, t, 4);
}
function Yv(e) {
	var t = e.getTimezoneOffset();
	return (t > 0 ? "-" : (t *= -1, "+")) + J(t / 60 | 0, "0", 2) + J(t % 60, "0", 2);
}
function Xv(e, t) {
	return J(e.getUTCDate(), t, 2);
}
function Zv(e, t) {
	return J(e.getUTCHours(), t, 2);
}
function Qv(e, t) {
	return J(e.getUTCHours() % 12 || 12, t, 2);
}
function $v(e, t) {
	return J(1 + E_.count(q_(e), e), t, 3);
}
function ey(e, t) {
	return J(e.getUTCMilliseconds(), t, 3);
}
function ty(e, t) {
	return ey(e, t) + "000";
}
function ny(e, t) {
	return J(e.getUTCMonth() + 1, t, 2);
}
function ry(e, t) {
	return J(e.getUTCMinutes(), t, 2);
}
function iy(e, t) {
	return J(e.getUTCSeconds(), t, 2);
}
function ay(e) {
	var t = e.getUTCDay();
	return t === 0 ? 7 : t;
}
function oy(e, t) {
	return J(L_.count(q_(e) - 1, e), t, 2);
}
function sy(e) {
	var t = e.getUTCDay();
	return t >= 4 || t === 0 ? V_(e) : V_.ceil(e);
}
function cy(e, t) {
	return e = sy(e), J(V_.count(q_(e), e) + (q_(e).getUTCDay() === 4), t, 2);
}
function ly(e) {
	return e.getUTCDay();
}
function uy(e, t) {
	return J(R_.count(q_(e) - 1, e), t, 2);
}
function dy(e, t) {
	return J(e.getUTCFullYear() % 100, t, 2);
}
function fy(e, t) {
	return e = sy(e), J(e.getUTCFullYear() % 100, t, 2);
}
function py(e, t) {
	return J(e.getUTCFullYear() % 1e4, t, 4);
}
function my(e, t) {
	var n = e.getUTCDay();
	return e = n >= 4 || n === 0 ? V_(e) : V_.ceil(e), J(e.getUTCFullYear() % 1e4, t, 4);
}
function hy() {
	return "+0000";
}
function gy() {
	return "%";
}
function _y(e) {
	return +e;
}
function vy(e) {
	return Math.floor(e / 1e3);
}
//#endregion
//#region node_modules/d3-time-format/src/defaultLocale.js
var yy, by, xy;
Sy({
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
function Sy(e) {
	return yy = nv(e), by = yy.format, yy.parse, xy = yy.utcFormat, yy.utcParse, yy;
}
//#endregion
//#region node_modules/d3-scale/src/time.js
function Cy(e) {
	return new Date(e);
}
function wy(e) {
	return e instanceof Date ? +e : +/* @__PURE__ */ new Date(+e);
}
function Ty(e, t, n, r, i, a, o, s, c, l) {
	var u = sg(), d = u.invert, f = u.domain, p = l(".%L"), m = l(":%S"), h = l("%I:%M"), g = l("%I %p"), _ = l("%a %d"), v = l("%b %d"), y = l("%B"), b = l("%Y");
	function x(e) {
		return (c(e) < e ? p : s(e) < e ? m : o(e) < e ? h : a(e) < e ? g : r(e) < e ? i(e) < e ? _ : v : n(e) < e ? y : b)(e);
	}
	return u.invert = function(e) {
		return new Date(d(e));
	}, u.domain = function(e) {
		return arguments.length ? f(Array.from(e, wy)) : f().map(Cy);
	}, u.ticks = function(t) {
		var n = f();
		return e(n[0], n[n.length - 1], t == null ? 10 : t);
	}, u.tickFormat = function(e, t) {
		return t == null ? x : l(t);
	}, u.nice = function(e) {
		var n = f();
		return (!e || typeof e.range != "function") && (e = t(n[0], n[n.length - 1], e == null ? 10 : e)), e ? f(Ig(n, e)) : u;
	}, u.copy = function() {
		return ag(u, Ty(e, t, n, r, i, a, o, s, c, l));
	}, u;
}
function Ey() {
	return zm.apply(Ty(Z_, Q_, K_, W_, k_, T_, C_, x_, b_, by).domain([new Date(2e3, 0, 1), new Date(2e3, 0, 2)]), arguments);
}
//#endregion
//#region node_modules/d3-scale/src/utcTime.js
function Dy() {
	return zm.apply(Ty(Y_, X_, q_, G_, L_, E_, w_, S_, b_, xy).domain([Date.UTC(2e3, 0, 1), Date.UTC(2e3, 0, 2)]), arguments);
}
//#endregion
//#region node_modules/d3-scale/src/sequential.js
function Oy() {
	var e = 0, t = 1, n, r, i, a, o = eg, s = !1, c;
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
	return l.range = u(Jh), l.rangeRound = u(Yh), l.unknown = function(e) {
		return arguments.length ? (c = e, l) : c;
	}, function(o) {
		return a = o, n = o(e), r = o(t), i = n === r ? 0 : 1 / (r - n), l;
	};
}
function ky(e, t) {
	return t.domain(e.domain()).interpolator(e.interpolator()).clamp(e.clamp()).unknown(e.unknown());
}
function Ay() {
	var e = Ng(Oy()(eg));
	return e.copy = function() {
		return ky(e, Ay());
	}, Bm.apply(e, arguments);
}
function jy() {
	var e = Gg(Oy()).domain([1, 10]);
	return e.copy = function() {
		return ky(e, jy()).base(e.base());
	}, Bm.apply(e, arguments);
}
function My() {
	var e = Yg(Oy());
	return e.copy = function() {
		return ky(e, My()).constant(e.constant());
	}, Bm.apply(e, arguments);
}
function Ny() {
	var e = e_(Oy());
	return e.copy = function() {
		return ky(e, Ny()).exponent(e.exponent());
	}, Bm.apply(e, arguments);
}
function Py() {
	return Ny.apply(null, arguments).exponent(.5);
}
//#endregion
//#region node_modules/d3-scale/src/sequentialQuantile.js
function Fy() {
	var e = [], t = eg;
	function n(n) {
		if (n != null && !isNaN(n = +n)) return t((_m(e, n, 1) - 1) / (e.length - 1));
	}
	return n.domain = function(t) {
		if (!arguments.length) return e.slice();
		e = [];
		for (let n of t) n != null && !isNaN(n = +n) && e.push(n);
		return e.sort(um), n;
	}, n.interpolator = function(e) {
		return arguments.length ? (t = e, n) : t;
	}, n.range = function() {
		return e.map((n, r) => t(r / (e.length - 1)));
	}, n.quantiles = function(t) {
		return Array.from({ length: t + 1 }, (n, r) => Im(e, r / t));
	}, n.copy = function() {
		return Fy(t).domain(e);
	}, Bm.apply(n, arguments);
}
//#endregion
//#region node_modules/d3-scale/src/diverging.js
function Iy() {
	var e = 0, t = .5, n = 1, r = 1, i, a, o, s, c, l = eg, u, d = !1, f;
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
			return arguments.length ? ([n, r, i] = t, l = Xh(e, [
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
	return p.range = m(Jh), p.rangeRound = m(Yh), p.unknown = function(e) {
		return arguments.length ? (f = e, p) : f;
	}, function(l) {
		return u = l, i = l(e), a = l(t), o = l(n), s = i === a ? 0 : .5 / (a - i), c = a === o ? 0 : .5 / (o - a), r = a < i ? -1 : 1, p;
	};
}
function Ly() {
	var e = Ng(Iy()(eg));
	return e.copy = function() {
		return ky(e, Ly());
	}, Bm.apply(e, arguments);
}
function Ry() {
	var e = Gg(Iy()).domain([
		.1,
		1,
		10
	]);
	return e.copy = function() {
		return ky(e, Ry()).base(e.base());
	}, Bm.apply(e, arguments);
}
function zy() {
	var e = Yg(Iy());
	return e.copy = function() {
		return ky(e, zy()).constant(e.constant());
	}, Bm.apply(e, arguments);
}
function By() {
	var e = e_(Iy());
	return e.copy = function() {
		return ky(e, By()).exponent(e.exponent());
	}, Bm.apply(e, arguments);
}
function Vy() {
	return By.apply(null, arguments).exponent(.5);
}
//#endregion
//#region node_modules/victory-vendor/es/d3-scale.js
var Hy = /* @__PURE__ */ s({
	scaleBand: () => Um,
	scaleDiverging: () => Ly,
	scaleDivergingLog: () => Ry,
	scaleDivergingPow: () => By,
	scaleDivergingSqrt: () => Vy,
	scaleDivergingSymlog: () => zy,
	scaleIdentity: () => Fg,
	scaleImplicit: () => Vm,
	scaleLinear: () => Pg,
	scaleLog: () => Kg,
	scaleOrdinal: () => Hm,
	scalePoint: () => Gm,
	scalePow: () => t_,
	scaleQuantile: () => o_,
	scaleQuantize: () => s_,
	scaleRadial: () => a_,
	scaleSequential: () => Ay,
	scaleSequentialLog: () => jy,
	scaleSequentialPow: () => Ny,
	scaleSequentialQuantile: () => Fy,
	scaleSequentialSqrt: () => Py,
	scaleSequentialSymlog: () => My,
	scaleSqrt: () => n_,
	scaleSymlog: () => Xg,
	scaleThreshold: () => c_,
	scaleTime: () => Ey,
	scaleUtc: () => Dy,
	tickFormat: () => Mg
});
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineConfiguredScale.js
function Uy(e) {
	var t = Hy;
	if (e in t && typeof t[e] == "function") return t[e]();
	var n = `scale${un(e)}`;
	if (n in t && typeof t[n] == "function") return t[n]();
}
function Wy(e, t, n) {
	if (typeof e == "function") return e.copy().domain(t).range(n);
	if (e != null) {
		var r = Uy(e);
		if (r != null) return r.domain(t).range(n), r;
	}
}
function Gy(e, t, n, r) {
	if (!(n == null || r == null)) return typeof e.scale == "function" ? Wy(e.scale, n, r) : Wy(t, n, r);
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineRealScaleType.js
function Ky(e) {
	return `scale${un(e)}`;
}
function qy(e) {
	return Ky(e) in Hy;
}
var Jy = (e, t, n) => {
	if (e != null) {
		var r = e.scale, i = e.type;
		if (r === "auto") return i === "category" && n && (n.indexOf("LineChart") >= 0 || n.indexOf("AreaChart") >= 0 || n.indexOf("ComposedChart") >= 0 && !t) ? "point" : i === "category" ? "band" : "linear";
		if (typeof r == "string") return qy(r) ? r : "point";
	}
};
//#endregion
//#region node_modules/recharts/es6/util/scale/createCategoricalInverse.js
function Yy(e, t) {
	for (var n = 0, r = e.length, i = e[0] < e[e.length - 1]; n < r;) {
		var a = Math.floor((n + r) / 2);
		(i ? e[a] < t : e[a] > t) ? n = a + 1 : r = a;
	}
	return n;
}
function Xy(e, t) {
	if (e) {
		var n = t == null ? e.domain() : t, r = n.map((t) => {
			var n;
			return (n = e(t)) == null ? 0 : n;
		}), i = e.range();
		if (!(n.length === 0 || i.length < 2)) return (e) => {
			var t, i, a = Yy(r, e);
			if (a <= 0) return n[0];
			if (a >= n.length) return n[n.length - 1];
			var o = (t = r[a - 1]) == null ? 0 : t, s = (i = r[a]) == null ? 0 : i;
			return Math.abs(e - o) <= Math.abs(e - s) ? n[a - 1] : n[a];
		};
	}
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineInverseScaleFunction.js
function Zy(e) {
	if (e != null) return "invert" in e && typeof e.invert == "function" ? e.invert.bind(e) : Xy(e, void 0);
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/axisSelectors.js
function Qy(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function $y(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Qy(Object(n), !0).forEach(function(t) {
			eb(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Qy(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function eb(e, t, n) {
	return (t = tb(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function tb(e) {
	var t = nb(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function nb(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function rb(e, t) {
	return cb(e) || sb(e, t) || ab(e, t) || ib();
}
function ib() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function ab(e, t) {
	if (e) {
		if (typeof e == "string") return ob(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? ob(e, t) : void 0;
	}
}
function ob(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function sb(e, t) {
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
function cb(e) {
	if (Array.isArray(e)) return e;
}
var lb = [0, "auto"], ub = {
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
}, db = (e, t) => e.cartesianAxis.xAxis[t], fb = (e, t) => {
	var n = db(e, t);
	return n == null ? ub : n;
}, pb = {
	allowDataOverflow: !1,
	allowDecimals: !0,
	allowDuplicatedCategory: !0,
	angle: 0,
	dataKey: void 0,
	domain: lb,
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
}, mb = (e, t) => e.cartesianAxis.yAxis[t], hb = (e, t) => {
	var n = mb(e, t);
	return n == null ? pb : n;
}, gb = {
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
}, _b = (e, t) => {
	var n = e.cartesianAxis.zAxis[t];
	return n == null ? gb : n;
}, vb = (e, t, n) => {
	switch (t) {
		case "xAxis": return fb(e, n);
		case "yAxis": return hb(e, n);
		case "zAxis": return _b(e, n);
		case "angleAxis": return Up(e, n);
		case "radiusAxis": return Wp(e, n);
		default: throw Error(`Unexpected axis type: ${t}`);
	}
}, yb = (e, t, n) => {
	switch (t) {
		case "xAxis": return fb(e, n);
		case "yAxis": return hb(e, n);
		default: throw Error(`Unexpected axis type: ${t}`);
	}
}, bb = (e, t, n) => {
	switch (t) {
		case "xAxis": return fb(e, n);
		case "yAxis": return hb(e, n);
		case "angleAxis": return Up(e, n);
		case "radiusAxis": return Wp(e, n);
		default: throw Error(`Unexpected axis type: ${t}`);
	}
}, xb = (e) => e.graphicalItems.cartesianItems.some((e) => e.type === "bar") || e.graphicalItems.polarItems.some((e) => e.type === "radialBar");
function Sb(e, t) {
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
var Cb = (e) => e.graphicalItems.cartesianItems, wb = R([Qp, $p], Sb), Tb = (e, t, n) => e.filter(n).filter((e) => (t == null ? void 0 : t.includeHidden) === !0 || !e.hide), Eb = R([
	Cb,
	vb,
	wb
], Tb, { memoizeOptions: { resultEqualityCheck: im } }), Db = R([Eb], (e) => e.filter((e) => e.type === "area" || e.type === "bar").filter(nm)), Ob = (e) => e.filter((e) => !("stackId" in e) || e.stackId === void 0), kb = R([Eb], Ob), Ab = (e) => e.map((e) => e.data).filter(Boolean).flat(1), jb = R([Eb], (e) => e.some((e) => !e.data)), Mb = R([Eb], Ab, { memoizeOptions: { resultEqualityCheck: im } }), Nb = (e, t) => {
	var n = t.chartData, r = n === void 0 ? [] : n, i = t.dataStartIndex, a = t.dataEndIndex;
	return e.length > 0 ? e : r.slice(i, a + 1);
}, Pb = R([Mb, Kf], Nb), Fb = (e, t, n) => (t == null ? void 0 : t.dataKey) == null ? n.length > 0 ? n.map((e) => e.dataKey).flatMap((t) => e.map((e) => ({ value: js(e, t) }))) : e.map((e) => ({ value: e })) : e.map((e) => ({ value: js(e, t.dataKey) })), Ib = (e, t, n, r, i, a) => {
	var o = r.chartData, s = o === void 0 ? [] : o, c = r.dataStartIndex, l = r.dataEndIndex, u = Fb(e, t, n);
	return i && (t == null ? void 0 : t.dataKey) != null && a.length > 0 ? [...s.slice(c, l + 1).map((e) => ({ value: js(e, t.dataKey) })).filter((e) => e.value != null), ...u] : u;
}, Lb = R([
	Pb,
	vb,
	Eb,
	Kf,
	jb,
	Mb
], Ib);
function Rb(e) {
	if (tn(e) || e instanceof Date) {
		var t = Number(e);
		if (U(t)) return t;
	}
}
function zb(e) {
	if (Array.isArray(e)) {
		var t = [Rb(e[0]), Rb(e[1])];
		return np(t) ? t : void 0;
	}
	var n = Rb(e);
	if (n != null) return [n, n];
}
function Bb(e) {
	return e.map(Rb).filter(dn);
}
function Vb(e, t) {
	var n = Rb(e), r = Rb(t);
	return n == null && r == null ? 0 : n == null ? -1 : r == null ? 1 : n - r;
}
var Hb = R([Lb], (e) => e == null ? void 0 : e.map((e) => e.value).sort(Vb));
function Ub(e, t) {
	switch (e) {
		case "xAxis": return t.direction === "x";
		case "yAxis": return t.direction === "y";
		default: return !1;
	}
}
function Wb(e, t, n) {
	if (!n || !n.length) return [];
	var r;
	if (typeof t == "number" && !$t(t)) r = t;
	else if (Array.isArray(t)) {
		var i = Bb(t);
		i.length > 0 && (r = Math.max(...i));
	}
	return r == null ? [] : Bb(n.flatMap((t) => {
		var n = js(e, t.dataKey), i, a;
		if (Array.isArray(n)) {
			var o = rb(n, 2);
			i = o[0], a = o[1];
		} else i = a = n;
		if (!(!U(i) || !U(a))) return [r - i, r + a];
	}));
}
var Gb = (e) => bb(e, om(e), sm(e)), Kb = R([Gb], (e) => e == null ? void 0 : e.dataKey), qb = R([
	Db,
	Kf,
	Gb
], tm), Jb = (e, t, n, r) => {
	var i = t.reduce((e, t) => {
		if (t.stackId == null) return e;
		var n = e[t.stackId];
		return n == null && (n = []), n.push(t), e[t.stackId] = n, e;
	}, {});
	return Object.fromEntries(Object.entries(i).map((t) => {
		var i = rb(t, 2), a = i[0], o = i[1], s = r ? [...o].reverse() : o;
		return [a, {
			stackedData: Is(e, s.map(em), n),
			graphicalItems: s
		}];
	}));
}, Yb = R([
	qb,
	Db,
	Tp,
	Ep
], Jb), Xb = (e, t, n, r) => {
	var i = t.dataStartIndex, a = t.dataEndIndex;
	if (r == null && n !== "zAxis") return Hs(e, i, a);
}, Zb = R([vb], (e) => e.allowDataOverflow), Qb = (e) => {
	var t;
	if (e == null || !("domain" in e)) return lb;
	if (e.domain != null) return e.domain;
	if ("ticks" in e && e.ticks != null) {
		if (e.type === "number") {
			var n = Bb(e.ticks);
			return [Math.min(...n), Math.max(...n)];
		}
		if (e.type === "category") return e.ticks.map(String);
	}
	return (t = e == null ? void 0 : e.domain) == null ? lb : t;
}, $b = R([vb], Qb), ex = R([$b, Zb], ip), tx = R([
	Yb,
	Wf,
	Qp,
	ex
], Xb, { memoizeOptions: { resultEqualityCheck: rm } }), nx = (e) => e.errorBars, rx = (e, t, n) => e.flatMap((e) => t[e.id]).filter(Boolean).filter((e) => Ub(n, e)), ix = function() {
	var e = [...arguments].filter(Boolean);
	if (e.length !== 0) {
		var t = e.flat();
		return [Math.min(...t), Math.max(...t)];
	}
}, ax = function(e, t, n, r, i) {
	var a = arguments.length > 5 && arguments[5] !== void 0 ? arguments[5] : [], o, s;
	if (n.length > 0 && n.forEach((e) => {
		var n, c = e.data == null ? a : [...e.data], l = (n = r[e.id]) == null ? void 0 : n.filter((e) => Ub(i, e));
		c.forEach((n) => {
			var r, i = js(n, (r = t.dataKey) == null ? e.dataKey : r), a = Wb(n, i, l);
			if (a.length >= 2) {
				var c = Math.min(...a), u = Math.max(...a);
				(o == null || c < o) && (o = c), (s == null || u > s) && (s = u);
			}
			var d = zb(i);
			d != null && (o = o == null ? d[0] : Math.min(o, d[0]), s = s == null ? d[1] : Math.max(s, d[1]));
		});
	}), (t == null ? void 0 : t.dataKey) != null && n.length === 0 && e.forEach((e) => {
		var n = zb(js(e, t.dataKey));
		n != null && (o = o == null ? n[0] : Math.min(o, n[0]), s = s == null ? n[1] : Math.max(s, n[1]));
	}), U(o) && U(s)) return [o, s];
}, ox = R([
	Pb,
	vb,
	kb,
	nx,
	Qp,
	Jf
], ax, { memoizeOptions: { resultEqualityCheck: rm } });
function sx(e) {
	var t = e.value;
	if (tn(t) || t instanceof Date) return t;
}
var cx = (e, t, n) => {
	var r = e.map(sx).filter((e) => e != null);
	return n && (t.dataKey == null || t.allowDuplicatedCategory && on(r)) ? Uf(0, e.length) : t.allowDuplicatedCategory ? r : Array.from(new Set(r));
}, lx = (e) => e.referenceElements.dots, ux = (e, t, n) => e.filter((e) => e.ifOverflow === "extendDomain").filter((e) => t === "xAxis" ? e.xAxisId === n : e.yAxisId === n), dx = R([
	lx,
	Qp,
	$p
], ux), fx = (e) => e.referenceElements.areas, px = R([
	fx,
	Qp,
	$p
], ux), mx = (e) => e.referenceElements.lines, hx = R([
	mx,
	Qp,
	$p
], ux), gx = (e, t) => {
	if (e != null) {
		var n = Bb(e.map((e) => t === "xAxis" ? e.x : e.y));
		if (n.length !== 0) return [Math.min(...n), Math.max(...n)];
	}
}, _x = R(dx, Qp, gx), vx = (e, t) => {
	if (e != null) {
		var n = Bb(e.flatMap((e) => [t === "xAxis" ? e.x1 : e.y1, t === "xAxis" ? e.x2 : e.y2]));
		if (n.length !== 0) return [Math.min(...n), Math.max(...n)];
	}
}, yx = R([px, Qp], vx);
function bx(e) {
	var t;
	if (e.x != null) return Bb([e.x]);
	var n = (t = e.segment) == null ? void 0 : t.map((e) => e.x);
	return n == null || n.length === 0 ? [] : Bb(n);
}
function xx(e) {
	var t;
	if (e.y != null) return Bb([e.y]);
	var n = (t = e.segment) == null ? void 0 : t.map((e) => e.y);
	return n == null || n.length === 0 ? [] : Bb(n);
}
var Sx = (e, t) => {
	if (e != null) {
		var n = e.flatMap((e) => t === "xAxis" ? bx(e) : xx(e));
		if (n.length !== 0) return [Math.min(...n), Math.max(...n)];
	}
}, Cx = R(_x, R([hx, Qp], Sx), yx, (e, t, n) => ix(e, n, t)), wx = (e, t, n, r, i, a, o, s, c) => {
	if (n != null) return n;
	var l = o === "vertical" && s === "xAxis" || o === "horizontal" && s === "yAxis" ? ix(r, a, i) : ix(a, i), u = ap(t, l, e.allowDataOverflow);
	return u == null && e.allowDataOverflow && l == null && c != null ? c : u;
}, Tx = R([
	vb,
	$b,
	ex,
	tx,
	ox,
	Cx,
	K,
	Qp,
	R([vb], (e) => {
		if (!(e == null || e.type !== "number" || !("ticks" in e) || e.ticks == null)) {
			var t = Bb(e.ticks);
			if (t.length !== 0) return [Math.min(...t), Math.max(...t)];
		}
	}, { memoizeOptions: { resultEqualityCheck: rm } })
], wx, { memoizeOptions: { resultEqualityCheck: rm } }), Ex = [0, 1], Dx = (e, t, n, r, i, a, o) => {
	if (!((e == null || n == null || n.length === 0) && o === void 0)) {
		var s = e.dataKey, c = e.type, l = Ns(t, a);
		if (l && s == null) {
			var u;
			return Uf(0, (u = n == null ? void 0 : n.length) == null ? 0 : u);
		}
		return c === "category" ? cx(r, e, l) : i === "expand" && !l ? Ex : o;
	}
}, Ox = R([
	vb,
	K,
	Pb,
	Lb,
	Tp,
	Qp,
	Tx
], Dx), kx = R([
	vb,
	xb,
	Dp
], Jy), Ax = (e, t, n) => {
	var r = t.niceTicks;
	if (r !== "none") {
		var i = Qb(t), a = Array.isArray(i) && (i[0] === "auto" || i[1] === "auto");
		if ((r === "snap125" || r === "adaptive") && t != null && t.tickCount && np(e)) {
			if (a) return yp(e, t.tickCount, t.allowDecimals, r);
			if (t.type === "number") return bp(e, t.tickCount, t.allowDecimals, r);
		}
		if (r === "auto" && n === "linear" && t != null && t.tickCount) {
			if (a && np(e)) return yp(e, t.tickCount, t.allowDecimals, "adaptive");
			if (t.type === "number" && np(e)) return bp(e, t.tickCount, t.allowDecimals, "adaptive");
		}
	}
}, jx = R([
	Ox,
	bb,
	kx
], Ax), Mx = (e, t, n, r) => {
	if (r !== "angleAxis" && (e == null ? void 0 : e.type) === "number" && np(t) && Array.isArray(n) && n.length > 0) {
		var i, a, o = t[0], s = (i = n[0]) == null ? 0 : i, c = t[1], l = (a = n[n.length - 1]) == null ? 0 : a;
		return [Math.min(o, s), Math.max(c, l)];
	}
	return t;
}, Nx = R([
	vb,
	Ox,
	jx,
	Qp
], Mx), Px = R(R(Lb, vb, (e, t) => {
	if (!(!t || t.type !== "number")) {
		var n = Infinity, r = Array.from(Bb(e.map((e) => e.value))).sort((e, t) => e - t), i = r[0], a = r[r.length - 1];
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
}), K, Cp, pc, (e, t, n, r, i) => i, (e, t, n, r, i) => {
	if (!U(e)) return 0;
	var a = t === "vertical" ? r.height : r.width;
	if (i === "gap") return e * a / 2;
	if (i === "no-gap") {
		var o = an(n, e * a), s = e * a / 2;
		return s - o - (s - o) / a * o;
	}
	return 0;
}), Fx = (e, t, n) => {
	var r = fb(e, t);
	return r == null || typeof r.padding != "string" ? 0 : Px(e, "xAxis", t, n, r.padding);
}, Ix = (e, t, n) => {
	var r = hb(e, t);
	return r == null || typeof r.padding != "string" ? 0 : Px(e, "yAxis", t, n, r.padding);
}, Lx = R(fb, Fx, (e, t) => {
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
}), Rx = R(hb, Ix, (e, t) => {
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
}), zx = R([
	pc,
	Lx,
	yc,
	vc,
	(e, t, n) => n
], (e, t, n, r, i) => {
	var a = r.padding;
	return i ? [a.left, n.width - a.right] : [e.left + t.left, e.left + e.width - t.right];
}), Bx = R([
	pc,
	K,
	Rx,
	yc,
	vc,
	(e, t, n) => n
], (e, t, n, r, i, a) => {
	var o = i.padding;
	return a ? [r.height - o.bottom, o.top] : t === "horizontal" ? [e.top + e.height - n.bottom, e.top + n.top] : [e.top + n.top, e.top + e.height - n.bottom];
}), Vx = (e, t, n, r) => {
	var i;
	switch (t) {
		case "xAxis": return zx(e, n, r);
		case "yAxis": return Bx(e, n, r);
		case "zAxis": return (i = _b(e, n)) == null ? void 0 : i.range;
		case "angleAxis": return Yp(e);
		case "radiusAxis": return Xp(e, n);
		default: return;
	}
}, Hx = R([vb, Vx], Pp), Ux = R([
	vb,
	kx,
	R([kx, Nx], lm),
	Hx
], Gy), Wx = (e, t, n, r) => {
	if (!(n == null || n.dataKey == null)) {
		var i = n.type, a = n.scale;
		if (Ns(e, r) && (i === "number" || a !== "auto")) return t.map((e) => e.value);
	}
}, Gx = R([
	K,
	Lb,
	bb,
	Qp
], Wx), Kx = R([Ux], cm);
R([Ux], Zy), R([Ux, Hb], Xy), R([
	Eb,
	nx,
	Qp
], rx);
function qx(e, t) {
	return e.id < t.id ? -1 : +(e.id > t.id);
}
var Jx = (e, t) => t, Yx = (e, t, n) => n, Xx = R(ec, Jx, Yx, (e, t, n) => e.filter((e) => e.orientation === t).filter((e) => e.mirror === n).sort(qx)), Zx = R(tc, Jx, Yx, (e, t, n) => e.filter((e) => e.orientation === t).filter((e) => e.mirror === n).sort(qx)), Qx = (e, t) => ({
	width: e.width,
	height: t.height
}), $x = (e, t) => ({
	width: typeof t.width == "number" ? t.width : 60,
	height: e.height
}), eS = R(pc, fb, Qx), tS = (e, t, n) => {
	switch (t) {
		case "top": return e.top;
		case "bottom": return n - e.bottom;
		default: return 0;
	}
}, nS = (e, t, n) => {
	switch (t) {
		case "left": return e.left;
		case "right": return n - e.right;
		default: return 0;
	}
}, rS = R(Zs, pc, Xx, Jx, Yx, (e, t, n, r, i) => {
	var a = {}, o;
	return n.forEach((n) => {
		var s = Qx(t, n);
		o == null && (o = tS(t, r, e));
		var c = r === "top" && !i || r === "bottom" && i;
		a[n.id] = o - Number(c) * s.height, o += (c ? -1 : 1) * s.height;
	}), a;
}), iS = R(Xs, pc, Zx, Jx, Yx, (e, t, n, r, i) => {
	var a = {}, o;
	return n.forEach((n) => {
		var s = $x(t, n);
		o == null && (o = nS(t, r, e));
		var c = r === "left" && !i || r === "right" && i;
		a[n.id] = o - Number(c) * s.width, o += (c ? -1 : 1) * s.width;
	}), a;
}), aS = R([
	pc,
	fb,
	(e, t) => {
		var n = fb(e, t);
		if (n != null) return rS(e, n.orientation, n.mirror);
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
}), oS = R([
	pc,
	hb,
	(e, t) => {
		var n = hb(e, t);
		if (n != null) return iS(e, n.orientation, n.mirror);
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
}), sS = R(pc, hb, (e, t) => ({
	width: typeof t.width == "number" ? t.width : 60,
	height: e.height
})), cS = (e, t, n) => {
	switch (t) {
		case "xAxis": return eS(e, n).width;
		case "yAxis": return sS(e, n).height;
		default: return;
	}
}, lS = (e, t, n, r) => {
	if (n != null) {
		var i = n.allowDuplicatedCategory, a = n.type, o = n.dataKey, s = Ns(e, r), c = t.map((e) => e.value), l = c.filter((e) => e != null);
		if (o && s && a === "category" && i && on(l)) return c;
	}
}, uS = R([
	K,
	Lb,
	vb,
	Qp
], lS);
R([
	K,
	yb,
	kx,
	Kx,
	uS,
	Gx,
	Vx,
	jx,
	Qp
], (e, t, n, r, i, a, o, s, c) => {
	if (t != null) {
		var l = Ns(e, c);
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
var dS = R([
	K,
	bb,
	kx,
	Kx,
	jx,
	Vx,
	uS,
	Gx,
	Qp
], (e, t, n, r, i, a, o, s, c) => {
	if (!(t == null || r == null)) {
		var l = Ns(e, c), u = t.type, d = t.ticks, f = t.tickCount, p = n === "scaleBand" && typeof r.bandwidth == "function" ? r.bandwidth() / 2 : 2, m = u === "category" && r.bandwidth ? r.bandwidth() / p : 0;
		m = c === "angleAxis" && a != null && a.length >= 2 ? Qt(a[0] - a[1]) * 2 * m : m;
		var h = d || i;
		return h ? h.map((e, t) => {
			var n = o ? o.indexOf(e) : e, i = r.map(n);
			return U(i) ? {
				index: t,
				coordinate: i + m,
				value: e,
				offset: m
			} : null;
		}).filter(dn) : l && s ? s.map((e, t) => {
			var n = r.map(e);
			return U(n) ? {
				coordinate: n + m,
				value: e,
				index: t,
				offset: m
			} : null;
		}).filter(dn) : r.ticks ? r.ticks(f).map((e, t) => {
			var n = r.map(e);
			return U(n) ? {
				coordinate: n + m,
				value: e,
				index: t,
				offset: m
			} : null;
		}).filter(dn) : r.domain().map((e, t) => {
			var n = r.map(e);
			return U(n) ? {
				coordinate: n + m,
				value: o ? o[e] : e,
				index: t,
				offset: m
			} : null;
		}).filter(dn);
	}
}), fS = R([
	K,
	bb,
	Kx,
	Vx,
	uS,
	Gx,
	Qp
], (e, t, n, r, i, a, o) => {
	if (!(t == null || n == null || r == null || r[0] === r[1])) {
		var s = Ns(e, o), c = t.tickCount, l = 0;
		return l = o === "angleAxis" && (r == null ? void 0 : r.length) >= 2 ? Qt(r[0] - r[1]) * 2 * l : l, s && a ? a.map((e, t) => {
			var r = n.map(e);
			return U(r) ? {
				coordinate: r + l,
				value: e,
				index: t,
				offset: l
			} : null;
		}).filter(dn) : n.ticks ? n.ticks(c).map((e, t) => {
			var r = n.map(e);
			return U(r) ? {
				coordinate: r + l,
				value: e,
				index: t,
				offset: l
			} : null;
		}).filter(dn) : n.domain().map((e, t) => {
			var r = n.map(e);
			return U(r) ? {
				coordinate: r + l,
				value: i ? i[e] : e,
				index: t,
				offset: l
			} : null;
		}).filter(dn);
	}
}), pS = R(vb, Kx, (e, t) => {
	if (!(e == null || t == null)) return $y($y({}, e), {}, { scale: t });
});
R((e, t, n) => _b(e, n), R([R([
	vb,
	kx,
	Ox,
	Hx
], Gy)], cm), (e, t) => {
	if (!(e == null || t == null)) return $y($y({}, e), {}, { scale: t });
});
var mS = R([
	K,
	ec,
	tc
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
var hS = (e) => e.options.defaultTooltipEventType, gS = (e) => e.options.validateTooltipEventTypes;
function _S(e, t, n) {
	if (e == null) return t;
	var r = e ? "axis" : "item";
	return n == null ? t : n.includes(r) ? r : t;
}
function vS(e, t) {
	return _S(t, hS(e), gS(e));
}
function yS(e) {
	return L((t) => vS(t, e));
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineActiveLabel.js
var bS = (e, t) => {
	var n, r = Number(t);
	if (!($t(r) || t == null)) return r >= 0 ? e == null || (n = e[r]) == null ? void 0 : n.value : void 0;
}, xS = (e) => e.tooltip.settings, SS = {
	active: !1,
	index: null,
	dataKey: void 0,
	graphicalItemId: void 0,
	coordinate: void 0
}, CS = H({
	name: "tooltip",
	initialState: {
		itemInteraction: {
			click: SS,
			hover: SS
		},
		axisInteraction: {
			click: SS,
			hover: SS
		},
		keyboardInteraction: SS,
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
				e.tooltipItemPayloads.push(B(t.payload));
			},
			prepare: V()
		},
		replaceTooltipEntrySettings: {
			reducer(e, t) {
				var n = t.payload, r = n.prev, i = n.next, a = to(e).tooltipItemPayloads.indexOf(B(r));
				a > -1 && (e.tooltipItemPayloads[a] = B(i));
			},
			prepare: V()
		},
		removeTooltipEntrySettings: {
			reducer(e, t) {
				var n = to(e).tooltipItemPayloads.indexOf(B(t.payload));
				n > -1 && e.tooltipItemPayloads.splice(n, 1);
			},
			prepare: V()
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
}), wS = CS.actions, TS = wS.addTooltipEntrySettings, ES = wS.replaceTooltipEntrySettings, DS = wS.removeTooltipEntrySettings, OS = wS.setTooltipSettingsState, kS = wS.setActiveMouseOverItemIndex, AS = wS.mouseLeaveItem, jS = wS.mouseLeaveChart, MS = wS.setActiveClickItemIndex, NS = wS.setMouseOverAxisIndex, PS = wS.setMouseClickAxisIndex, FS = wS.setSyncInteraction, IS = wS.setKeyboardInteraction, LS = CS.reducer;
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineTooltipInteractionState.js
function RS(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function zS(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? RS(Object(n), !0).forEach(function(t) {
			BS(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : RS(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function BS(e, t, n) {
	return (t = VS(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function VS(e) {
	var t = HS(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function HS(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function US(e, t, n) {
	return t === "axis" ? n === "click" ? e.axisInteraction.click : e.axisInteraction.hover : n === "click" ? e.itemInteraction.click : e.itemInteraction.hover;
}
function WS(e) {
	return e.index != null;
}
var GS = (e, t, n, r) => {
	if (t == null) return SS;
	var i = US(e, t, n);
	if (i == null) return SS;
	if (i.active) return i;
	if (e.keyboardInteraction.active) return e.keyboardInteraction;
	if (e.syncInteraction.active && e.syncInteraction.index != null) return e.syncInteraction;
	var a = e.settings.active === !0;
	if (WS(i)) {
		if (a) return zS(zS({}, i), {}, { active: !0 });
	} else if (r != null) return {
		active: !0,
		coordinate: void 0,
		dataKey: void 0,
		index: r,
		graphicalItemId: void 0
	};
	return zS(zS({}, SS), {}, { coordinate: i.coordinate });
};
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineActiveTooltipIndex.js
function KS(e) {
	if (typeof e == "number") return Number.isFinite(e) ? e : void 0;
	if (e instanceof Date) {
		var t = e.valueOf();
		return Number.isFinite(t) ? t : void 0;
	}
	var n = Number(e);
	return Number.isFinite(n) ? n : void 0;
}
function qS(e, t) {
	var n = KS(e), r = t[0], i = t[1];
	return n !== void 0 && n >= Math.min(r, i) && n <= Math.max(r, i);
}
function JS(e, t, n) {
	if (n == null || t == null) return !0;
	var r = js(e, t);
	return r == null || !np(n) || qS(r, n);
}
var YS = (e, t, n, r) => {
	var i = e == null ? void 0 : e.index;
	if (i == null) return null;
	var a = Number(i);
	if (!U(a)) return i;
	var o = 0, s = Infinity;
	t.length > 0 && (s = t.length - 1);
	var c = Math.max(o, Math.min(a, s)), l = t[c];
	return l == null || JS(l, n, r) ? String(c) : null;
}, XS = (e, t, n, r, i, a, o) => {
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
}, ZS = (e, t, n, r) => {
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
}, QS = (e) => e.options.tooltipPayloadSearcher, $S = (e) => e.tooltip;
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineTooltipPayload.js
function eC(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function tC(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? eC(Object(n), !0).forEach(function(t) {
			nC(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : eC(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function nC(e, t, n) {
	return (t = rC(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function rC(e) {
	var t = iC(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function iC(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function aC(e) {
	if (typeof e == "string" || typeof e == "number") return e;
}
function oC(e) {
	if (typeof e == "string" || typeof e == "number" || typeof e == "boolean") return e;
}
function sC(e) {
	if (typeof e == "string" || typeof e == "number") return e;
	if (typeof e == "function") return (t) => e(t);
}
function cC(e) {
	if (typeof e == "string") return e;
}
function lC(e) {
	if (!(typeof e != "object" || !e)) return {
		name: "name" in e ? aC(e.name) : void 0,
		unit: "unit" in e ? oC(e.unit) : void 0,
		dataKey: "dataKey" in e ? sC(e.dataKey) : void 0,
		payload: "payload" in e ? e.payload : void 0,
		color: "color" in e ? cC(e.color) : void 0,
		fill: "fill" in e ? cC(e.fill) : void 0
	};
}
function uC(e, t) {
	return e == null ? t : e;
}
var dC = (e, t, n, r, i, a, o) => {
	if (!(t == null || a == null)) {
		var s = n.chartData, c = n.computedData, l = n.dataStartIndex, u = n.dataEndIndex;
		return e.reduce((e, n) => {
			var d, f = n.dataDefinedOnItem, p = n.settings, m = uC(f, s), h = Array.isArray(m) ? ws(m, l, u) : m, g = (d = p == null ? void 0 : p.dataKey) == null ? r : d, _ = p == null ? void 0 : p.nameKey, v = r && Array.isArray(h) && !Array.isArray(h[0]) && o === "axis" ? cn(h, r, i) : a(h, t, c, _);
			if (Array.isArray(v)) v.forEach((t) => {
				var n, r, i = lC(t), a = i == null ? void 0 : i.name, o = i == null ? void 0 : i.dataKey, s = i == null ? void 0 : i.payload, c = tC(tC({}, p), {}, {
					name: a,
					unit: i == null ? void 0 : i.unit,
					color: (n = i == null ? void 0 : i.color) == null ? p == null ? void 0 : p.color : n,
					fill: (r = i == null ? void 0 : i.fill) == null ? p == null ? void 0 : p.fill : r
				});
				e.push(Ks({
					tooltipEntrySettings: c,
					dataKey: o,
					payload: s,
					value: js(s, o),
					name: a == null ? void 0 : String(a)
				}));
			});
			else {
				var y;
				e.push(Ks({
					tooltipEntrySettings: p,
					dataKey: g,
					payload: v,
					value: js(v, g),
					name: (y = js(v, _)) == null ? p == null ? void 0 : p.name : y
				}));
			}
			return e;
		}, []);
	}
}, fC = R([
	Gb,
	xb,
	Dp
], Jy), pC = R([
	R([(e) => e.graphicalItems.cartesianItems, (e) => e.graphicalItems.polarItems], (e, t) => [...e, ...t]),
	Gb,
	R([om, sm], Sb)
], Tb, { memoizeOptions: { resultEqualityCheck: im } }), mC = R([pC], (e) => e.filter(nm)), hC = R([pC], Ab, { memoizeOptions: { resultEqualityCheck: im } }), gC = R([pC], (e) => e.some((e) => !e.data)), _C = R([hC, Wf], Nb), vC = R([
	mC,
	Wf,
	Gb
], tm), yC = R([
	_C,
	Gb,
	pC,
	Wf,
	gC,
	hC
], Ib), bC = R([Gb], Qb), xC = R([bC, R([Gb], (e) => e.allowDataOverflow)], ip), SC = R([
	R([
		vC,
		R([pC], (e) => e.filter(nm)),
		Tp,
		Ep
	], Jb),
	Wf,
	om,
	xC
], Xb), CC = R([
	_C,
	Gb,
	R([pC], Ob),
	nx,
	om,
	Yf
], ax, { memoizeOptions: { resultEqualityCheck: rm } }), wC = R([R([
	lx,
	om,
	sm
], ux), om], gx), TC = R([R([
	fx,
	om,
	sm
], ux), om], vx), EC = R([
	Gb,
	K,
	_C,
	yC,
	Tp,
	om,
	R([
		Gb,
		bC,
		xC,
		SC,
		CC,
		R([
			wC,
			R([R([
				mx,
				om,
				sm
			], ux), om], Sx),
			TC
		], ix),
		K,
		om
	], wx)
], Dx), DC = R([
	Gb,
	EC,
	R([
		EC,
		Gb,
		fC
	], Ax),
	om
], Mx), OC = (e) => Vx(e, om(e), sm(e), !1), kC = R([Gb, OC], Pp), AC = R([R([
	Gb,
	fC,
	DC,
	kC
], Gy)], cm), jC = R([
	K,
	Gb,
	fC,
	AC,
	OC,
	R([
		K,
		yC,
		Gb,
		om
	], lS),
	R([
		K,
		yC,
		Gb,
		om
	], Wx),
	om
], (e, t, n, r, i, a, o, s) => {
	if (t) {
		var c = t.type, l = Ns(e, s);
		if (r) {
			var u = n === "scaleBand" && r.bandwidth ? r.bandwidth() / 2 : 2, d = c === "category" && r.bandwidth ? r.bandwidth() / u : 0;
			return d = s === "angleAxis" && i != null && (i == null ? void 0 : i.length) >= 2 ? Qt(i[0] - i[1]) * 2 * d : d, l && o ? o.map((e, t) => {
				var n = r.map(e);
				return U(n) ? {
					coordinate: n + d,
					value: e,
					index: t,
					offset: d
				} : null;
			}).filter(dn) : r.domain().map((e, t) => {
				var n = r.map(e);
				return U(n) ? {
					coordinate: n + d,
					value: a ? a[e] : e,
					index: t,
					offset: d
				} : null;
			}).filter(dn);
		}
	}
}), MC = R([
	hS,
	gS,
	xS
], (e, t, n) => _S(n.shared, e, t)), NC = (e) => e.tooltip.settings.trigger, PC = (e) => e.tooltip.settings.defaultIndex, FC = R([
	$S,
	MC,
	NC,
	PC
], GS), IC = R([
	FC,
	_C,
	Kb,
	EC
], YS), LC = R([jC, IC], bS), RC = R([FC], (e) => {
	if (e) return e.dataKey;
}), zC = R([FC], (e) => {
	if (e) return e.graphicalItemId;
}), BC = R([
	$S,
	MC,
	NC,
	PC
], ZS), VC = R([FC, R([
	Xs,
	Zs,
	K,
	pc,
	jC,
	PC,
	BC
], XS)], (e, t) => e != null && e.coordinate ? e.coordinate : t), HC = R([FC], (e) => {
	var t;
	return (t = e == null ? void 0 : e.active) != null && t;
});
R([R([
	BC,
	IC,
	Wf,
	Kb,
	LC,
	QS,
	MC
], dC)], (e) => {
	if (e != null) {
		var t = e.map((e) => e.payload).filter((e) => e != null);
		return Array.from(new Set(t));
	}
});
//#endregion
//#region node_modules/recharts/es6/context/useTooltipAxis.js
function UC(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function WC(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? UC(Object(n), !0).forEach(function(t) {
			GC(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : UC(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function GC(e, t, n) {
	return (t = KC(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function KC(e) {
	var t = qC(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function qC(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var JC = () => L(Gb), YC = () => {
	var e = JC(), t = L(jC), n = L(AC);
	return Gs(!e || !n ? void 0 : WC(WC({}, e), {}, { scale: n }), t);
};
//#endregion
//#region node_modules/recharts/es6/util/getActiveCoordinate.js
function XC(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function ZC(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? XC(Object(n), !0).forEach(function(t) {
			QC(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : XC(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function QC(e, t, n) {
	return (t = $C(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function $C(e) {
	var t = ew(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function ew(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var tw = (e, t, n, r) => {
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
}, nw = (e, t, n, r) => {
	var i = t.find((e) => e && e.index === n);
	if (i) {
		if (e === "centric") {
			var a = i.coordinate, o = r.radius;
			return ZC(ZC(ZC({}, r), _f(r.cx, r.cy, o, a)), {}, {
				angle: a,
				radius: o
			});
		}
		var s = i.coordinate, c = r.angle;
		return ZC(ZC(ZC({}, r), _f(r.cx, r.cy, s, c)), {}, {
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
function rw(e, t) {
	var n = e.relativeX, r = e.relativeY;
	return n >= t.left && n <= t.left + t.width && r >= t.top && r <= t.top + t.height;
}
var iw = (e, t, n, r, i) => {
	var a, o = (a = t == null ? void 0 : t.length) == null ? 0 : a;
	if (o <= 1 || e == null) return 0;
	if (r === "angleAxis" && i != null && Math.abs(Math.abs(i[1] - i[0]) - 360) <= 1e-6) for (var s = 0; s < o; s++) {
		var c, l, u, d, f, p = s > 0 ? (c = n[s - 1]) == null ? void 0 : c.coordinate : (l = n[o - 1]) == null ? void 0 : l.coordinate, m = (u = n[s]) == null ? void 0 : u.coordinate, h = s >= o - 1 ? (d = n[0]) == null ? void 0 : d.coordinate : (f = n[s + 1]) == null ? void 0 : f.coordinate, g = void 0;
		if (!(p == null || m == null || h == null)) if (Qt(m - p) !== Qt(h - m)) {
			var _ = [];
			if (Qt(h - m) === Qt(i[1] - i[0])) {
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
}, aw = () => L(Dp), ow = (e, t) => t, sw = (e, t, n) => n, cw = (e, t, n, r) => r, lw = R(jC, (e) => pi(e, (e) => e.coordinate)), uw = R([
	$S,
	ow,
	sw,
	cw
], GS), dw = R([
	uw,
	_C,
	Kb,
	EC
], YS), fw = (e, t, n) => {
	if (t != null) {
		var r = $S(e);
		return t === "axis" ? n === "hover" ? r.axisInteraction.hover.dataKey : r.axisInteraction.click.dataKey : n === "hover" ? r.itemInteraction.hover.dataKey : r.itemInteraction.click.dataKey;
	}
}, pw = R([
	$S,
	ow,
	sw,
	cw
], ZS), mw = R([
	Xs,
	Zs,
	K,
	pc,
	jC,
	cw,
	pw
], XS), hw = R([uw, mw], (e, t) => {
	var n;
	return (n = e.coordinate) == null ? t : n;
}), gw = R([jC, dw], bS), _w = R([
	pw,
	dw,
	Wf,
	Kb,
	gw,
	QS,
	ow
], dC), vw = R([uw, dw], (e, t) => ({
	isActive: e.active && t != null,
	activeIndex: t
})), yw = (e, t, n, r, i, a, o) => {
	if (!(!e || !n || !r || !i) && rw(e, o)) {
		var s = iw(Js(e, t), a, i, n, r), c = tw(t, i, s, e);
		return {
			activeIndex: String(s),
			activeCoordinate: c
		};
	}
}, bw = (e, t, n, r, i, a, o) => {
	if (!(!e || !r || !i || !a || !n)) {
		var s = Cf(e, n);
		if (s) {
			var c = iw(Ys(s, t), o, a, r, i), l = nw(t, a, c, s);
			return {
				activeIndex: String(c),
				activeCoordinate: l
			};
		}
	}
}, xw = (e, t, n, r, i, a, o, s) => {
	if (!(!e || !t || !r || !i || !a)) return t === "horizontal" || t === "vertical" ? yw(e, t, r, i, a, o, s) : bw(e, t, n, r, i, a, o);
}, Sw = R((e) => e.zIndex.zIndexMap, (e, t) => t, (e, t, n) => n, (e, t, n) => {
	if (t != null) {
		var r = e[t];
		if (r != null) return n ? r.panoramaElement : r.element;
	}
}), Cw = R((e) => e.zIndex.zIndexMap, (e) => {
	var t = Object.keys(e).map((e) => parseInt(e, 10)).concat(Object.values(jp));
	return Array.from(new Set(t)).sort((e, t) => e - t);
}, { memoizeOptions: { resultEqualityCheck: am } });
//#endregion
//#region node_modules/recharts/es6/state/zIndexSlice.js
function ww(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Tw(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? ww(Object(n), !0).forEach(function(t) {
			Ew(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : ww(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Ew(e, t, n) {
	return (t = Dw(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function Dw(e) {
	var t = Ow(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Ow(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var kw = { zIndexMap: Object.values(jp).reduce((e, t) => Tw(Tw({}, e), {}, { [t]: {
	element: void 0,
	panoramaElement: void 0,
	consumers: 0
} }), {}) }, Aw = new Set(Object.values(jp));
function jw(e) {
	return Aw.has(e);
}
var Mw = H({
	name: "zIndex",
	initialState: kw,
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
			prepare: V()
		},
		unregisterZIndexPortal: {
			reducer: (e, t) => {
				var n = t.payload.zIndex;
				e.zIndexMap[n] && (--e.zIndexMap[n].consumers, e.zIndexMap[n].consumers <= 0 && !jw(n) && delete e.zIndexMap[n]);
			},
			prepare: V()
		},
		registerZIndexPortalElement: {
			reducer: (e, t) => {
				var n = t.payload, r = n.zIndex, i = n.element, a = n.isPanorama;
				e.zIndexMap[r] ? a ? e.zIndexMap[r].panoramaElement = B(i) : e.zIndexMap[r].element = B(i) : e.zIndexMap[r] = {
					consumers: 0,
					element: a ? void 0 : B(i),
					panoramaElement: a ? B(i) : void 0
				};
			},
			prepare: V()
		},
		unregisterZIndexPortalElement: {
			reducer: (e, t) => {
				var n = t.payload.zIndex;
				e.zIndexMap[n] && (t.payload.isPanorama ? e.zIndexMap[n].panoramaElement = void 0 : e.zIndexMap[n].element = void 0);
			},
			prepare: V()
		}
	}
}), Nw = Mw.actions, Pw = Nw.registerZIndexPortal, Fw = Nw.unregisterZIndexPortal, Iw = Nw.registerZIndexPortalElement, Lw = Nw.unregisterZIndexPortalElement, Rw = Mw.reducer, zw = h();
function Bw(e) {
	var t = e.zIndex, n = e.children, r = ol() && t !== void 0 && t !== 0, i = _c(), a = (0, C.useRef)(void 0), o = (0, C.useRef)(/* @__PURE__ */ new Set()), s = Lr(), c = L((e) => Sw(e, t, i));
	if ((0, C.useLayoutEffect)(() => {
		if (!r) {
			var e = o.current;
			e.forEach((e) => {
				s(Fw({ zIndex: e }));
			}), e.clear(), a.current = void 0;
			return;
		}
		if (o.current.has(t) || (s(Pw({ zIndex: t })), o.current.add(t)), c) {
			a.current = c;
			var n = o.current;
			n.forEach((e) => {
				e !== t && (s(Fw({ zIndex: e })), n.delete(e));
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
				s(Fw({ zIndex: e }));
			}), e.clear();
		};
	}, [s]), !r) return n;
	var l = c == null ? a.current : c;
	return l ? /*#__PURE__*/ (0, zw.createPortal)(n, l) : null;
}
//#endregion
//#region node_modules/recharts/es6/component/Cursor.js
function Vw() {
	return Vw = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, Vw.apply(null, arguments);
}
function Hw(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Uw(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Hw(Object(n), !0).forEach(function(t) {
			Ww(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Hw(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Ww(e, t, n) {
	return (t = Gw(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function Gw(e) {
	var t = Kw(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Kw(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function qw(e) {
	var t = e.cursor, n = e.cursorComp, r = e.cursorProps;
	return /*#__PURE__*/ (0, C.isValidElement)(t) ? /*#__PURE__*/ (0, C.cloneElement)(t, r) : /*#__PURE__*/ (0, C.createElement)(n, r);
}
function Jw(e) {
	var t, n = e.coordinate, r = e.payload, i = e.index, a = e.offset, o = e.tooltipAxisBandSize, s = e.layout, c = e.cursor, l = e.tooltipEventType, u = e.chartName, d = n, f = r, p = i;
	if (!c || !d || u !== "ScatterChart" && l !== "axis") return null;
	var m, h, g;
	if (u === "ScatterChart") m = d, h = Yu, g = jp.cursorLine;
	else if (u === "BarChart") m = Xu(s, d, a, o), h = lf, g = jp.cursorRectangle;
	else if (s === "radial" && pn(d)) {
		var _ = wf(d), v = _.cx, y = _.cy, b = _.radius;
		m = {
			cx: v,
			cy: y,
			startAngle: _.startAngle,
			endAngle: _.endAngle,
			innerRadius: b,
			outerRadius: b
		}, h = zf, g = jp.cursorLine;
	} else m = { points: Bf(s, d, a) }, h = Ru, g = jp.cursorLine;
	var x = typeof c == "object" && "className" in c ? c.className : void 0, S = Uw(Uw(Uw(Uw({
		stroke: "#ccc",
		pointerEvents: "none"
	}, a), m), Ae(c)), {}, {
		payload: f,
		payloadIndex: p,
		className: Ce("recharts-tooltip-cursor", x)
	});
	return /*#__PURE__*/ C.createElement(Bw, { zIndex: (t = e.zIndex) == null ? g : t }, /*#__PURE__*/ C.createElement(qw, {
		cursor: c,
		cursorComp: h,
		cursorProps: S
	}));
}
function Yw(e) {
	var t = YC(), n = el(), r = rl(), i = aw();
	return t == null || n == null || r == null || i == null ? null : /*#__PURE__*/ C.createElement(Jw, Vw({}, e, {
		offset: n,
		layout: r,
		tooltipAxisBandSize: t,
		chartName: i
	}));
}
//#endregion
//#region node_modules/recharts/es6/context/tooltipPortalContext.js
var Xw = /*#__PURE__*/ (0, C.createContext)(null), Zw = () => (0, C.useContext)(Xw), Qw = (/* @__PURE__ */ l((/* @__PURE__ */ o(((e, t) => {
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
})))(), 1)).default, $w = new Qw(), eT = "recharts.syncEvent.tooltip", tT = "recharts.syncEvent.brush", nT = (e, t) => {
	if (t && Array.isArray(e)) {
		var n = Number.parseInt(t, 10);
		if (!$t(n)) return e[n];
	}
}, rT = H({
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
}), iT = rT.reducer, aT = rT.actions.createEventEmitter;
//#endregion
//#region node_modules/recharts/es6/synchronisation/syncSelectors.js
function oT(e) {
	return e.tooltip.syncInteraction;
}
var sT = H({
	name: "chartData",
	initialState: {
		chartData: void 0,
		computedData: void 0,
		dataStartIndex: 0,
		dataEndIndex: 0
	},
	reducers: {
		setChartData(e, t) {
			if (e.chartData = B(t.payload), t.payload == null) {
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
}), cT = sT.actions, lT = cT.setChartData, uT = cT.setDataStartEndIndexes;
cT.setComputedData;
var dT = sT.reducer, fT = ["x", "y"];
function pT(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function mT(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? pT(Object(n), !0).forEach(function(t) {
			hT(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : pT(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function hT(e, t, n) {
	return (t = gT(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function gT(e) {
	var t = _T(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function _T(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function vT(e, t) {
	if (e == null) return {};
	var n, r, i = yT(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function yT(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function bT() {
	var e = L(Op), t = L(Ap), n = Lr(), r = L(kp), i = L(jC), a = rl(), o = Qc();
	(0, C.useEffect)(() => {
		if (e == null) return fn;
		var s = (s, c, l) => {
			if (t !== l && e === s) {
				if (c.payload.active === !1) {
					n(FS({
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
						var d = c.payload.coordinate, f = d.x, p = d.y, m = vT(d, fT), h = c.payload.sourceViewBox, g = h.x, _ = h.y, v = h.width, y = h.height, b = mT(mT({}, m), {}, {
							x: o.x + (v ? (f - g) / v : 0) * o.width,
							y: o.y + (y ? (p - _) / y : 0) * o.height
						});
						n(mT(mT({}, c), {}, { payload: mT(mT({}, c.payload), {}, { coordinate: b }) }));
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
						n(FS({
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
						n(FS({
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
					n(FS({
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
		return $w.on(eT, s), () => {
			$w.off(eT, s);
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
function xT() {
	var e = L(Op), t = L(Ap), n = Lr();
	(0, C.useEffect)(() => {
		if (e == null) return fn;
		var r = (r, i, a) => {
			t !== a && e === r && n(uT(i));
		};
		return $w.on(tT, r), () => {
			$w.off(tT, r);
		};
	}, [
		n,
		t,
		e
	]);
}
function ST() {
	var e = Lr();
	(0, C.useEffect)(() => {
		e(aT());
	}, [e]), bT(), xT();
}
function CT(e, t, n, r, i, a) {
	var o = L((n) => fw(n, e, t)), s = L(zC), c = L(Ap), l = L(Op), u = L(kp), d = L(oT), f = (d == null ? void 0 : d.sourceViewBox) != null, p = Qc();
	(0, C.useEffect)(() => {
		if (!f && l != null && c != null) {
			var e = FS({
				active: a,
				coordinate: n,
				dataKey: o,
				index: i,
				label: typeof r == "number" ? String(r) : r,
				sourceViewBox: p,
				graphicalItemId: s
			});
			$w.emit(eT, l, e, c);
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
function wT(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function TT(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? wT(Object(n), !0).forEach(function(t) {
			ET(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : wT(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function ET(e, t, n) {
	return (t = DT(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function DT(e) {
	var t = OT(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function OT(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function kT(e, t) {
	return PT(e) || NT(e, t) || jT(e, t) || AT();
}
function AT() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function jT(e, t) {
	if (e) {
		if (typeof e == "string") return MT(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? MT(e, t) : void 0;
	}
}
function MT(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function NT(e, t) {
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
function PT(e) {
	if (Array.isArray(e)) return e;
}
function FT(e) {
	return e.dataKey;
}
function IT(e, t) {
	return /*#__PURE__*/ C.isValidElement(e) ? /*#__PURE__*/ C.cloneElement(e, t) : typeof e == "function" ? /*#__PURE__*/ C.createElement(e, t) : /*#__PURE__*/ C.createElement(Jl, t);
}
var LT = [], RT = {
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
function zT(e) {
	var t, n, r = Sn(e, RT), i = r.active, a = r.allowEscapeViewBox, o = r.animationDuration, s = r.animationEasing, c = r.content, l = r.filterNull, u = r.isAnimationActive, d = r.offset, f = r.payloadUniqBy, p = r.position, m = r.reverseDirection, h = r.useTranslate3d, g = r.wrapperStyle, _ = r.cursor, v = r.shared, y = r.trigger, b = r.defaultIndex, x = r.portal, S = r.axisId, w = Lr(), T = typeof b == "number" ? String(b) : b;
	(0, C.useEffect)(() => {
		w(OS({
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
	var E = Qc(), D = Cu(), O = yS(v), k = (t = L((e) => vw(e, O, y, T))) == null ? {} : t, A = k.activeIndex, j = k.isActive, M = L((e) => _w(e, O, y, T)), N = L((e) => gw(e, O, y, T)), P = L((e) => hw(e, O, y, T)), ee = M, te = Zw(), ne = (n = i == null ? j : i) != null && n, re = kT(Ti([ee, ne]), 2), ie = re[0], ae = re[1], oe = O === "axis" ? N : void 0;
	CT(O, y, P, oe, A, ne);
	var se = x == null ? te : x;
	if (se == null || E == null || O == null) return null;
	var ce = ee == null ? LT : ee;
	ne || (ce = LT), l && ce.length && (ce = kr(ce.filter((e) => e.value != null && (e.hide !== !0 || r.includeHidden)), f, FT));
	var le = ce.length > 0, ue = TT(TT({}, r), {}, {
		payload: ce,
		label: oe,
		active: ne,
		activeIndex: A,
		coordinate: P,
		accessibilityLayer: D
	}), de = /*#__PURE__*/ C.createElement(Su, {
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
	}, IT(c, ue));
	return /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ (0, zw.createPortal)(de, se), ne && /*#__PURE__*/ C.createElement(Yw, {
		cursor: _,
		tooltipEventType: O,
		coordinate: P,
		payload: ce,
		index: A
	}));
}
//#endregion
//#region node_modules/recharts/es6/component/Cell.js
var BT = (e) => null;
BT.displayName = "Cell";
//#endregion
//#region node_modules/recharts/es6/util/LRUCache.js
function VT(e, t, n) {
	return (t = HT(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function HT(e) {
	var t = UT(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function UT(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var WT = class {
	constructor(e) {
		VT(this, "cache", /* @__PURE__ */ new Map()), this.maxSize = e;
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
function GT(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function KT(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? GT(Object(n), !0).forEach(function(t) {
			qT(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : GT(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function qT(e, t, n) {
	return (t = JT(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function JT(e) {
	var t = YT(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function YT(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var XT = KT({}, {
	cacheSize: 2e3,
	enableCache: !0
}), ZT = new WT(XT.cacheSize), QT = {
	position: "absolute",
	top: "-20000px",
	left: 0,
	padding: 0,
	margin: 0,
	border: "none",
	whiteSpace: "pre"
}, $T = "recharts_measurement_span";
function eE(e, t) {
	return `${e}|${t.fontSize || ""}|${t.fontFamily || ""}|${t.fontWeight || ""}|${t.fontStyle || ""}|${t.letterSpacing || ""}|${t.textTransform || ""}`;
}
var tE = (e, t) => {
	try {
		var n = document.getElementById($T);
		n || (n = document.createElement("span"), n.setAttribute("id", $T), n.setAttribute("aria-hidden", "true"), document.body.appendChild(n)), Object.assign(n.style, QT, t), n.textContent = `${e}`;
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
}, nE = function(e) {
	var t = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : {};
	if (e == null || tu.isSsr) return {
		width: 0,
		height: 0
	};
	if (!XT.enableCache) return tE(e, t);
	var n = eE(e, t), r = ZT.get(n);
	if (r) return r;
	var i = tE(e, t);
	return ZT.set(n, i), i;
}, rE;
function iE(e, t) {
	return lE(e) || cE(e, t) || oE(e, t) || aE();
}
function aE() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function oE(e, t) {
	if (e) {
		if (typeof e == "string") return sE(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? sE(e, t) : void 0;
	}
}
function sE(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function cE(e, t) {
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
function lE(e) {
	if (Array.isArray(e)) return e;
}
function uE(e, t, n) {
	return (t = dE(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function dE(e) {
	var t = fE(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function fE(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var pE = /(-?\d+(?:\.\d+)?[a-zA-Z%]*)([*/])(-?\d+(?:\.\d+)?[a-zA-Z%]*)/, mE = /(-?\d+(?:\.\d+)?[a-zA-Z%]*)([+-])(-?\d+(?:\.\d+)?[a-zA-Z%]*)/, hE = /^(px|cm|vh|vw|em|rem|%|mm|in|pt|pc|ex|ch|vmin|vmax|Q)$/, gE = /(-?\d+(?:\.\d+)?)([a-zA-Z%]+)?/, _E = {
	cm: 96 / 2.54,
	mm: 96 / 25.4,
	pt: 96 / 72,
	pc: 96 / 6,
	in: 96,
	Q: 96 / (2.54 * 40),
	px: 1
}, vE = [
	"cm",
	"mm",
	"pt",
	"pc",
	"in",
	"Q",
	"px"
];
function yE(e) {
	return vE.includes(e);
}
var bE = "NaN";
function xE(e, t) {
	return e * _E[t];
}
var SE = class e {
	static parse(t) {
		var n, r = iE((n = gE.exec(t)) == null ? [] : n, 3), i = r[1], a = r[2];
		return i == null ? e.NaN : new e(parseFloat(i), a == null ? "" : a);
	}
	constructor(e, t) {
		this.num = e, this.unit = t, this.num = e, this.unit = t, $t(e) && (this.unit = ""), t !== "" && !hE.test(t) && (this.num = NaN, this.unit = ""), yE(t) && (this.num = xE(e, t), this.unit = "px");
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
		return $t(this.num);
	}
};
rE = SE, uE(SE, "NaN", new rE(NaN, ""));
function CE(e) {
	if (e == null || e.includes(bE)) return bE;
	for (var t = e; t.includes("*") || t.includes("/");) {
		var n, r = iE((n = pE.exec(t)) == null ? [] : n, 4), i = r[1], a = r[2], o = r[3], s = SE.parse(i == null ? "" : i), c = SE.parse(o == null ? "" : o), l = a === "*" ? s.multiply(c) : s.divide(c);
		if (l.isNaN()) return bE;
		t = t.replace(pE, l.toString());
	}
	for (; t.includes("+") || /.-\d+(?:\.\d+)?/.test(t);) {
		var u, d = iE((u = mE.exec(t)) == null ? [] : u, 4), f = d[1], p = d[2], m = d[3], h = SE.parse(f == null ? "" : f), g = SE.parse(m == null ? "" : m), _ = p === "+" ? h.add(g) : h.subtract(g);
		if (_.isNaN()) return bE;
		t = t.replace(mE, _.toString());
	}
	return t;
}
var wE = /\(([^()]*)\)/;
function TE(e) {
	for (var t = e, n; (n = wE.exec(t)) != null;) {
		var r = iE(n, 2)[1];
		t = t.replace(wE, CE(r));
	}
	return t;
}
function EE(e) {
	var t = e.replace(/\s+/g, "");
	return t = TE(t), t = CE(t), t;
}
function DE(e) {
	try {
		return EE(e);
	} catch (e) {
		return bE;
	}
}
function OE(e) {
	var t = DE(e.slice(5, -1));
	return t === bE ? "" : t;
}
//#endregion
//#region node_modules/recharts/es6/component/Text.js
var kE = [
	"x",
	"y",
	"lineHeight",
	"capHeight",
	"fill",
	"scaleToFit",
	"textAnchor",
	"verticalAnchor"
], AE = [
	"dx",
	"dy",
	"angle",
	"className",
	"breakAll"
];
function jE() {
	return jE = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, jE.apply(null, arguments);
}
function ME(e, t) {
	if (e == null) return {};
	var n, r, i = NE(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function NE(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function PE(e, t) {
	return zE(e) || RE(e, t) || IE(e, t) || FE();
}
function FE() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function IE(e, t) {
	if (e) {
		if (typeof e == "string") return LE(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? LE(e, t) : void 0;
	}
}
function LE(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function RE(e, t) {
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
function zE(e) {
	if (Array.isArray(e)) return e;
}
var BE = /[ \f\n\r\t\v\u2028\u2029]+/, VE = (e) => {
	var t = e.children, n = e.breakAll, r = e.style;
	try {
		var i = [];
		return ln(t) || (i = n ? t.toString().split("") : t.toString().split(BE)), {
			wordsWithComputedWidth: i.map((e) => ({
				word: e,
				width: nE(e, r).width
			})),
			spaceWidth: n ? 0 : nE("\xA0", r).width
		};
	} catch (e) {
		return null;
	}
};
function HE(e) {
	return e === "start" || e === "middle" || e === "end" || e === "inherit";
}
function UE(e) {
	return ln(e) || typeof e == "string" || typeof e == "number" || typeof e == "boolean";
}
var WE = (e, t, n, r) => e.reduce((e, i) => {
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
}, []), GE = (e) => e.reduce((e, t) => e.width > t.width ? e : t), KE = "…", qE = (e, t, n, r, i, a, o, s) => {
	var c = VE({
		breakAll: n,
		style: r,
		children: e.slice(0, t) + KE
	});
	if (!c) return [!1, []];
	var l = WE(c.wordsWithComputedWidth, a, o, s);
	return [l.length > i || GE(l).width > Number(a), l];
}, JE = (e, t, n, r, i) => {
	var a = e.maxLines, o = e.children, s = e.style, c = e.breakAll, l = I(a), u = String(o), d = WE(t, r, n, i);
	if (!l || i || !(d.length > a || GE(d).width > Number(r))) return d;
	for (var f = 0, p = u.length - 1, m = 0, h; f <= p && m <= u.length - 1;) {
		var g = Math.floor((f + p) / 2), _ = PE(qE(u, g - 1, c, s, a, r, n, i), 2), v = _[0], y = _[1], b = PE(qE(u, g, c, s, a, r, n, i), 1)[0];
		if (!v && !b && (f = g + 1), v && b && (p = g - 1), !v && b) {
			h = y;
			break;
		}
		m++;
	}
	return h || d;
}, YE = (e) => [{
	words: ln(e) ? [] : e.toString().split(BE),
	width: void 0
}], XE = (e) => {
	var t = e.width, n = e.scaleToFit, r = e.children, i = e.style, a = e.breakAll, o = e.maxLines;
	if ((t || n) && !tu.isSsr) {
		var s, c, l = VE({
			breakAll: a,
			children: r,
			style: i
		});
		if (l) {
			var u = l.wordsWithComputedWidth, d = l.spaceWidth;
			s = u, c = d;
		} else return YE(r);
		return JE({
			breakAll: a,
			children: r,
			maxLines: o,
			style: i
		}, s, c, t, !!n);
	}
	return YE(r);
}, ZE = "#808080", QE = {
	angle: 0,
	breakAll: !1,
	capHeight: "0.71em",
	fill: ZE,
	lineHeight: "1em",
	scaleToFit: !1,
	textAnchor: "start",
	verticalAnchor: "end",
	x: 0,
	y: 0
}, $E = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = Sn(e, QE), r = n.x, i = n.y, a = n.lineHeight, o = n.capHeight, s = n.fill, c = n.scaleToFit, l = n.textAnchor, u = n.verticalAnchor, d = ME(n, kE), f = (0, C.useMemo)(() => XE({
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
	]), p = d.dx, m = d.dy, h = d.angle, g = d.className, _ = d.breakAll, v = ME(d, AE);
	if (!tn(r) || !tn(i) || f.length === 0) return null;
	var y = Number(r) + (I(p) ? p : 0), b = Number(i) + (I(m) ? m : 0);
	if (!U(y) || !U(b)) return null;
	var x;
	switch (u) {
		case "start":
			x = OE(`calc(${o})`);
			break;
		case "middle":
			x = OE(`calc(${(f.length - 1) / 2} * -${a} + (${o} / 2))`);
			break;
		default:
			x = OE(`calc(${f.length - 1} * -${a})`);
			break;
	}
	var S = [], w = f[0];
	if (c && w != null) {
		var T = w.width, E = d.width;
		S.push(`scale(${I(E) && I(T) ? E / T : 1})`);
	}
	return h && S.push(`rotate(${h}, ${y}, ${b})`), S.length && (v.transform = S.join(" ")), /*#__PURE__*/ C.createElement("text", jE({}, je(v), {
		ref: t,
		x: y,
		y: b,
		className: Ce("recharts-text", g),
		textAnchor: l,
		fill: s.includes("url") ? ZE : s
	}), f.map((e, t) => {
		var n = e.words.join(_ ? "" : " ");
		return /*#__PURE__*/ C.createElement("tspan", {
			x: y,
			dy: t === 0 ? x : a,
			key: `${n}-${t}`
		}, n);
	}));
});
$E.displayName = "Text";
//#endregion
//#region node_modules/recharts/es6/cartesian/getCartesianPosition.js
function eD(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function tD(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? eD(Object(n), !0).forEach(function(t) {
			nD(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : eD(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function nD(e, t, n) {
	return (t = rD(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function rD(e) {
	var t = iD(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function iD(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var aD = (e) => {
	var t = e.viewBox, n = e.position, r = e.offset, i = r === void 0 ? 0 : r, a = e.parentViewBox, o = e.clamp, s = Zc(t), c = s.x, l = s.y, u = s.height, d = s.upperWidth, f = s.lowerWidth, p = c, m = c + (d - f) / 2, h = (p + m) / 2, g = (d + f) / 2, _ = p + d / 2, v = u >= 0 ? 1 : -1, y = v * i, b = v > 0 ? "end" : "start", x = v > 0 ? "start" : "end", S = d >= 0 ? 1 : -1, C = S * i, w = S > 0 ? "end" : "start", T = S > 0 ? "start" : "end", E = a;
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
	return n === "insideLeft" ? tD({
		x: h + C,
		y: l + u / 2,
		horizontalAnchor: T,
		verticalAnchor: "middle"
	}, j) : n === "insideRight" ? tD({
		x: h + g - C,
		y: l + u / 2,
		horizontalAnchor: w,
		verticalAnchor: "middle"
	}, j) : n === "insideTop" ? tD({
		x: p + d / 2,
		y: l + y,
		horizontalAnchor: "middle",
		verticalAnchor: x
	}, j) : n === "insideBottom" ? tD({
		x: m + f / 2,
		y: l + u - y,
		horizontalAnchor: "middle",
		verticalAnchor: b
	}, j) : n === "insideTopLeft" ? tD({
		x: p + C,
		y: l + y,
		horizontalAnchor: T,
		verticalAnchor: x
	}, j) : n === "insideTopRight" ? tD({
		x: p + d - C,
		y: l + y,
		horizontalAnchor: w,
		verticalAnchor: x
	}, j) : n === "insideBottomLeft" ? tD({
		x: m + C,
		y: l + u - y,
		horizontalAnchor: T,
		verticalAnchor: b
	}, j) : n === "insideBottomRight" ? tD({
		x: m + f - C,
		y: l + u - y,
		horizontalAnchor: w,
		verticalAnchor: b
	}, j) : n && typeof n == "object" && (I(n.x) || en(n.x)) && (I(n.y) || en(n.y)) ? tD({
		x: c + an(n.x, g),
		y: l + an(n.y, u),
		horizontalAnchor: "end",
		verticalAnchor: "end"
	}, j) : tD({
		x: _,
		y: l + u / 2,
		horizontalAnchor: "middle",
		verticalAnchor: "middle"
	}, j);
}, oD = ["labelRef"], sD = ["content"];
function cD(e, t) {
	if (e == null) return {};
	var n, r, i = lD(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function lD(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function uD(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function dD(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? uD(Object(n), !0).forEach(function(t) {
			fD(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : uD(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function fD(e, t, n) {
	return (t = pD(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function pD(e) {
	var t = mD(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function mD(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function hD() {
	return hD = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, hD.apply(null, arguments);
}
var gD = /*#__PURE__*/ (0, C.createContext)(null), _D = (e) => {
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
	return /*#__PURE__*/ C.createElement(gD.Provider, { value: c }, s);
}, vD = () => {
	var e = (0, C.useContext)(gD), t = Qc();
	return e || (t ? Zc(t) : void 0);
}, yD = /*#__PURE__*/ (0, C.createContext)(null), bD = () => {
	var e = (0, C.useContext)(yD), t = L(Zp);
	return e || t;
}, xD = (e) => {
	var t = e.value, n = e.formatter, r = ln(e.children) ? t : e.children;
	return typeof n == "function" ? n(r) : r;
}, SD = (e) => e != null && typeof e == "function", CD = (e, t) => Qt(t - e) * Math.min(Math.abs(t - e), 360), wD = (e, t, n, r, i) => {
	var a = e.offset, o = e.className, s = i.cx, c = i.cy, l = i.innerRadius, u = i.outerRadius, d = i.startAngle, f = i.endAngle, p = i.clockWise, m = (l + u) / 2, h = CD(d, f), g = h >= 0 ? 1 : -1, _, v;
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
	var y = _f(s, c, m, _), b = _f(s, c, m, _ + (v ? 1 : -1) * 359), x = `M${y.x},${y.y}
    A${m},${m},0,1,${+!v},
    ${b.x},${b.y}`, S = ln(e.id) ? rn("recharts-radial-line-") : e.id;
	return /*#__PURE__*/ C.createElement("text", hD({}, r, {
		dominantBaseline: "central",
		className: Ce("recharts-radial-bar-label", o)
	}), /*#__PURE__*/ C.createElement("defs", null, /*#__PURE__*/ C.createElement("path", {
		id: S,
		d: x
	})), /*#__PURE__*/ C.createElement("textPath", { xlinkHref: `#${S}` }, n));
}, TD = (e, t, n) => {
	var r = e.cx, i = e.cy, a = e.innerRadius, o = e.outerRadius, s = (e.startAngle + e.endAngle) / 2;
	if (n === "outside") {
		var c = _f(r, i, o + t, s), l = c.x;
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
	var u = _f(r, i, (a + o) / 2, s);
	return {
		x: u.x,
		y: u.y,
		textAnchor: "middle",
		verticalAnchor: "middle"
	};
}, ED = (e) => e != null && "cx" in e && I(e.cx), DD = {
	angle: 0,
	offset: 5,
	zIndex: jp.label,
	position: "middle",
	textBreakAll: !1
};
function OD(e) {
	if (!ED(e)) return e;
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
function kD(e) {
	var t = Sn(e, DD), n = t.viewBox, r = t.parentViewBox, i = t.position, a = t.value, o = t.children, s = t.content, c = t.className, l = c === void 0 ? "" : c, u = t.textBreakAll, d = t.labelRef, f = bD(), p = vD(), m = n == null ? i === "center" || f == null ? p : f : ED(n) ? n : Zc(n), h, g, _ = OD(m);
	if (!m || ln(a) && ln(o) && !/*#__PURE__*/ (0, C.isValidElement)(s) && typeof s != "function") return null;
	var v = dD(dD({}, t), {}, { viewBox: m });
	if (/*#__PURE__*/ (0, C.isValidElement)(s)) return v.labelRef, /*#__PURE__*/ (0, C.cloneElement)(s, cD(v, oD));
	if (typeof s == "function") {
		if (v.content, h = /*#__PURE__*/ (0, C.createElement)(s, cD(v, sD)), /*#__PURE__*/ (0, C.isValidElement)(h)) return h;
	} else h = xD(t);
	var y = je(t);
	if (ED(m)) {
		if (i === "insideStart" || i === "insideEnd" || i === "end") return wD(t, i, h, y, m);
		g = TD(m, t.offset, t.position);
	} else {
		if (!_) return null;
		var b = aD({
			viewBox: _,
			position: i,
			offset: t.offset,
			parentViewBox: ED(r) ? void 0 : r,
			clamp: !0
		});
		g = dD(dD({
			x: b.x,
			y: b.y,
			textAnchor: b.horizontalAnchor,
			verticalAnchor: b.verticalAnchor
		}, b.width === void 0 ? {} : { width: b.width }), b.height === void 0 ? {} : { height: b.height });
	}
	return /*#__PURE__*/ C.createElement(Bw, { zIndex: t.zIndex }, /*#__PURE__*/ C.createElement($E, hD({
		ref: d,
		className: Ce("recharts-label", l)
	}, y, g, {
		textAnchor: HE(y.textAnchor) ? y.textAnchor : g.textAnchor,
		breakAll: u
	}), h));
}
kD.displayName = "Label";
var AD = (e, t, n) => {
	if (!e) return null;
	var r = {
		viewBox: t,
		labelRef: n
	};
	return e === !0 ? /*#__PURE__*/ C.createElement(kD, hD({ key: "label-implicit" }, r)) : tn(e) ? /*#__PURE__*/ C.createElement(kD, hD({
		key: "label-implicit",
		value: e
	}, r)) : /*#__PURE__*/ (0, C.isValidElement)(e) ? e.type === kD ? /*#__PURE__*/ (0, C.cloneElement)(e, dD({ key: "label-implicit" }, r)) : /*#__PURE__*/ C.createElement(kD, hD({
		key: "label-implicit",
		content: e
	}, r)) : SD(e) ? /*#__PURE__*/ C.createElement(kD, hD({
		key: "label-implicit",
		content: e
	}, r)) : e && typeof e == "object" ? /*#__PURE__*/ C.createElement(kD, hD({}, e, { key: "label-implicit" }, r)) : null;
};
function jD(e) {
	var t = e.label, n = e.labelRef;
	return AD(t, vD(), n) || null;
}
//#endregion
//#region node_modules/recharts/es6/component/LabelList.js
var MD = ["valueAccessor"], ND = [
	"dataKey",
	"clockWise",
	"id",
	"textBreakAll",
	"zIndex"
];
function PD() {
	return PD = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, PD.apply(null, arguments);
}
function FD(e, t) {
	if (e == null) return {};
	var n, r, i = ID(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function ID(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var LD = (e) => {
	var t = Array.isArray(e.value) ? e.value[e.value.length - 1] : e.value;
	if (UE(t)) return t;
}, RD = /*#__PURE__*/ (0, C.createContext)(void 0), zD = RD.Provider, BD = /*#__PURE__*/ (0, C.createContext)(void 0);
BD.Provider;
function VD() {
	return (0, C.useContext)(RD);
}
function HD() {
	return (0, C.useContext)(BD);
}
function UD(e) {
	var t = e.valueAccessor, n = t === void 0 ? LD : t, r = FD(e, MD), i = r.dataKey;
	r.clockWise;
	var a = r.id, o = r.textBreakAll, s = r.zIndex, c = FD(r, ND), l = VD(), u = HD(), d = l || u;
	return !d || !d.length ? null : /*#__PURE__*/ C.createElement(Bw, { zIndex: s == null ? jp.label : s }, /*#__PURE__*/ C.createElement(Ve, { className: "recharts-label-list" }, d.map((e, t) => {
		var s, l = ln(i) ? n(e, t) : js(e.payload, i), u = ln(a) ? {} : { id: `${a}-${t}` };
		return /*#__PURE__*/ C.createElement(kD, PD({ key: `label-${t}` }, je(e), c, u, {
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
UD.displayName = "LabelList";
function WD(e) {
	var t = e.label;
	return t ? t === !0 ? /*#__PURE__*/ C.createElement(UD, { key: "labelList-implicit" }) : /*#__PURE__*/ C.isValidElement(t) || SD(t) ? /*#__PURE__*/ C.createElement(UD, {
		key: "labelList-implicit",
		content: t
	}) : typeof t == "object" ? /*#__PURE__*/ C.createElement(UD, PD({ key: "labelList-implicit" }, t, { type: String(t.type) })) : null : null;
}
//#endregion
//#region node_modules/recharts/es6/state/polarAxisSlice.js
var GD = H({
	name: "polarAxis",
	initialState: {
		radiusAxis: {},
		angleAxis: {}
	},
	reducers: {
		addRadiusAxis(e, t) {
			e.radiusAxis[t.payload.id] = B(t.payload);
		},
		removeRadiusAxis(e, t) {
			delete e.radiusAxis[t.payload.id];
		},
		addAngleAxis(e, t) {
			e.angleAxis[t.payload.id] = B(t.payload);
		},
		removeAngleAxis(e, t) {
			delete e.angleAxis[t.payload.id];
		}
	}
}), KD = GD.actions;
KD.addRadiusAxis, KD.removeRadiusAxis, KD.addAngleAxis, KD.removeAngleAxis;
var qD = GD.reducer;
//#endregion
//#region node_modules/recharts/es6/util/getClassNameFromUnknown.js
function JD(e) {
	return e && typeof e == "object" && "className" in e && typeof e.className == "string" ? e.className : "";
}
//#endregion
//#region node_modules/react-is/cjs/react-is.production.min.js
var YD = /* @__PURE__ */ o(((e) => {
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
})), XD = (/* @__PURE__ */ o(((e, t) => {
	t.exports = YD();
})))(), ZD = (e) => typeof e == "string" ? e : e ? e.displayName || e.name || "Component" : "", QD = null, $D = null, eO = (e) => {
	if (e === QD && Array.isArray($D)) return $D;
	var t = [];
	return C.Children.forEach(e, (e) => {
		ln(e) || ((0, XD.isFragment)(e) ? t = t.concat(eO(e.props.children)) : t.push(e));
	}), $D = t, QD = e, t;
};
function tO(e, t) {
	var n = [], r = [];
	return r = Array.isArray(t) ? t.map((e) => ZD(e)) : [ZD(t)], eO(e).forEach((e) => {
		var t = qt(e, "type.displayName") || qt(e, "type.name");
		t && r.indexOf(t) !== -1 && n.push(e);
	}), n;
}
//#endregion
//#region node_modules/recharts/es6/util/ActiveShapeUtils.js
function nO(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function rO(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? nO(Object(n), !0).forEach(function(t) {
			iO(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : nO(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function iO(e, t, n) {
	return (t = aO(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function aO(e) {
	var t = oO(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function oO(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function sO(e, t) {
	return rO(rO({}, t), e);
}
function cO(e) {
	return /*#__PURE__*/ (0, C.isValidElement)(e) ? e.props : e;
}
function lO(e, t) {
	return /*#__PURE__*/ (0, C.cloneElement)(e, sO(cO(e), t));
}
function uO(e) {
	if ("index" in e) {
		var t = e.index;
		return typeof t == "number" || typeof t == "string" ? t : void 0;
	}
}
function dO(e) {
	return "isActive" in e && e.isActive === !0;
}
function fO(e) {
	var t = e.option, n = e.DefaultShape, r = e.shapeProps, i = e.activeClassName, a = i === void 0 ? "recharts-active-shape" : i, o = e.inActiveClassName, s = o === void 0 ? "recharts-shape" : o, c = uO(r), l = /*#__PURE__*/ (0, C.isValidElement)(t) ? lO(t, r) : t === n ? /*#__PURE__*/ C.createElement(n, r) : typeof t == "function" ? t(r, c) : typeof t == "object" ? /*#__PURE__*/ C.createElement(n, sO(t, r)) : /*#__PURE__*/ C.createElement(n, r);
	return dO(r) ? /*#__PURE__*/ C.createElement(Ve, { className: a }, l) : /*#__PURE__*/ C.createElement(Ve, { className: s }, l);
}
//#endregion
//#region node_modules/recharts/es6/context/tooltipContext.js
var pO = (e, t, n) => {
	var r = Lr();
	return (i, a) => (o) => {
		e == null || e(i, a, o), r(kS({
			activeIndex: String(a),
			activeDataKey: t,
			activeCoordinate: i.tooltipPosition,
			activeGraphicalItemId: n
		}));
	};
}, mO = (e) => {
	var t = Lr();
	return (n, r) => (i) => {
		e == null || e(n, r, i), t(AS());
	};
}, hO = (e, t, n) => {
	var r = Lr();
	return (i, a) => (o) => {
		e == null || e(i, a, o), r(MS({
			activeIndex: String(a),
			activeDataKey: t,
			activeCoordinate: i.tooltipPosition,
			activeGraphicalItemId: n
		}));
	};
};
//#endregion
//#region node_modules/recharts/es6/state/SetTooltipEntrySettings.js
function gO(e) {
	var t = e.tooltipEntrySettings, n = Lr(), r = _c(), i = (0, C.useRef)(null);
	return (0, C.useLayoutEffect)(() => {
		r || (i.current === null ? n(TS(t)) : i.current !== t && n(ES({
			prev: i.current,
			next: t
		})), i.current = t);
	}, [
		t,
		n,
		r
	]), (0, C.useLayoutEffect)(() => () => {
		i.current && (n(DS(i.current)), i.current = null);
	}, [n]), null;
}
//#endregion
//#region node_modules/recharts/es6/state/SetLegendPayload.js
function _O(e) {
	var t = e.legendPayload, n = Lr(), r = _c(), i = (0, C.useRef)(null);
	return (0, C.useLayoutEffect)(() => {
		r || (i.current === null ? n(ul(t)) : i.current !== t && n(dl({
			prev: i.current,
			next: t
		})), i.current = t);
	}, [
		n,
		r,
		t
	]), (0, C.useLayoutEffect)(() => () => {
		i.current && (n(fl(i.current)), i.current = null);
	}, [n]), null;
}
//#endregion
//#region node_modules/recharts/es6/animation/matchBy.js
function vO(e, t) {
	return CO(e) || SO(e, t) || bO(e, t) || yO();
}
function yO() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function bO(e, t) {
	if (e) {
		if (typeof e == "string") return xO(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? xO(e, t) : void 0;
	}
}
function xO(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function SO(e, t) {
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
function CO(e) {
	if (Array.isArray(e)) return e;
}
var wO = "index", TO = "append";
function EO(e, t) {
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
function DO(e, t) {
	var n = e.length / t.length;
	return EO(t.map((t, r) => e[Math.floor(r * n)]), t);
}
function OO(e, t) {
	return EO(t.map((t, n) => e[n]), t);
}
function kO(e, t) {
	for (var n = /* @__PURE__ */ new Map(), r = 0; r < e.length; r++) {
		var i = e[r];
		if (i != null) {
			var a = t(i, r);
			a != null && !n.has(a) && n.set(a, i);
		}
	}
	return n;
}
function AO(e, t, n) {
	var r = kO(e, n), i = /* @__PURE__ */ new Set(), a = t.map((e, t) => {
		var a = n(e, t);
		if (a != null) {
			var o = r.get(a);
			if (o !== void 0) return i.add(a), o;
		}
	}), o = [];
	for (var s of r) {
		var c = vO(s, 2), l = c[0], u = c[1];
		i.has(l) || o.push(u);
	}
	return EO(a, t, o);
}
function jO(e, t, n) {
	return t == null ? null : e == null ? t.map((e) => ({
		status: "added",
		next: e
	})) : n === "index" ? DO(e, t) : n === "append" ? OO(e, t) : AO(e, t, n);
}
//#endregion
//#region node_modules/recharts/es6/animation/useAnimationStartSnapshot.js
function MO(e, t) {
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
function zO(e, t) {
	var n = NO((0, C.useState)(!1), 2), r = n[0], i = n[1];
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
function BO(e) {
	var t, n = e.animationInput, r = e.animationIdPrefix, i = e.items, a = e.previousItemsRef, o = e.isAnimationActive, s = e.animationBegin, c = e.animationDuration, l = e.animationEasing, u = e.onAnimationStart, d = e.onAnimationEnd, f = e.animationInterpolateFn, p = e.animationMatchBy, m = e.shouldUpdatePreviousRef, h = e.children, g = e.layout, _ = Ad(n, r), v = MO(_, a), y = (t = v.startValue) == null ? null : t, b = jO(y, i, p == null ? wO : p);
	return /*#__PURE__*/ C.createElement(kd, {
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
var VO;
function HO(e, t) {
	return qO(e) || KO(e, t) || WO(e, t) || UO();
}
function UO() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function WO(e, t) {
	if (e) {
		if (typeof e == "string") return GO(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? GO(e, t) : void 0;
	}
}
function GO(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function KO(e, t) {
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
function qO(e) {
	if (Array.isArray(e)) return e;
}
var JO = (VO = C.useId) == null ? () => HO(C.useState(() => rn("uid-")), 1)[0] : VO;
//#endregion
//#region node_modules/recharts/es6/util/useUniqueId.js
function YO(e, t) {
	var n = JO();
	return t || (e ? `${e}-${n}` : n);
}
//#endregion
//#region node_modules/recharts/es6/context/RegisterGraphicalItemId.js
var XO = /*#__PURE__*/ (0, C.createContext)(void 0), ZO = (e) => {
	var t = e.id, n = e.type, r = e.children, i = YO(`recharts-${n}`, t);
	return /*#__PURE__*/ C.createElement(XO.Provider, { value: i }, r(i));
}, QO = H({
	name: "graphicalItems",
	initialState: {
		cartesianItems: [],
		polarItems: []
	},
	reducers: {
		addCartesianGraphicalItem: {
			reducer(e, t) {
				e.cartesianItems.push(B(t.payload));
			},
			prepare: V()
		},
		replaceCartesianGraphicalItem: {
			reducer(e, t) {
				var n = t.payload, r = n.prev, i = n.next, a = to(e).cartesianItems.indexOf(B(r));
				a > -1 && (e.cartesianItems[a] = B(i));
			},
			prepare: V()
		},
		removeCartesianGraphicalItem: {
			reducer(e, t) {
				var n = to(e).cartesianItems.indexOf(B(t.payload));
				n > -1 && e.cartesianItems.splice(n, 1);
			},
			prepare: V()
		},
		addPolarGraphicalItem: {
			reducer(e, t) {
				e.polarItems.push(B(t.payload));
			},
			prepare: V()
		},
		removePolarGraphicalItem: {
			reducer(e, t) {
				var n = to(e).polarItems.indexOf(B(t.payload));
				n > -1 && e.polarItems.splice(n, 1);
			},
			prepare: V()
		},
		replacePolarGraphicalItem: {
			reducer(e, t) {
				var n = t.payload, r = n.prev, i = n.next, a = to(e).polarItems.indexOf(B(r));
				a > -1 && (e.polarItems[a] = B(i));
			},
			prepare: V()
		}
	}
}), $O = QO.actions, ek = $O.addCartesianGraphicalItem, tk = $O.replaceCartesianGraphicalItem, nk = $O.removeCartesianGraphicalItem;
$O.addPolarGraphicalItem, $O.removePolarGraphicalItem, $O.replacePolarGraphicalItem;
var rk = QO.reducer, ik = /*#__PURE__*/ (0, C.memo)((e) => {
	var t = Lr(), n = (0, C.useRef)(null);
	return (0, C.useLayoutEffect)(() => {
		n.current === null ? t(ek(e)) : n.current !== e && t(tk({
			prev: n.current,
			next: e
		})), n.current = e;
	}, [t, e]), (0, C.useLayoutEffect)(() => () => {
		n.current && (t(nk(n.current)), n.current = null);
	}, [t]), null;
});
//#endregion
//#region node_modules/recharts/es6/state/cartesianAxisSlice.js
function ak(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function ok(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? ak(Object(n), !0).forEach(function(t) {
			sk(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : ak(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function sk(e, t, n) {
	return (t = ck(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function ck(e) {
	var t = lk(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function lk(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var uk = H({
	name: "cartesianAxis",
	initialState: {
		xAxis: {},
		yAxis: {},
		zAxis: {}
	},
	reducers: {
		addXAxis: {
			reducer(e, t) {
				e.xAxis[t.payload.id] = B(t.payload);
			},
			prepare: V()
		},
		replaceXAxis: {
			reducer(e, t) {
				var n = t.payload, r = n.prev, i = n.next;
				e.xAxis[r.id] !== void 0 && (r.id !== i.id && delete e.xAxis[r.id], e.xAxis[i.id] = B(i));
			},
			prepare: V()
		},
		removeXAxis: {
			reducer(e, t) {
				delete e.xAxis[t.payload.id];
			},
			prepare: V()
		},
		addYAxis: {
			reducer(e, t) {
				e.yAxis[t.payload.id] = B(t.payload);
			},
			prepare: V()
		},
		replaceYAxis: {
			reducer(e, t) {
				var n = t.payload, r = n.prev, i = n.next;
				e.yAxis[r.id] !== void 0 && (r.id !== i.id && delete e.yAxis[r.id], e.yAxis[i.id] = B(i));
			},
			prepare: V()
		},
		removeYAxis: {
			reducer(e, t) {
				delete e.yAxis[t.payload.id];
			},
			prepare: V()
		},
		addZAxis: {
			reducer(e, t) {
				e.zAxis[t.payload.id] = B(t.payload);
			},
			prepare: V()
		},
		replaceZAxis: {
			reducer(e, t) {
				var n = t.payload, r = n.prev, i = n.next;
				e.zAxis[r.id] !== void 0 && (r.id !== i.id && delete e.zAxis[r.id], e.zAxis[i.id] = B(i));
			},
			prepare: V()
		},
		removeZAxis: {
			reducer(e, t) {
				delete e.zAxis[t.payload.id];
			},
			prepare: V()
		},
		updateYAxisWidth(e, t) {
			var n = t.payload, r = n.id, i = n.width, a = e.yAxis[r];
			if (a) {
				var o, s = a.widthHistory || [];
				if (s.length === 3 && s[0] === s[2] && i === s[1] && i !== a.width && Math.abs(i - ((o = s[0]) == null ? 0 : o)) <= 1) return;
				var c = [...s, i].slice(-3);
				e.yAxis[r] = ok(ok({}, a), {}, {
					width: i,
					widthHistory: c
				});
			}
		}
	}
}), dk = uk.actions, fk = dk.addXAxis, pk = dk.replaceXAxis, mk = dk.removeXAxis, hk = dk.addYAxis, gk = dk.replaceYAxis, _k = dk.removeYAxis;
dk.addZAxis, dk.replaceZAxis, dk.removeZAxis;
var vk = dk.updateYAxisWidth, yk = uk.reducer, bk = R([
	R([pc], (e) => ({
		top: e.top,
		bottom: e.bottom,
		left: e.left,
		right: e.right
	})),
	Xs,
	Zs
], (e, t, n) => {
	if (!(!e || t == null || n == null)) return {
		x: e.left,
		y: e.top,
		width: Math.max(0, t - e.left - e.right),
		height: Math.max(0, n - e.top - e.bottom)
	};
}), xk = () => L(bk);
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineBarSizeList.js
function Sk(e, t) {
	return Dk(e) || Ek(e, t) || wk(e, t) || Ck();
}
function Ck() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function wk(e, t) {
	if (e) {
		if (typeof e == "string") return Tk(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? Tk(e, t) : void 0;
	}
}
function Tk(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function Ek(e, t) {
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
function Dk(e) {
	if (Array.isArray(e)) return e;
}
var Ok = (e, t, n) => {
	var r = n == null ? e : n;
	if (!ln(r)) return an(r, t, 0);
}, kk = (e, t, n) => {
	var r = {}, i = e.filter(nm), a = e.filter((e) => e.stackId == null), o = i.reduce((e, t) => {
		var n = e[t.stackId];
		return n == null && (n = []), n.push(t), e[t.stackId] = n, e;
	}, r), s = Object.entries(o).map((e) => {
		var r, i = Sk(e, 2), a = i[0], o = i[1];
		return {
			stackId: a,
			dataKeys: o.map((e) => e.dataKey),
			barSize: Ok(t, n, (r = o[0]) == null ? void 0 : r.barSize)
		};
	}), c = a.map((e) => ({
		stackId: void 0,
		dataKeys: [e.dataKey].filter((e) => e != null),
		barSize: Ok(t, n, e.barSize)
	}));
	return [...s, ...c];
};
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineAllBarPositions.js
function Ak(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function jk(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Ak(Object(n), !0).forEach(function(t) {
			Mk(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Ak(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Mk(e, t, n) {
	return (t = Nk(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function Nk(e) {
	var t = Pk(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Pk(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function Fk(e, t, n, r, i) {
	var a, o = r.length;
	if (!(o < 1)) {
		var s = an(e, n, 0, !0), c, l = [];
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
			var m = an(t, n, 0, !0);
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
var Ik = (e, t, n, r, i, a, o) => {
	var s = ln(o) ? t : o, c = Fk(n, r, i === a ? a : i, e, s);
	return i !== a && c != null && (c = c.map((e) => jk(jk({}, e), {}, { position: jk(jk({}, e.position), {}, { offset: e.position.offset - i / 2 }) }))), c;
}, Lk = (e, t) => {
	var n = em(t);
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
}, Rk = (e, t) => {
	if (!(e == null || t == null)) {
		var n = e.find((e) => e.stackId === t.stackId && t.dataKey != null && e.dataKeys.includes(t.dataKey));
		if (n != null) return n.position;
	}
};
//#endregion
//#region node_modules/recharts/es6/zIndex/getZIndexFromUnknown.js
function zk(e, t) {
	return e && typeof e == "object" && "zIndex" in e && typeof e.zIndex == "number" && U(e.zIndex) ? e.zIndex : t;
}
//#endregion
//#region node_modules/recharts/es6/context/chartDataContext.js
var Bk = (e) => {
	var t = e.chartData, n = Lr(), r = _c();
	return (0, C.useEffect)(() => r ? () => {} : (n(lT(t)), () => {
		n(lT(void 0));
	}), [
		t,
		n,
		r
	]), null;
}, Vk = {
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
}, Hk = H({
	name: "brush",
	initialState: Vk,
	reducers: { setBrushSettings(e, t) {
		return t.payload == null ? Vk : t.payload;
	} }
});
Hk.actions.setBrushSettings;
var Uk = Hk.reducer;
//#endregion
//#region node_modules/recharts/es6/util/CartesianUtils.js
function Wk(e) {
	return (e % 180 + 180) % 180;
}
var Gk = function(e) {
	var t = e.width, n = e.height, r = Wk(arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : 0) * Math.PI / 180, i = Math.atan(n / t), a = r > i && r < Math.PI - i ? n / Math.sin(r) : t / Math.cos(r);
	return Math.abs(a);
}, Kk = H({
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
			var n = to(e).dots.findIndex((e) => e === t.payload);
			n !== -1 && e.dots.splice(n, 1);
		},
		addArea: (e, t) => {
			e.areas.push(t.payload);
		},
		removeArea: (e, t) => {
			var n = to(e).areas.findIndex((e) => e === t.payload);
			n !== -1 && e.areas.splice(n, 1);
		},
		addLine: (e, t) => {
			e.lines.push(B(t.payload));
		},
		removeLine: (e, t) => {
			var n = to(e).lines.findIndex((e) => e === t.payload);
			n !== -1 && e.lines.splice(n, 1);
		}
	}
}), qk = Kk.actions;
qk.addDot, qk.removeDot, qk.addArea, qk.removeArea, qk.addLine, qk.removeLine;
var Jk = Kk.reducer;
//#endregion
//#region node_modules/recharts/es6/container/ClipPathProvider.js
function Yk(e, t) {
	return eA(e) || $k(e, t) || Zk(e, t) || Xk();
}
function Xk() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function Zk(e, t) {
	if (e) {
		if (typeof e == "string") return Qk(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? Qk(e, t) : void 0;
	}
}
function Qk(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function $k(e, t) {
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
function eA(e) {
	if (Array.isArray(e)) return e;
}
var tA = /*#__PURE__*/ (0, C.createContext)(void 0), nA = (e) => {
	var t = e.children, n = Yk((0, C.useState)(`${rn("recharts")}-clip`), 1)[0], r = xk();
	if (r == null) return null;
	var i = r.x, a = r.y, o = r.width, s = r.height;
	return /*#__PURE__*/ C.createElement(tA.Provider, { value: n }, /*#__PURE__*/ C.createElement("defs", null, /*#__PURE__*/ C.createElement("clipPath", { id: n }, /*#__PURE__*/ C.createElement("rect", {
		x: i,
		y: a,
		height: s,
		width: o
	}))), t);
};
//#endregion
//#region node_modules/recharts/es6/util/getEveryNth.js
function rA(e, t) {
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
function iA(e, t, n) {
	return Gk({
		width: e.width + t.width,
		height: e.height + t.height
	}, n);
}
function aA(e, t, n) {
	var r = n === "width", i = e.x, a = e.y, o = e.width, s = e.height;
	return t === 1 ? {
		start: r ? i : a,
		end: r ? i + o : a + s
	} : {
		start: r ? i + o : a + s,
		end: r ? i : a
	};
}
function oA(e, t, n, r, i) {
	if (e * t < e * r || e * t > e * i) return !1;
	var a = n();
	return e * (t - e * a / 2 - r) >= 0 && e * (t + e * a / 2 - i) <= 0;
}
function sA(e, t) {
	return rA(e, t + 1);
}
//#endregion
//#region node_modules/recharts/es6/cartesian/getEquidistantTicks.js
function cA(e, t, n, r, i) {
	for (var a = (r || []).slice(), o = t.start, s = t.end, c = 0, l = 1, u = o, d = function() {
		var t = r == null ? void 0 : r[c];
		if (t === void 0) return { v: rA(r, l) };
		var a = c, d, f = () => (d === void 0 && (d = n(t, a)), d), p = t.coordinate, m = c === 0 || oA(e, p, f, u, s);
		m || (c = 0, u = o, l += 1), m && (u = p + e * (f() / 2 + i), c += l);
	}, f; l <= a.length;) if (f = d(), f) return f.v;
	return [];
}
function lA(e, t, n, r, i) {
	var a = (r || []).slice().length;
	if (a === 0) return [];
	for (var o = t.start, s = t.end, c = 1; c <= a; c++) {
		for (var l = (a - 1) % c, u = o, d = !0, f = function() {
			var t = r[m];
			if (t == null) return 0;
			var a = m, o, c = () => (o === void 0 && (o = n(t, a)), o), f = t.coordinate, p = m === l || oA(e, f, c, u, s);
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
function uA(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function dA(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? uA(Object(n), !0).forEach(function(t) {
			fA(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : uA(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function fA(e, t, n) {
	return (t = pA(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function pA(e) {
	var t = mA(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function mA(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function hA(e, t, n, r, i) {
	for (var a = (r || []).slice(), o = a.length, s = t.start, c = t.end, l = function(t) {
		var r = a[t];
		if (r == null) return 1;
		var l = r, u, d = () => (u === void 0 && (u = n(r, t)), u);
		if (t === o - 1) {
			var f = e * (l.coordinate + e * d() / 2 - c);
			a[t] = l = dA(dA({}, l), {}, { tickCoord: f > 0 ? l.coordinate - f * e : l.coordinate });
		} else a[t] = l = dA(dA({}, l), {}, { tickCoord: l.coordinate });
		l.tickCoord != null && oA(e, l.tickCoord, d, s, c) && (c = l.tickCoord - e * (d() / 2 + i), a[t] = dA(dA({}, l), {}, { isShow: !0 }));
	}, u = o - 1; u >= 0; u--) if (l(u)) continue;
	return a;
}
function gA(e, t, n, r, i, a) {
	var o = (r || []).slice(), s = o.length, c = t.start, l = t.end;
	if (a) {
		var u = r[s - 1];
		if (u != null) {
			var d = n(u, s - 1), f = e * (u.coordinate + e * d / 2 - l);
			o[s - 1] = u = dA(dA({}, u), {}, { tickCoord: f > 0 ? u.coordinate - f * e : u.coordinate }), u.tickCoord != null && oA(e, u.tickCoord, () => d, c, l) && (l = u.tickCoord - e * (d / 2 + i), o[s - 1] = dA(dA({}, u), {}, { isShow: !0 }));
		}
	}
	for (var p = a ? s - 1 : s, m = function(t) {
		var r = o[t];
		if (r == null) return 1;
		var a = r, s, u = () => (s === void 0 && (s = n(r, t)), s);
		if (t === 0) {
			var d = e * (a.coordinate - e * u() / 2 - c);
			o[t] = a = dA(dA({}, a), {}, { tickCoord: d < 0 ? a.coordinate - d * e : a.coordinate });
		} else o[t] = a = dA(dA({}, a), {}, { tickCoord: a.coordinate });
		a.tickCoord != null && oA(e, a.tickCoord, u, c, l) && (c = a.tickCoord + e * (u() / 2 + i), o[t] = dA(dA({}, a), {}, { isShow: !0 }));
	}, h = 0; h < p; h++) if (m(h)) continue;
	return o;
}
function _A(e, t, n) {
	var r = e.tick, i = e.ticks, a = e.viewBox, o = e.minTickGap, s = e.orientation, c = e.interval, l = e.tickFormatter, u = e.unit, d = e.angle;
	if (!i || !i.length || !r) return [];
	if (I(c) || tu.isSsr) {
		var f;
		return (f = sA(i, I(c) ? c : 0)) == null ? [] : f;
	}
	var p = [], m = s === "top" || s === "bottom" ? "width" : "height", h = u && m === "width" ? nE(u, {
		fontSize: t,
		letterSpacing: n
	}) : {
		width: 0,
		height: 0
	}, g = (e, r) => {
		var i = typeof l == "function" ? l(e.value, r) : e.value;
		return m === "width" ? iA(nE(i, {
			fontSize: t,
			letterSpacing: n
		}), h, d) : nE(i, {
			fontSize: t,
			letterSpacing: n
		})[m];
	}, _ = i[0], v = i[1], y = i.length >= 2 && _ != null && v != null ? Qt(v.coordinate - _.coordinate) : 1, b = aA(a, y, m);
	return c === "equidistantPreserveStart" ? cA(y, b, g, i, o) : c === "equidistantPreserveEnd" ? lA(y, b, g, i, o) : (p = c === "preserveStart" || c === "preserveStartEnd" ? gA(y, b, g, i, o, c === "preserveStartEnd") : hA(y, b, g, i, o), p.filter((e) => e.isShow));
}
//#endregion
//#region node_modules/recharts/es6/util/YAxisUtils.js
var vA = (e) => {
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
}, yA = H({
	name: "renderedTicks",
	initialState: {
		xAxis: {},
		yAxis: {}
	},
	reducers: {
		setRenderedTicks: (e, t) => {
			var n = t.payload, r = n.axisType, i = n.axisId, a = n.ticks;
			e[r][i] = B(a);
		},
		removeRenderedTicks: (e, t) => {
			var n = t.payload, r = n.axisType, i = n.axisId;
			delete e[r][i];
		}
	}
}), bA = yA.actions, xA = bA.setRenderedTicks, SA = bA.removeRenderedTicks, CA = yA.reducer, wA = [
	"axisLine",
	"width",
	"height",
	"className",
	"hide",
	"ticks",
	"axisType",
	"axisId"
];
function TA(e, t) {
	return AA(e) || kA(e, t) || DA(e, t) || EA();
}
function EA() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function DA(e, t) {
	if (e) {
		if (typeof e == "string") return OA(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? OA(e, t) : void 0;
	}
}
function OA(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function kA(e, t) {
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
function AA(e) {
	if (Array.isArray(e)) return e;
}
function jA(e, t) {
	if (e == null) return {};
	var n, r, i = MA(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function MA(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function NA() {
	return NA = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, NA.apply(null, arguments);
}
function PA(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function FA(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? PA(Object(n), !0).forEach(function(t) {
			IA(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : PA(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function IA(e, t, n) {
	return (t = LA(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function LA(e) {
	var t = RA(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function RA(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var zA = {
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
	zIndex: jp.axis
};
function BA(e) {
	var t = e.x, n = e.y, r = e.width, i = e.height, a = e.orientation, o = e.mirror, s = e.axisLine, c = e.otherSvgProps;
	if (!s) return null;
	var l = FA(FA(FA({}, c), ke(s)), {}, { fill: "none" });
	if (a === "top" || a === "bottom") {
		var u = +(a === "top" && !o || a === "bottom" && o);
		l = FA(FA({}, l), {}, {
			x1: t,
			y1: n + u * i,
			x2: t + r,
			y2: n + u * i
		});
	} else {
		var d = +(a === "left" && !o || a === "right" && o);
		l = FA(FA({}, l), {}, {
			x1: t + d * r,
			y1: n,
			x2: t + d * r,
			y2: n + i
		});
	}
	return /*#__PURE__*/ C.createElement("line", NA({}, l, { className: Ce("recharts-cartesian-axis-line", qt(s, "className")) }));
}
function VA(e, t, n, r, i, a, o, s, c) {
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
function HA(e, t) {
	switch (e) {
		case "left": return t ? "start" : "end";
		case "right": return t ? "end" : "start";
		default: return "middle";
	}
}
function UA(e, t) {
	switch (e) {
		case "left":
		case "right": return "middle";
		case "top": return t ? "start" : "end";
		default: return t ? "end" : "start";
	}
}
function WA(e) {
	var t = e.option, n = e.tickProps, r = e.value, i, a = Ce(n.className, "recharts-cartesian-axis-tick-value");
	if (/*#__PURE__*/ C.isValidElement(t)) i = /*#__PURE__*/ C.cloneElement(t, FA(FA({}, n), {}, { className: a }));
	else if (typeof t == "function") i = t(FA(FA({}, n), {}, { className: a }));
	else {
		var o = "recharts-cartesian-axis-tick-value";
		typeof t != "boolean" && (o = Ce(o, JD(t))), i = /*#__PURE__*/ C.createElement($E, NA({}, n, { className: o }), r);
	}
	return i;
}
function GA(e) {
	var t = e.ticks, n = e.axisType, r = e.axisId, i = Lr();
	return (0, C.useEffect)(() => r == null || n == null ? fn : (i(xA({
		ticks: t.map((e) => ({
			value: e.value,
			coordinate: e.coordinate,
			offset: e.offset,
			index: e.index
		})),
		axisId: r,
		axisType: n
	})), () => {
		i(SA({
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
var KA = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.ticks, r = n === void 0 ? [] : n, i = e.tick, a = e.tickLine, o = e.stroke, s = e.tickFormatter, c = e.unit, l = e.padding, u = e.tickTextProps, d = e.orientation, f = e.mirror, p = e.x, m = e.y, h = e.width, g = e.height, _ = e.tickSize, v = e.tickMargin, y = e.fontSize, b = e.letterSpacing, x = e.getTicksConfig, S = e.events, w = e.axisType, T = e.axisId, E = _A(FA(FA({}, x), {}, { ticks: r }), y, b), D = ke(x), O = Ae(i), k = HE(D.textAnchor) ? D.textAnchor : HA(d, f), A = UA(d, f), j = {};
	typeof a == "object" && (j = a);
	var M = FA(FA({}, D), {}, { fill: "none" }, j), N = E.map((e) => FA({ entry: e }, VA(e, p, m, h, g, d, _, f, v))), P = N.map((e) => {
		var t = e.entry, n = e.line;
		return /*#__PURE__*/ C.createElement(Ve, {
			className: "recharts-cartesian-axis-tick",
			key: `tick-${t.value}-${t.coordinate}-${t.tickCoord}`
		}, a && /*#__PURE__*/ C.createElement("line", NA({}, M, n, { className: Ce("recharts-cartesian-axis-tick-line", qt(a, "className")) })));
	}), ee = N.map((e, t) => {
		var n, r, a = e.entry, d = e.tick, f = FA(FA({}, FA(FA(FA(FA({ verticalAnchor: A }, D), {}, {
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
		return /*#__PURE__*/ C.createElement(Ve, NA({
			className: "recharts-cartesian-axis-tick-label",
			key: `tick-label-${a.value}-${a.coordinate}-${a.tickCoord}`
		}, gn(S, a, t)), i && /*#__PURE__*/ C.createElement(WA, {
			option: i,
			tickProps: f,
			value: `${typeof s == "function" ? s(a.value, t) : a.value}${c || ""}`
		}));
	});
	return /*#__PURE__*/ C.createElement("g", { className: `recharts-cartesian-axis-ticks recharts-${w}-ticks` }, /*#__PURE__*/ C.createElement(GA, {
		ticks: E,
		axisId: T,
		axisType: w
	}), ee.length > 0 && /*#__PURE__*/ C.createElement(Bw, { zIndex: jp.label }, /*#__PURE__*/ C.createElement("g", {
		className: `recharts-cartesian-axis-tick-labels recharts-${w}-tick-labels`,
		ref: t
	}, ee)), P.length > 0 && /*#__PURE__*/ C.createElement("g", { className: `recharts-cartesian-axis-tick-lines recharts-${w}-tick-lines` }, P));
}), qA = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.axisLine, r = e.width, i = e.height, a = e.className, o = e.hide, s = e.ticks, c = e.axisType, l = e.axisId, u = jA(e, wA), d = TA((0, C.useState)(""), 2), f = d[0], p = d[1], m = TA((0, C.useState)(""), 2), h = m[0], g = m[1], _ = (0, C.useRef)(null);
	(0, C.useImperativeHandle)(t, () => ({ getCalculatedWidth: () => {
		var t;
		return vA({
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
	return o || r != null && r <= 0 || i != null && i <= 0 ? null : /*#__PURE__*/ C.createElement(Bw, { zIndex: e.zIndex }, /*#__PURE__*/ C.createElement(Ve, { className: Ce("recharts-cartesian-axis", a) }, /*#__PURE__*/ C.createElement(BA, {
		x: e.x,
		y: e.y,
		width: r,
		height: i,
		orientation: e.orientation,
		mirror: e.mirror,
		axisLine: n,
		otherSvgProps: ke(e)
	}), /*#__PURE__*/ C.createElement(KA, {
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
	}), /*#__PURE__*/ C.createElement(_D, {
		x: e.x,
		y: e.y,
		width: e.width,
		height: e.height,
		lowerWidth: e.width,
		upperWidth: e.width
	}, /*#__PURE__*/ C.createElement(jD, {
		label: e.label,
		labelRef: e.labelRef
	}), e.children)));
}), JA = /*#__PURE__*/ C.forwardRef((e, t) => {
	var n = Sn(e, zA);
	return /*#__PURE__*/ C.createElement(qA, NA({}, n, { ref: t }));
});
JA.displayName = "CartesianAxis";
//#endregion
//#region node_modules/recharts/es6/state/errorBarSlice.js
var YA = H({
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
}), XA = YA.actions;
XA.addErrorBar, XA.replaceErrorBar, XA.removeErrorBar;
var ZA = YA.reducer, QA = ["children"];
function $A(e, t) {
	if (e == null) return {};
	var n, r, i = ej(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function ej(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var tj = /*#__PURE__*/ (0, C.createContext)({
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
function nj(e) {
	var t = e.children, n = $A(e, QA);
	return /*#__PURE__*/ C.createElement(tj.Provider, { value: n }, t);
}
//#endregion
//#region node_modules/recharts/es6/cartesian/GraphicalItemClipPath.js
function rj(e, t) {
	var n, r, i = L((t) => fb(t, e)), a = L((e) => hb(e, t)), o = (n = i == null ? void 0 : i.allowDataOverflow) == null ? ub.allowDataOverflow : n, s = (r = a == null ? void 0 : a.allowDataOverflow) == null ? pb.allowDataOverflow : r;
	return {
		needClip: o || s,
		needClipX: o,
		needClipY: s
	};
}
function ij(e) {
	var t = e.xAxisId, n = e.yAxisId, r = e.clipPathId, i = xk(), a = rj(t, n), o = a.needClipX, s = a.needClipY, c = a.needClip, l = L((e) => zx(e, t, !1)), u = L((e) => Bx(e, n, !1));
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
function aj(e, t) {
	var n, r;
	return (n = (r = e.graphicalItems.cartesianItems.find((e) => e.id === t)) == null ? void 0 : r.xAxisId) == null ? 0 : n;
}
function oj(e, t) {
	var n, r;
	return (n = (r = e.graphicalItems.cartesianItems.find((e) => e.id === t)) == null ? void 0 : r.yAxisId) == null ? 0 : n;
}
//#endregion
//#region node_modules/tiny-invariant/dist/esm/tiny-invariant.js
var sj = "Invariant failed";
function cj(e, t) {
	if (!e) throw Error(sj);
}
//#endregion
//#region node_modules/recharts/es6/util/BarUtils.js
var lj = ["option"];
function uj(e, t) {
	if (e == null) return {};
	var n, r, i = dj(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function dj(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var fj = lf;
function pj(e) {
	var t = e.option, n = uj(e, lj);
	return /*#__PURE__*/ C.createElement(fO, {
		option: t,
		DefaultShape: fj,
		shapeProps: n,
		activeClassName: "recharts-active-bar",
		inActiveClassName: "recharts-inactive-bar"
	});
}
var mj = function(e) {
	var t = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : 0;
	return (n, r) => {
		if (I(e)) return e;
		var i = I(n) || ln(n);
		return i ? e(n, r) : (!i && cj(!1, `minPointSize callback function received a value with type of ${typeof n}. Currently only numbers or null/undefined are supported.`), t);
	};
}, hj = (e, t, n) => n, gj = R([Cb, (e, t) => t], (e, t) => e.filter((e) => e.type === "bar").find((e) => e.id === t)), _j = R([gj], (e) => e == null ? void 0 : e.maxBarSize), vj = (e, t, n, r) => r, yj = R([
	K,
	Cb,
	aj,
	oj,
	hj
], (e, t, n, r, i) => t.filter((t) => e === "horizontal" ? t.xAxisId === n : t.yAxisId === r).filter((e) => e.isPanorama === i).filter((e) => e.hide === !1).filter((e) => e.type === "bar")), bj = (e, t, n) => {
	var r = K(e), i = aj(e, t), a = oj(e, t);
	if (!(i == null || a == null)) return r === "horizontal" ? Yb(e, "yAxis", a, n) : Yb(e, "xAxis", i, n);
}, xj = R([
	yj,
	wp,
	(e, t) => {
		var n = K(e), r = aj(e, t), i = oj(e, t);
		if (!(r == null || i == null)) return n === "horizontal" ? cS(e, "xAxis", r) : cS(e, "yAxis", i);
	}
], kk), Sj = (e, t, n) => {
	var r, i, a = gj(e, t);
	if (a == null) return 0;
	var o = aj(e, t), s = oj(e, t);
	if (o == null || s == null) return 0;
	var c = K(e), l = xp(e), u = a.maxBarSize, d = ln(u) ? l : u, f, p;
	return c === "horizontal" ? (f = pS(e, "xAxis", o, n), p = fS(e, "xAxis", o, n)) : (f = pS(e, "yAxis", s, n), p = fS(e, "yAxis", s, n)), (r = (i = Gs(f, p, !0)) == null ? d : i) == null ? 0 : r;
}, Cj = (e, t, n) => {
	var r = K(e), i = aj(e, t), a = oj(e, t);
	if (!(i == null || a == null)) {
		var o, s;
		return r === "horizontal" ? (o = pS(e, "xAxis", i, n), s = fS(e, "xAxis", i, n)) : (o = pS(e, "yAxis", a, n), s = fS(e, "yAxis", a, n)), Gs(o, s);
	}
}, wj = R([
	pc,
	hc,
	(e, t, n) => {
		var r = aj(e, t);
		if (r != null) return pS(e, "xAxis", r, n);
	},
	(e, t, n) => {
		var r = oj(e, t);
		if (r != null) return pS(e, "yAxis", r, n);
	},
	(e, t, n) => {
		var r = aj(e, t);
		if (r != null) return fS(e, "xAxis", r, n);
	},
	(e, t, n) => {
		var r = oj(e, t);
		if (r != null) return fS(e, "yAxis", r, n);
	},
	R([R([
		xj,
		xp,
		Sp,
		Cp,
		Sj,
		Cj,
		_j
	], Ik), gj], Rk),
	K,
	qf,
	Cj,
	R([bj, gj], Lk),
	gj,
	vj
], (e, t, n, r, i, a, o, s, c, l, u, d, f) => {
	var p = c.chartData, m = c.dataStartIndex, h = c.dataEndIndex;
	if (!(d == null || o == null || t == null || s !== "horizontal" && s !== "vertical" || n == null || r == null || i == null || a == null || l == null)) {
		var g = d.data, _ = g != null && g.length > 0 ? g : p == null ? void 0 : p.slice(m, h + 1);
		if (_ != null) return pM({
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
}), Tj = ["index"];
function Ej() {
	return Ej = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, Ej.apply(null, arguments);
}
function Dj(e, t) {
	if (e == null) return {};
	var n, r, i = Oj(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function Oj(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var kj = /*#__PURE__*/ (0, C.createContext)(void 0), Aj = (e) => {
	var t = (0, C.useContext)(kj);
	if (t != null) return t.stackId;
	if (e != null) return Ls(e);
}, jj = (e, t) => `recharts-bar-stack-clip-path-${e}-${t}`, Mj = (e) => {
	var t = (0, C.useContext)(kj);
	if (t != null) {
		var n = t.stackId;
		return `url(#${jj(n, e)})`;
	}
}, Nj = (e) => {
	var t = e.index, n = Dj(e, Tj), r = Mj(t);
	return /*#__PURE__*/ C.createElement(Ve, Ej({
		className: "recharts-bar-stack-layer",
		clipPath: r
	}, n));
}, Pj = [
	"onMouseEnter",
	"onMouseLeave",
	"onClick"
], Fj = [
	"value",
	"background",
	"tooltipPosition"
], Ij = ["id"], Lj = [
	"onMouseEnter",
	"onClick",
	"onMouseLeave"
];
function Rj(e, t) {
	return Uj(e) || Hj(e, t) || Bj(e, t) || zj();
}
function zj() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function Bj(e, t) {
	if (e) {
		if (typeof e == "string") return Vj(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? Vj(e, t) : void 0;
	}
}
function Vj(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function Hj(e, t) {
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
function Uj(e) {
	if (Array.isArray(e)) return e;
}
function Wj() {
	return Wj = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, Wj.apply(null, arguments);
}
function Gj(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Kj(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Gj(Object(n), !0).forEach(function(t) {
			qj(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Gj(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function qj(e, t, n) {
	return (t = Jj(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function Jj(e) {
	var t = Yj(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Yj(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function Xj(e, t) {
	if (e == null) return {};
	var n, r, i = Zj(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function Zj(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var Qj = (e) => {
	var t = e.dataKey, n = e.name, r = e.fill, i = e.legendType;
	return [{
		inactive: e.hide,
		dataKey: t,
		type: i,
		color: r,
		value: qs(n, t),
		payload: e
	}];
}, $j = /*#__PURE__*/ C.memo((e) => {
	var t = e.dataKey, n = e.stroke, r = e.strokeWidth, i = e.fill, a = e.name, o = e.hide, s = e.unit, c = e.formatter, l = e.tooltipType, u = e.id, d = {
		dataDefinedOnItem: void 0,
		getPosition: fn,
		settings: {
			stroke: n,
			strokeWidth: r,
			fill: i,
			dataKey: t,
			nameKey: void 0,
			name: qs(a, t),
			hide: o,
			type: l,
			color: i,
			unit: s,
			formatter: c,
			graphicalItemId: u
		}
	};
	return /*#__PURE__*/ C.createElement(gO, { tooltipEntrySettings: d });
});
function eM(e) {
	var t = L(IC), n = e.data, r = e.dataKey, i = e.background, a = e.allOtherBarProps, o = a.onMouseEnter, s = a.onMouseLeave, c = a.onClick, l = Xj(a, Pj), u = pO(o, r, a.id), d = mO(s), f = hO(c, r, a.id);
	if (!i || n == null) return null;
	var p = Ae(i);
	return /*#__PURE__*/ C.createElement(Bw, { zIndex: zk(i, jp.barBackground) }, n.map((e, n) => {
		e.value;
		var a = e.background;
		e.tooltipPosition;
		var o = Xj(e, Fj);
		if (!a) return null;
		var s = u(e, e.originalDataIndex), c = d(e, e.originalDataIndex), m = f(e, e.originalDataIndex), h = Kj(Kj(Kj(Kj(Kj({
			option: i,
			isActive: String(e.originalDataIndex) === t
		}, o), {}, { fill: "#eee" }, a), p), gn(l, e, n)), {}, {
			onMouseEnter: s,
			onMouseLeave: c,
			onClick: m,
			dataKey: r,
			index: n,
			className: "recharts-bar-background-rectangle"
		});
		return /*#__PURE__*/ C.createElement(pj, Wj({ key: `background-bar-${n}` }, h));
	}));
}
function tM(e) {
	var t = e.showLabels, n = e.children, r = e.rects, i = r == null ? void 0 : r.map((e) => {
		var t = {
			x: e.x,
			y: e.y,
			width: e.width,
			lowerWidth: e.width,
			upperWidth: e.width,
			height: e.height
		};
		return Kj(Kj({}, t), {}, {
			value: e.value,
			payload: e.payload,
			parentViewBox: e.parentViewBox,
			viewBox: t,
			fill: e.fill
		});
	});
	return /*#__PURE__*/ C.createElement(zD, { value: t ? i : void 0 }, n);
}
function nM(e) {
	var t = e.shape, n = e.activeBar, r = e.baseProps, i = e.entry, a = e.index, o = e.dataKey, s = L(IC), c = L(RC), l = n && String(i.originalDataIndex) === s && (c == null || o === c), u = Rj((0, C.useState)(!1), 2), d = u[0], f = u[1], p = Rj((0, C.useState)(!1), 2), m = p[0], h = p[1];
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
	}, [l]), _ = l && m, v = l || d, y = l ? n === !0 ? t : n : t, b = /*#__PURE__*/ C.createElement(pj, Wj({}, r, { name: String(r.name) }, i, {
		isActive: _,
		option: y,
		index: a,
		dataKey: o,
		animationElapsedTime: e.animationElapsedTime,
		isAnimating: e.isAnimating,
		isEntrance: e.isEntrance,
		onTransitionEnd: g
	}));
	return v ? /*#__PURE__*/ C.createElement(Bw, { zIndex: jp.activeBar }, /*#__PURE__*/ C.createElement(Nj, { index: i.originalDataIndex }, b)) : b;
}
function rM(e) {
	var t = e.shape, n = e.baseProps, r = e.entry, i = e.index, a = e.dataKey;
	return /*#__PURE__*/ C.createElement(pj, Wj({}, n, { name: String(n.name) }, r, {
		isActive: !1,
		option: t,
		index: i,
		dataKey: a,
		animationElapsedTime: e.animationElapsedTime,
		isAnimating: e.isAnimating,
		isEntrance: e.isEntrance
	}));
}
function iM(e) {
	var t, n = e.data, r = e.props, i = e.animationElapsedTime, a = e.isAnimating, o = e.isEntrance, s = (t = ke(r)) == null ? {} : t, c = s.id, l = Xj(s, Ij), u = r.shape, d = r.dataKey, f = r.activeBar, p = r.onMouseEnter, m = r.onClick, h = r.onMouseLeave, g = Xj(r, Lj), _ = pO(p, d, c), v = mO(h), y = hO(m, d, c);
	return n ? /*#__PURE__*/ C.createElement(C.Fragment, null, n.map((e, t) => /*#__PURE__*/ C.createElement(Nj, Wj({
		index: e.originalDataIndex,
		key: `rectangle-${e == null ? void 0 : e.x}-${e == null ? void 0 : e.y}-${e == null ? void 0 : e.value}-${t}`,
		className: "recharts-bar-rectangle"
	}, gn(g, e, t), {
		onMouseEnter: _(e, e.originalDataIndex),
		onMouseLeave: v(e, e.originalDataIndex),
		onClick: y(e, e.originalDataIndex)
	}), f ? /*#__PURE__*/ C.createElement(nM, {
		shape: u,
		activeBar: f,
		baseProps: l,
		entry: e,
		index: t,
		dataKey: d,
		animationElapsedTime: i,
		isAnimating: a,
		isEntrance: o
	}) : /*#__PURE__*/ C.createElement(rM, {
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
var aM = (e, t, n) => e == null ? [] : t === 1 ? e.flatMap((e) => e.status === "removed" ? [] : [e.next]) : e.flatMap((e) => {
	if (e.status === "removed") return n === "horizontal" ? [Kj(Kj({}, e.prev), {}, {
		height: sn(e.prev.height, 0, t),
		y: sn(e.prev.y, e.prev.y + e.prev.height, t)
	})] : [Kj(Kj({}, e.prev), {}, { width: sn(e.prev.width, 0, t) })];
	if (e.status === "matched") return [Kj(Kj({}, e.next), {}, {
		x: sn(e.prev.x, e.next.x, t),
		y: sn(e.prev.y, e.next.y, t),
		width: sn(e.prev.width, e.next.width, t),
		height: sn(e.prev.height, e.next.height, t)
	})];
	var r = e.next;
	return n === "horizontal" ? [Kj(Kj({}, r), {}, {
		height: sn(0, r.height, t),
		y: sn(r.stackedBarStart, r.y, t)
	})] : [Kj(Kj({}, r), {}, {
		width: sn(0, r.width, t),
		x: sn(r.stackedBarStart, r.x, t)
	})];
});
function oM(e) {
	var t = e.props, n = e.previousRectanglesRef, r = t.data, i = t.isAnimationActive, a = t.animationBegin, o = t.animationDuration, s = t.animationEasing, c = t.animationInterpolateFn, l = t.layout, u = zO(t.onAnimationStart, t.onAnimationEnd), d = u.isAnimating, f = u.handleAnimationStart, p = u.handleAnimationEnd;
	return /*#__PURE__*/ C.createElement(tM, {
		showLabels: !d,
		rects: r
	}, /*#__PURE__*/ C.createElement(BO, {
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
	}, (e, n, r) => /*#__PURE__*/ C.createElement(Ve, null, /*#__PURE__*/ C.createElement(iM, {
		props: t,
		data: e,
		animationElapsedTime: n,
		isAnimating: d || n < 1,
		isEntrance: r
	}))), /*#__PURE__*/ C.createElement(WD, { label: t.label }), t.children);
}
function sM(e) {
	var t = (0, C.useRef)(null);
	return /*#__PURE__*/ C.createElement(oM, {
		previousRectanglesRef: t,
		props: e
	});
}
var cM = 0, lM = (e, t) => {
	var n = Array.isArray(e.value) ? e.value[1] : e.value;
	return {
		x: e.x,
		y: e.y,
		value: n,
		errorVal: js(e, t)
	};
}, uM = class extends C.PureComponent {
	render() {
		var e = this.props, t = e.hide, n = e.data, r = e.dataKey, i = e.className, a = e.xAxisId, o = e.yAxisId, s = e.needClip, c = e.background, l = e.id;
		if (t || n == null) return null;
		var u = Ce("recharts-bar", i), d = l;
		return /*#__PURE__*/ C.createElement(Ve, {
			className: u,
			id: l
		}, s && /*#__PURE__*/ C.createElement("defs", null, /*#__PURE__*/ C.createElement(ij, {
			clipPathId: d,
			xAxisId: a,
			yAxisId: o
		})), /*#__PURE__*/ C.createElement(Ve, {
			className: "recharts-bar-rectangles",
			clipPath: s ? `url(#clipPath-${d})` : void 0
		}, /*#__PURE__*/ C.createElement(eM, {
			data: n,
			dataKey: r,
			background: c,
			allOtherBarProps: this.props
		}), /*#__PURE__*/ C.createElement(sM, this.props)));
	}
}, dM = {
	activeBar: !1,
	animationBegin: 0,
	animationDuration: 400,
	animationEasing: "ease",
	animationInterpolateFn: aM,
	animationMatchBy: TO,
	background: !1,
	hide: !1,
	isAnimationActive: "auto",
	label: !1,
	legendType: "rect",
	minPointSize: cM,
	shape: fj,
	xAxisId: 0,
	yAxisId: 0,
	zIndex: jp.bar
};
function fM(e) {
	var t = e.xAxisId, n = e.yAxisId, r = e.hide, i = e.legendType, a = e.minPointSize, o = e.activeBar, s = e.animationBegin, c = e.animationDuration, l = e.animationEasing, u = e.isAnimationActive, d = rj(t, n).needClip, f = rl(), p = _c(), m = tO(e.children, BT), h = L((t) => wj(t, e.id, p, m));
	if (f !== "vertical" && f !== "horizontal") return null;
	var g, _ = h == null ? void 0 : h[0];
	return g = _ == null || _.height == null || _.width == null ? 0 : f === "vertical" ? _.height / 2 : _.width / 2, /*#__PURE__*/ C.createElement(nj, {
		xAxisId: t,
		yAxisId: n,
		data: h,
		dataPointFormatter: lM,
		errorBarOffset: g
	}, /*#__PURE__*/ C.createElement(uM, Wj({}, e, {
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
function pM(e) {
	var t = e.layout, n = e.barSettings, r = n.dataKey, i = n.minPointSize, a = n.hasCustomShape, o = e.pos, s = e.bandSize, c = e.xAxis, l = e.yAxis, u = e.xAxisTicks, d = e.yAxisTicks, f = e.stackedData, p = e.displayedData, m = e.offset, h = e.cells, g = e.parentViewBox, _ = e.dataStartIndex, v = t === "horizontal" ? l : c, y = f ? v.scale.domain() : null, b = zs({ numericAxis: v }), x = v.scale.map(b);
	return p.map((e, n) => {
		var p, v, S, C, w, T;
		if (f) {
			var E = f[n + _];
			if (E == null) return null;
			p = Ps(E, y);
		} else p = js(e, r), Array.isArray(p) || (p = [b, p]);
		var D = mj(i, cM)(p[1], n);
		if (t === "horizontal") {
			var O, k = l.scale.map(p[0]), A = l.scale.map(p[1]);
			if (k == null || A == null) return null;
			v = Rs({
				axis: c,
				ticks: u,
				bandSize: s,
				offset: o.offset,
				entry: e,
				index: n
			}), S = (O = A == null ? k : A) == null ? void 0 : O, C = o.size;
			var j = k - A;
			if (w = $t(j) ? 0 : j, T = {
				x: v,
				y: m.top,
				width: C,
				height: m.height
			}, Math.abs(D) > 0 && Math.abs(w) < Math.abs(D)) {
				var M = Qt(w || D) * (Math.abs(D) - Math.abs(w));
				S -= M, w += M;
			}
		} else {
			var N = c.scale.map(p[0]), P = c.scale.map(p[1]);
			if (N == null || P == null) return null;
			if (v = N, S = Rs({
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
				var ee = Qt(C || D) * (Math.abs(D) - Math.abs(C));
				C += ee;
			}
		}
		return v == null || S == null || C == null || w == null || !a && (C === 0 || w === 0) ? null : Kj(Kj({}, e), {}, {
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
function mM(e) {
	var t = Sn(e, dM), n = Aj(t.stackId), r = _c();
	return /*#__PURE__*/ C.createElement(ZO, {
		id: t.id,
		type: "bar"
	}, (e) => /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(_O, { legendPayload: Qj(t) }), /*#__PURE__*/ C.createElement($j, {
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
	}), /*#__PURE__*/ C.createElement(ik, {
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
		hasCustomShape: t.shape != null && t.shape !== fj
	}), /*#__PURE__*/ C.createElement(Bw, { zIndex: t.zIndex }, /*#__PURE__*/ C.createElement(fM, Wj({}, t, { id: e })))));
}
var hM = /*#__PURE__*/ C.memo(mM, Ml);
hM.displayName = "Bar";
//#endregion
//#region node_modules/recharts/es6/util/axisPropsAreEqual.js
var gM = ["domain", "range"], _M = ["domain", "range"];
function vM(e, t) {
	if (e == null) return {};
	var n, r, i = yM(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function yM(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function bM(e, t) {
	return e === t ? !0 : Array.isArray(e) && e.length === 2 && Array.isArray(t) && t.length === 2 ? e[0] === t[0] && e[1] === t[1] : !1;
}
function xM(e, t) {
	if (e === t) return !0;
	var n = e.domain, r = e.range, i = vM(e, gM), a = t.domain, o = t.range, s = vM(t, _M);
	return !bM(n, a) || !bM(r, o) ? !1 : Ml(i, s);
}
//#endregion
//#region node_modules/recharts/es6/cartesian/XAxis.js
var SM = ["type"], CM = [
	"dangerouslySetInnerHTML",
	"ticks",
	"scale"
], wM = ["id", "scale"];
function TM() {
	return TM = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, TM.apply(null, arguments);
}
function EM(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function DM(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? EM(Object(n), !0).forEach(function(t) {
			OM(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : EM(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function OM(e, t, n) {
	return (t = kM(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function kM(e) {
	var t = AM(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function AM(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function jM(e, t) {
	if (e == null) return {};
	var n, r, i = MM(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function MM(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function NM(e) {
	var t = Lr(), n = (0, C.useRef)(null), r = il(), i = e.type, a = jM(e, SM), o = Fp(r, "xAxis", i), s = (0, C.useMemo)(() => {
		if (o != null) return DM(DM({}, a), {}, { type: o });
	}, [a, o]);
	return (0, C.useLayoutEffect)(() => {
		s != null && (n.current === null ? t(fk(s)) : n.current !== s && t(pk({
			prev: n.current,
			next: s
		})), n.current = s);
	}, [s, t]), (0, C.useLayoutEffect)(() => () => {
		n.current && (t(mk(n.current)), n.current = null);
	}, [t]), null;
}
var PM = (e) => {
	var t = e.xAxisId, n = e.className, r = L(hc), i = _c(), a = "xAxis", o = L((e) => dS(e, a, t, i)), s = L((e) => eS(e, t)), c = L((e) => aS(e, t)), l = L((e) => db(e, t));
	if (s == null || c == null || l == null) return null;
	e.dangerouslySetInnerHTML, e.ticks, e.scale;
	var u = jM(e, CM);
	l.id, l.scale;
	var d = jM(l, wM);
	return /*#__PURE__*/ C.createElement(JA, TM({}, u, d, {
		x: c.x,
		y: c.y,
		width: s.width,
		height: s.height,
		className: Ce(`recharts-${a} ${a}`, n),
		viewBox: r,
		ticks: o,
		axisType: a,
		axisId: t
	}));
}, FM = {
	allowDataOverflow: ub.allowDataOverflow,
	allowDecimals: ub.allowDecimals,
	allowDuplicatedCategory: ub.allowDuplicatedCategory,
	angle: ub.angle,
	axisLine: zA.axisLine,
	height: ub.height,
	hide: !1,
	includeHidden: ub.includeHidden,
	interval: ub.interval,
	label: !1,
	minTickGap: ub.minTickGap,
	mirror: ub.mirror,
	orientation: ub.orientation,
	padding: ub.padding,
	reversed: ub.reversed,
	scale: ub.scale,
	tick: ub.tick,
	tickCount: ub.tickCount,
	tickLine: zA.tickLine,
	tickSize: zA.tickSize,
	type: ub.type,
	niceTicks: ub.niceTicks,
	xAxisId: 0
}, IM = /*#__PURE__*/ C.memo((e) => {
	var t = Sn(e, FM);
	return /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(NM, {
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
	}), /*#__PURE__*/ C.createElement(PM, t));
}, xM);
IM.displayName = "XAxis";
//#endregion
//#region node_modules/recharts/es6/cartesian/YAxis.js
var LM = ["type"], RM = [
	"dangerouslySetInnerHTML",
	"ticks",
	"scale"
], zM = ["id", "scale"];
function BM() {
	return BM = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, BM.apply(null, arguments);
}
function VM(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function HM(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? VM(Object(n), !0).forEach(function(t) {
			UM(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : VM(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function UM(e, t, n) {
	return (t = WM(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function WM(e) {
	var t = GM(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function GM(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function KM(e, t) {
	if (e == null) return {};
	var n, r, i = qM(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function qM(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function JM(e) {
	var t = Lr(), n = (0, C.useRef)(null), r = il(), i = e.type, a = KM(e, LM), o = Fp(r, "yAxis", i), s = (0, C.useMemo)(() => {
		if (o != null) return HM(HM({}, a), {}, { type: o });
	}, [o, a]);
	return (0, C.useLayoutEffect)(() => {
		s != null && (n.current === null ? t(hk(s)) : n.current !== s && t(gk({
			prev: n.current,
			next: s
		})), n.current = s);
	}, [s, t]), (0, C.useLayoutEffect)(() => () => {
		n.current && (t(_k(n.current)), n.current = null);
	}, [t]), null;
}
function YM(e) {
	var t = e.yAxisId, n = e.className, r = e.width, i = e.label, a = (0, C.useRef)(null), o = (0, C.useRef)(null), s = L(hc), c = _c(), l = Lr(), u = "yAxis", d = L((e) => sS(e, t)), f = L((e) => oS(e, t)), p = L((e) => dS(e, u, t, c)), m = L((e) => mb(e, t));
	if ((0, C.useLayoutEffect)(() => {
		if (!(r !== "auto" || !d || SD(i) || /*#__PURE__*/ (0, C.isValidElement)(i) || m == null)) {
			var e = a.current;
			if (e) {
				var n = e.getCalculatedWidth();
				Math.round(d.width) !== Math.round(n) && l(vk({
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
	var h = KM(e, RM);
	m.id, m.scale;
	var g = KM(m, zM);
	return /*#__PURE__*/ C.createElement(JA, BM({}, h, g, {
		ref: a,
		labelRef: o,
		x: f.x,
		y: f.y,
		tickTextProps: r === "auto" ? { width: void 0 } : { width: r },
		width: d.width,
		height: d.height,
		className: Ce(`recharts-${u} ${u}`, n),
		viewBox: s,
		ticks: p,
		axisType: u,
		axisId: t
	}));
}
var XM = {
	allowDataOverflow: pb.allowDataOverflow,
	allowDecimals: pb.allowDecimals,
	allowDuplicatedCategory: pb.allowDuplicatedCategory,
	angle: pb.angle,
	axisLine: zA.axisLine,
	hide: !1,
	includeHidden: pb.includeHidden,
	interval: pb.interval,
	label: !1,
	minTickGap: pb.minTickGap,
	mirror: pb.mirror,
	orientation: pb.orientation,
	padding: pb.padding,
	reversed: pb.reversed,
	scale: pb.scale,
	tick: pb.tick,
	tickCount: pb.tickCount,
	tickLine: zA.tickLine,
	tickSize: zA.tickSize,
	type: pb.type,
	niceTicks: pb.niceTicks,
	width: pb.width,
	yAxisId: 0
}, ZM = /*#__PURE__*/ C.memo((e) => {
	var t = Sn(e, XM);
	return /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(JM, {
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
	}), /*#__PURE__*/ C.createElement(YM, t));
}, xM);
ZM.displayName = "YAxis";
var QM = R([
	(e, t) => t,
	K,
	Zp,
	om,
	kC,
	jC,
	lw,
	pc
], xw);
//#endregion
//#region node_modules/recharts/es6/util/getRelativeCoordinate.js
function $M(e) {
	return "getBBox" in e.currentTarget && typeof e.currentTarget.getBBox == "function";
}
function eN(e) {
	var t = e.currentTarget.getBoundingClientRect(), n, r;
	if ($M(e)) {
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
var tN = co("mouseClick"), nN = hs();
nN.startListening({
	actionCreator: tN,
	effect: (e, t) => {
		var n = e.payload, r = QM(t.getState(), eN(n));
		(r == null ? void 0 : r.activeIndex) != null && t.dispatch(PS({
			activeIndex: r.activeIndex,
			activeDataKey: void 0,
			activeCoordinate: r.activeCoordinate
		}));
	}
});
var rN = co("mouseMove"), iN = hs(), aN = null, oN = null, sN = null;
iN.startListening({
	actionCreator: rN,
	effect: (e, t) => {
		var n = e.payload, r = t.getState().eventSettings, i = r.throttleDelay, a = r.throttledEvents, o = a === "all" || (a == null ? void 0 : a.includes("mousemove"));
		aN !== null && (cancelAnimationFrame(aN), aN = null), oN !== null && (typeof i != "number" || !o) && (clearTimeout(oN), oN = null), sN = eN(n);
		var s = () => {
			var e = t.getState(), n = vS(e, e.tooltip.settings.shared);
			if (!sN) {
				aN = null, oN = null;
				return;
			}
			if (n === "axis") {
				var r = QM(e, sN);
				(r == null ? void 0 : r.activeIndex) == null ? t.dispatch(jS()) : t.dispatch(NS({
					activeIndex: r.activeIndex,
					activeDataKey: void 0,
					activeCoordinate: r.activeCoordinate
				}));
			}
			aN = null, oN = null;
		};
		if (!o) {
			s();
			return;
		}
		i === "raf" ? aN = requestAnimationFrame(s) : typeof i == "number" && oN === null && (oN = setTimeout(s, i));
	}
});
//#endregion
//#region node_modules/recharts/es6/state/reduxDevtoolsJsonStringifyReplacer.js
function cN(e, t) {
	return t instanceof HTMLElement ? `HTMLElement <${t.tagName} class="${t.className}">` : t === window ? "global.window" : e === "children" && typeof t == "object" && t ? "<<CHILDREN>>" : t;
}
//#endregion
//#region node_modules/recharts/es6/state/rootPropsSlice.js
var lN = {
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
}, uN = H({
	name: "rootProps",
	initialState: lN,
	reducers: { updateOptions: (e, t) => {
		var n;
		e.accessibilityLayer = t.payload.accessibilityLayer, e.barCategoryGap = t.payload.barCategoryGap, e.barGap = (n = t.payload.barGap) == null ? lN.barGap : n, e.barSize = t.payload.barSize, e.maxBarSize = t.payload.maxBarSize, e.stackOffset = t.payload.stackOffset, e.syncId = t.payload.syncId, e.syncMethod = t.payload.syncMethod, e.className = t.payload.className, e.baseValue = t.payload.baseValue, e.reverseStackOrder = t.payload.reverseStackOrder;
	} }
}), dN = uN.reducer, fN = uN.actions.updateOptions, pN = H({
	name: "polarOptions",
	initialState: null,
	reducers: { updatePolarOptions: (e, t) => e === null ? t.payload : (e.startAngle = t.payload.startAngle, e.endAngle = t.payload.endAngle, e.cx = t.payload.cx, e.cy = t.payload.cy, e.innerRadius = t.payload.innerRadius, e.outerRadius = t.payload.outerRadius, e) }
});
pN.actions.updatePolarOptions;
var mN = pN.reducer, hN = co("keyDown"), gN = co("focus"), _N = co("blur"), vN = hs(), yN = null, bN = null, xN = null;
vN.startListening({
	actionCreator: hN,
	effect: (e, t) => {
		xN = e.payload, yN !== null && (cancelAnimationFrame(yN), yN = null);
		var n = t.getState().eventSettings, r = n.throttleDelay, i = n.throttledEvents, a = i === "all" || i.includes("keydown");
		bN !== null && (typeof r != "number" || !a) && (clearTimeout(bN), bN = null);
		var o = () => {
			try {
				var e = t.getState();
				if (e.rootProps.accessibilityLayer === !1) return;
				var n = e.tooltip.keyboardInteraction, r = xN;
				if (r !== "ArrowRight" && r !== "ArrowLeft" && r !== "Enter") return;
				var i = YS(n, _C(e), Kb(e), EC(e)), a = i == null ? -1 : Number(i), o = !Number.isFinite(a) || a < 0, s = jC(e), c = _C(e), l = vS(e, e.tooltip.settings.shared);
				if (r === "Enter") {
					if (o) return;
					var u = mw(e, l, "hover", String(n.index));
					t.dispatch(IS({
						active: !n.active,
						activeIndex: n.index,
						activeCoordinate: u
					}));
					return;
				}
				var d = mS(e) === "left-to-right" ? 1 : -1, f = r === "ArrowRight" ? 1 : -1, p;
				if (o) {
					var m = Kb(e), h = EC(e), g = f * d, _ = (e) => ({
						active: !1,
						index: String(e),
						dataKey: void 0,
						graphicalItemId: void 0,
						coordinate: void 0
					});
					if (p = -1, g > 0) {
						for (var v = 0; v < c.length; v++) if (YS(_(v), c, m, h) != null) {
							p = v;
							break;
						}
					} else for (var y = c.length - 1; y >= 0; y--) if (YS(_(y), c, m, h) != null) {
						p = y;
						break;
					}
					if (p < 0) return;
				} else {
					p = a + f * d;
					var b = (s == null ? void 0 : s.length) || c.length;
					if (b === 0 || p >= b || p < 0) return;
				}
				var x = mw(e, l, "hover", String(p));
				t.dispatch(IS({
					active: !0,
					activeIndex: p.toString(),
					activeCoordinate: x
				}));
			} finally {
				yN = null, bN = null;
			}
		};
		if (!a) {
			o();
			return;
		}
		r === "raf" ? yN = requestAnimationFrame(o) : typeof r == "number" && bN === null && (o(), xN = null, bN = setTimeout(() => {
			xN ? o() : (bN = null, yN = null);
		}, r));
	}
}), vN.startListening({
	actionCreator: gN,
	effect: (e, t) => {
		var n = t.getState();
		if (n.rootProps.accessibilityLayer !== !1) {
			var r = n.tooltip.keyboardInteraction;
			if (!r.active && r.index == null) {
				var i = "0", a = mw(n, vS(n, n.tooltip.settings.shared), "hover", String(i));
				t.dispatch(IS({
					active: !0,
					activeIndex: i,
					activeCoordinate: a
				}));
			}
		}
	}
}), vN.startListening({
	actionCreator: _N,
	effect: (e, t) => {
		var n = t.getState();
		if (n.rootProps.accessibilityLayer !== !1) {
			var r = n.tooltip.keyboardInteraction;
			r.active && t.dispatch(IS({
				active: !1,
				activeIndex: r.index,
				activeCoordinate: r.coordinate
			}));
		}
	}
});
//#endregion
//#region node_modules/recharts/es6/util/createEventProxy.js
function SN(e) {
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
var CN = co("externalEvent"), wN = hs(), TN = /* @__PURE__ */ new Map(), EN = /* @__PURE__ */ new Map(), DN = /* @__PURE__ */ new Map();
wN.startListening({
	actionCreator: CN,
	effect: (e, t) => {
		var n = e.payload, r = n.handler, i = n.reactEvent;
		if (r != null) {
			var a = i.type, o = SN(i);
			DN.set(a, {
				handler: r,
				reactEvent: o
			});
			var s = TN.get(a);
			s !== void 0 && (cancelAnimationFrame(s), TN.delete(a));
			var c = t.getState().eventSettings, l = c.throttleDelay, u = c.throttledEvents, d = u === "all" || (u == null ? void 0 : u.includes(a)), f = EN.get(a);
			f !== void 0 && (typeof l != "number" || !d) && (clearTimeout(f), EN.delete(a));
			var p = () => {
				var e = DN.get(a);
				try {
					if (!e) return;
					var n = e.handler, r = e.reactEvent, i = t.getState(), o = {
						activeCoordinate: VC(i),
						activeDataKey: RC(i),
						activeIndex: IC(i),
						activeLabel: LC(i),
						activeTooltipIndex: IC(i),
						isTooltipActive: HC(i)
					};
					n && n(o, r);
				} finally {
					TN.delete(a), EN.delete(a), DN.delete(a);
				}
			};
			if (!d) {
				p();
				return;
			}
			if (l === "raf") {
				var m = requestAnimationFrame(p);
				TN.set(a, m);
			} else if (typeof l == "number") {
				if (!EN.has(a)) {
					p();
					var h = setTimeout(p, l);
					EN.set(a, h);
				}
			} else p();
		}
	}
});
var ON = R([
	R([$S], (e) => e.tooltipItemPayloads),
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
}), kN = co("touchMove"), AN = hs(), jN = null, MN = null, NN = null, PN = null;
AN.startListening({
	actionCreator: kN,
	effect: (e, t) => {
		var n = e.payload;
		if (!(n.touches == null || n.touches.length === 0)) {
			PN = SN(n);
			var r = t.getState().eventSettings, i = r.throttleDelay, a = r.throttledEvents, o = a === "all" || a.includes("touchmove");
			jN !== null && (cancelAnimationFrame(jN), jN = null), MN !== null && (typeof i != "number" || !o) && (clearTimeout(MN), MN = null), NN = Array.from(n.touches).map((e) => eN({
				clientX: e.clientX,
				clientY: e.clientY,
				currentTarget: n.currentTarget
			}));
			var s = () => {
				if (PN != null) {
					var e = t.getState(), n = vS(e, e.tooltip.settings.shared);
					if (n === "axis") {
						var r, i = (r = NN) == null ? void 0 : r[0];
						if (i == null) {
							jN = null, MN = null;
							return;
						}
						var a = QM(e, i);
						(a == null ? void 0 : a.activeIndex) != null && t.dispatch(NS({
							activeIndex: a.activeIndex,
							activeDataKey: void 0,
							activeCoordinate: a.activeCoordinate
						}));
					} else if (n === "item") {
						var o, s = PN.touches[0];
						if (document.elementFromPoint == null || s == null) return;
						var c = document.elementFromPoint(s.clientX, s.clientY);
						if (!c || !c.getAttribute) return;
						var l = c.getAttribute(nc), u = (o = c.getAttribute("data-recharts-item-id")) == null ? void 0 : o, d = pC(e).find((e) => e.id === u);
						if (l == null || d == null || u == null) return;
						var f = d.dataKey, p = ON(e, l, u);
						t.dispatch(kS({
							activeDataKey: f,
							activeIndex: l,
							activeCoordinate: p,
							activeGraphicalItemId: u
						}));
					}
					jN = null, MN = null;
				}
			};
			if (!o) {
				s();
				return;
			}
			i === "raf" ? jN = requestAnimationFrame(s) : typeof i == "number" && MN === null && (s(), PN = null, MN = setTimeout(() => {
				PN ? s() : (MN = null, jN = null);
			}, i));
		}
	}
});
//#endregion
//#region node_modules/recharts/es6/state/eventSettingsSlice.js
var FN = {
	throttleDelay: "raf",
	throttledEvents: [
		"mousemove",
		"touchmove",
		"pointermove",
		"scroll",
		"wheel"
	]
}, IN = H({
	name: "eventSettings",
	initialState: FN,
	reducers: { setEventSettings: (e, t) => {
		t.payload.throttleDelay != null && (e.throttleDelay = t.payload.throttleDelay), t.payload.throttledEvents != null && (e.throttledEvents = B(t.payload.throttledEvents));
	} }
}), LN = IN.actions.setEventSettings, RN = IN.reducer, zN = Ni({
	brush: Uk,
	cartesianAxis: yk,
	chartData: dT,
	errorBars: ZA,
	eventSettings: RN,
	graphicalItems: rk,
	layout: Cs,
	legend: pl,
	options: iT,
	polarAxis: qD,
	polarOptions: mN,
	referenceElements: Jk,
	renderedTicks: CA,
	rootProps: dN,
	tooltip: LS,
	zIndex: Rw
}), BN = function(e) {
	var t = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : "Chart";
	return bo({
		reducer: zN,
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
				nN.middleware,
				iN.middleware,
				vN.middleware,
				wN.middleware,
				AN.middleware
			]);
		},
		enhancers: (e) => {
			var t = e;
			return typeof e == "function" && (t = e()), t.concat(vo({ type: "raf" }));
		},
		devTools: tu.devToolsEnabled && {
			serialize: { replacer: cN },
			name: `recharts-${t}`
		}
	});
};
//#endregion
//#region node_modules/recharts/es6/state/RechartsStoreProvider.js
function VN(e) {
	var t = e.preloadedState, n = e.children, r = e.reduxStoreName, i = _c(), a = (0, C.useRef)(null);
	if (i) return n;
	a.current == null && (a.current = BN(t, r));
	var o = Pr;
	return /*#__PURE__*/ C.createElement(kl, {
		context: o,
		store: a.current
	}, n);
}
//#endregion
//#region node_modules/recharts/es6/state/ReportMainChartProps.js
function HN(e) {
	var t = e.layout, n = e.margin, r = Lr(), i = _c();
	return (0, C.useEffect)(() => {
		i || (r(bs(t)), r(ys(n)));
	}, [
		r,
		i,
		t,
		n
	]), null;
}
var UN = /*#__PURE__*/ (0, C.memo)(HN, Ml);
//#endregion
//#region node_modules/recharts/es6/state/ReportChartProps.js
function WN(e) {
	var t = Lr();
	return (0, C.useEffect)(() => {
		t(fN(e));
	}, [t, e]), null;
}
var GN = /*#__PURE__*/ (0, C.memo)((e) => {
	var t = Lr();
	return (0, C.useEffect)(() => {
		t(LN(e));
	}, [t, e]), null;
}, Ml);
//#endregion
//#region node_modules/recharts/es6/zIndex/ZIndexPortal.js
function KN(e) {
	var t = e.zIndex, n = e.isPanorama, r = (0, C.useRef)(null), i = Lr();
	return (0, C.useLayoutEffect)(() => (r.current && i(Iw({
		zIndex: t,
		element: r.current,
		isPanorama: n
	})), () => {
		i(Lw({
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
function qN(e) {
	var t = e.children, n = e.isPanorama, r = L(Cw);
	if (!r || r.length === 0) return t;
	var i = r.filter((e) => e < 0), a = r.filter((e) => e > 0);
	return /*#__PURE__*/ C.createElement(C.Fragment, null, i.map((e) => /*#__PURE__*/ C.createElement(KN, {
		key: e,
		zIndex: e,
		isPanorama: n
	})), t, a.map((e) => /*#__PURE__*/ C.createElement(KN, {
		key: e,
		zIndex: e,
		isPanorama: n
	})));
}
//#endregion
//#region node_modules/recharts/es6/container/RootSurface.js
var JN = ["children"];
function YN(e, t) {
	if (e == null) return {};
	var n, r, i = XN(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function XN(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function ZN() {
	return ZN = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, ZN.apply(null, arguments);
}
var QN = {
	width: "100%",
	height: "100%",
	display: "block"
}, $N = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = tl(), r = nl(), i = Cu();
	if (!Ts(n) || !Ts(r)) return null;
	var a = e.children, o = e.otherAttributes, s = e.title, c = e.desc, l, u;
	return o != null && (l = typeof o.tabIndex == "number" ? o.tabIndex : i ? 0 : void 0, u = typeof o.role == "string" ? o.role : i ? "application" : void 0), /*#__PURE__*/ C.createElement(Ie, ZN({}, o, {
		title: s,
		desc: c,
		role: u,
		tabIndex: l,
		width: n,
		height: r,
		style: QN,
		ref: t
	}), a);
}), eP = (e) => {
	var t = e.children, n = L(yc);
	if (!n) return null;
	var r = n.width, i = n.height, a = n.y, o = n.x;
	return /*#__PURE__*/ C.createElement(Ie, {
		width: r,
		height: i,
		x: o,
		y: a
	}, t);
}, tP = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.children, r = YN(e, JN);
	return _c() ? /*#__PURE__*/ C.createElement(eP, null, /*#__PURE__*/ C.createElement(qN, { isPanorama: !0 }, n)) : /*#__PURE__*/ C.createElement($N, ZN({ ref: t }, r), /*#__PURE__*/ C.createElement(qN, { isPanorama: !1 }, n));
});
//#endregion
//#region node_modules/recharts/es6/util/useReportScale.js
function nP(e, t) {
	return sP(e) || oP(e, t) || iP(e, t) || rP();
}
function rP() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function iP(e, t) {
	if (e) {
		if (typeof e == "string") return aP(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? aP(e, t) : void 0;
	}
}
function aP(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function oP(e, t) {
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
function sP(e) {
	if (Array.isArray(e)) return e;
}
function cP() {
	var e = Lr(), t = nP((0, C.useState)(null), 2), n = t[0], r = t[1], i = L(Qs);
	return (0, C.useEffect)(() => {
		if (n != null) {
			var t = n.getBoundingClientRect().width / n.offsetWidth;
			U(t) && t !== i && e(Ss(t));
		}
	}, [
		n,
		e,
		i
	]), r;
}
//#endregion
//#region node_modules/recharts/es6/chart/RechartsWrapper.js
function lP(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function uP(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? lP(Object(n), !0).forEach(function(t) {
			dP(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : lP(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function dP(e, t, n) {
	return (t = fP(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function fP(e) {
	var t = pP(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function pP(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function mP() {
	return mP = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, mP.apply(null, arguments);
}
function hP(e, t) {
	return bP(e) || yP(e, t) || _P(e, t) || gP();
}
function gP() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function _P(e, t) {
	if (e) {
		if (typeof e == "string") return vP(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? vP(e, t) : void 0;
	}
}
function vP(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function yP(e, t) {
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
function bP(e) {
	if (Array.isArray(e)) return e;
}
var xP = () => (ST(), null);
function SP(e) {
	if (typeof e == "number") return e;
	if (typeof e == "string") {
		var t = parseFloat(e);
		if (!Number.isNaN(t)) return t;
	}
	return 0;
}
var CP = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n, r, i = (0, C.useRef)(null), a = hP((0, C.useState)({
		containerWidth: SP((n = e.style) == null ? void 0 : n.width),
		containerHeight: SP((r = e.style) == null ? void 0 : r.height)
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
	}, [c]), /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(sl, {
		width: o.containerWidth,
		height: o.containerHeight
	}), /*#__PURE__*/ C.createElement("div", mP({ ref: l }, e)));
}), wP = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.width, r = e.height, i = hP((0, C.useState)({
		containerWidth: SP(n),
		containerHeight: SP(r)
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
	return /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(sl, {
		width: a.containerWidth,
		height: a.containerHeight
	}), /*#__PURE__*/ C.createElement("div", mP({ ref: c }, e)));
}), TP = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.width, r = e.height;
	return /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(sl, {
		width: n,
		height: r
	}), /*#__PURE__*/ C.createElement("div", mP({ ref: t }, e)));
}), EP = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.width, r = e.height;
	return typeof n == "string" || typeof r == "string" ? /*#__PURE__*/ C.createElement(wP, mP({}, e, { ref: t })) : typeof n == "number" && typeof r == "number" ? /*#__PURE__*/ C.createElement(TP, mP({}, e, {
		width: n,
		height: r,
		ref: t
	})) : /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(sl, {
		width: n,
		height: r
	}), /*#__PURE__*/ C.createElement("div", mP({ ref: t }, e)));
});
function DP(e) {
	return e ? CP : EP;
}
var OP = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.children, r = e.className, i = e.height, a = e.onClick, o = e.onContextMenu, s = e.onDoubleClick, c = e.onMouseDown, l = e.onMouseEnter, u = e.onMouseLeave, d = e.onMouseMove, f = e.onMouseUp, p = e.onTouchEnd, m = e.onTouchMove, h = e.onTouchStart, g = e.style, _ = e.width, v = e.responsive, y = e.dispatchTouchEvents, b = y === void 0 || y, x = (0, C.useRef)(null), S = Lr(), w = hP((0, C.useState)(null), 2), T = w[0], E = w[1], D = hP((0, C.useState)(null), 2), O = D[0], k = D[1], A = cP(), j = G(), M = (j == null ? void 0 : j.width) > 0 ? j.width : _, N = (j == null ? void 0 : j.height) > 0 ? j.height : i, P = (0, C.useCallback)((e) => {
		A(e), typeof t == "function" && t(e), E(e), k(e), e != null && (x.current = e);
	}, [
		A,
		t,
		E,
		k
	]), ee = (0, C.useCallback)((e) => {
		S(tN(e)), S(CN({
			handler: a,
			reactEvent: e
		}));
	}, [S, a]), te = (0, C.useCallback)((e) => {
		S(rN(e)), S(CN({
			handler: l,
			reactEvent: e
		}));
	}, [S, l]), ne = (0, C.useCallback)((e) => {
		S(jS()), S(CN({
			handler: u,
			reactEvent: e
		}));
	}, [S, u]), re = (0, C.useCallback)((e) => {
		S(rN(e)), S(CN({
			handler: d,
			reactEvent: e
		}));
	}, [S, d]), ie = (0, C.useCallback)(() => {
		S(gN());
	}, [S]), ae = (0, C.useCallback)(() => {
		S(_N());
	}, [S]), oe = (0, C.useCallback)((e) => {
		S(hN(e.key));
	}, [S]), se = (0, C.useCallback)((e) => {
		S(CN({
			handler: o,
			reactEvent: e
		}));
	}, [S, o]), ce = (0, C.useCallback)((e) => {
		S(CN({
			handler: s,
			reactEvent: e
		}));
	}, [S, s]), le = (0, C.useCallback)((e) => {
		S(CN({
			handler: c,
			reactEvent: e
		}));
	}, [S, c]), ue = (0, C.useCallback)((e) => {
		S(CN({
			handler: f,
			reactEvent: e
		}));
	}, [S, f]), de = (0, C.useCallback)((e) => {
		S(CN({
			handler: h,
			reactEvent: e
		}));
	}, [S, h]), fe = (0, C.useCallback)((e) => {
		b && S(kN(e)), S(CN({
			handler: m,
			reactEvent: e
		}));
	}, [
		S,
		b,
		m
	]), pe = (0, C.useCallback)((e) => {
		S(CN({
			handler: p,
			reactEvent: e
		}));
	}, [S, p]), me = DP(v);
	return /*#__PURE__*/ C.createElement(Xw.Provider, { value: T }, /*#__PURE__*/ C.createElement(He.Provider, { value: O }, /*#__PURE__*/ C.createElement(me, {
		width: M == null ? g == null ? void 0 : g.width : M,
		height: N == null ? g == null ? void 0 : g.height : N,
		className: Ce("recharts-wrapper", r),
		style: uP({
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
	}, /*#__PURE__*/ C.createElement(xP, null), n)));
}), kP = [
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
function AP(e, t) {
	if (e == null) return {};
	var n, r, i = jP(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function jP(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var MP = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.width, r = e.height, i = e.responsive, a = e.children, o = e.className, s = e.style, c = e.compact, l = e.title, u = e.desc, d = ke(AP(e, kP));
	return c ? /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(sl, {
		width: n,
		height: r
	}), /*#__PURE__*/ C.createElement(tP, {
		otherAttributes: d,
		title: l,
		desc: u
	}, a)) : /*#__PURE__*/ C.createElement(OP, {
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
	}, /*#__PURE__*/ C.createElement(tP, {
		otherAttributes: d,
		title: l,
		desc: u,
		ref: t
	}, /*#__PURE__*/ C.createElement(nA, null, a)));
});
//#endregion
//#region node_modules/recharts/es6/chart/CartesianChart.js
function NP() {
	return NP = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, NP.apply(null, arguments);
}
function PP(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function FP(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? PP(Object(n), !0).forEach(function(t) {
			IP(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : PP(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function IP(e, t, n) {
	return (t = LP(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function LP(e) {
	var t = RP(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function RP(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var zP = FP({
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
}, FN), BP = /*#__PURE__*/ (0, C.forwardRef)(function(e, t) {
	var n, r = Sn(e.categoricalChartProps, zP), i = e.chartName, a = e.defaultTooltipEventType, o = e.validateTooltipEventTypes, s = e.tooltipPayloadSearcher, c = e.categoricalChartProps, l = {
		chartName: i,
		defaultTooltipEventType: a,
		validateTooltipEventTypes: o,
		tooltipPayloadSearcher: s,
		eventEmitter: void 0
	};
	return /*#__PURE__*/ C.createElement(VN, {
		preloadedState: { options: l },
		reduxStoreName: (n = c.id) == null ? i : n
	}, /*#__PURE__*/ C.createElement(Bk, { chartData: c.data }), /*#__PURE__*/ C.createElement(UN, {
		layout: r.layout,
		margin: r.margin
	}), /*#__PURE__*/ C.createElement(GN, {
		throttleDelay: r.throttleDelay,
		throttledEvents: r.throttledEvents
	}), /*#__PURE__*/ C.createElement(WN, {
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
	}), /*#__PURE__*/ C.createElement(MP, NP({}, r, { ref: t })));
}), VP = ["axis", "item"], HP = /*#__PURE__*/ (0, C.forwardRef)((e, t) => /*#__PURE__*/ C.createElement(BP, {
	chartName: "BarChart",
	defaultTooltipEventType: "axis",
	validateTooltipEventTypes: VP,
	tooltipPayloadSearcher: nT,
	categoricalChartProps: e,
	ref: t
})), UP = /* @__PURE__ */ o(((e) => {
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
})), WP = /* @__PURE__ */ o(((e, t) => {
	t.exports = UP();
})), GP = g(), Y = WP(), KP = [
	{
		key: "queueRows",
		label: "Queue Rows",
		icon: me,
		tone: "blue"
	},
	{
		key: "nextSteps",
		label: "Next Steps",
		icon: le,
		tone: "green"
	},
	{
		key: "undecidedJobReviews",
		label: "Undecided Job Reviews",
		icon: ue,
		tone: "violet"
	},
	{
		key: "undecidedMaybeTailor",
		label: "Undecided Maybe Tailor",
		icon: xe,
		tone: "cyan"
	}
], qP = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
function JP(e) {
	return Number.isFinite(e) ? Math.max(0, Number(e)) : 0;
}
function YP(e) {
	return Number.isFinite(e) ? qP.format(Number(e)) : "—";
}
function XP({ active: e, payload: t }) {
	var n;
	if (!e || !(t != null && t.length)) return null;
	let r = (n = t[0]) == null ? void 0 : n.payload;
	return r ? /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "executive-kpi-tooltip",
		children: [
			/* @__PURE__ */ (0, Y.jsx)("span", { children: "Current" }),
			/* @__PURE__ */ (0, Y.jsx)("strong", { children: YP(r.current) }),
			Number(r.baseline) > 0 ? /* @__PURE__ */ (0, Y.jsxs)("small", { children: ["Queue baseline: ", YP(r.baseline)] }) : null
		]
	}) : null;
}
function ZP({ value: e, queueRows: t, label: n }) {
	let r = Math.max(t, e, 1), i = [{
		name: "Current snapshot",
		current: e,
		remaining: Math.max(0, r - e),
		baseline: t
	}];
	return /* @__PURE__ */ (0, Y.jsx)("div", {
		className: "executive-kpi-chart",
		role: "img",
		"aria-label": t > 0 ? `${n}: ${YP(e)} against a current queue baseline of ${YP(t)}` : `${n}: ${YP(e)} in the current snapshot`,
		children: /* @__PURE__ */ (0, Y.jsx)(Xc, {
			width: "100%",
			height: "100%",
			children: /* @__PURE__ */ (0, Y.jsxs)(HP, {
				data: i,
				layout: "vertical",
				margin: {
					top: 6,
					right: 0,
					bottom: 6,
					left: 0
				},
				children: [
					/* @__PURE__ */ (0, Y.jsx)(IM, {
						type: "number",
						domain: [0, r],
						hide: !0
					}),
					/* @__PURE__ */ (0, Y.jsx)(ZM, {
						type: "category",
						dataKey: "name",
						hide: !0
					}),
					/* @__PURE__ */ (0, Y.jsx)(zT, {
						allowEscapeViewBox: {
							x: !1,
							y: !0
						},
						content: /* @__PURE__ */ (0, Y.jsx)(XP, {}),
						cursor: !1,
						wrapperStyle: {
							zIndex: 30,
							pointerEvents: "none"
						}
					}),
					/* @__PURE__ */ (0, Y.jsx)(hM, {
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
					/* @__PURE__ */ (0, Y.jsx)(hM, {
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
function QP({ metric: e }) {
	let t = e.icon;
	return /* @__PURE__ */ (0, Y.jsxs)("article", {
		className: `executive-kpi-card executive-kpi-card--${e.tone}`,
		"aria-busy": "true",
		children: [
			/* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "executive-kpi-card-header",
				children: [/* @__PURE__ */ (0, Y.jsx)("span", {
					className: "executive-kpi-label",
					children: e.label
				}), /* @__PURE__ */ (0, Y.jsx)("span", {
					className: "executive-kpi-icon",
					"aria-hidden": "true",
					children: /* @__PURE__ */ (0, Y.jsx)(t, {
						size: 17,
						strokeWidth: 2
					})
				})]
			}),
			/* @__PURE__ */ (0, Y.jsx)("div", { className: "executive-kpi-skeleton executive-kpi-skeleton--value" }),
			/* @__PURE__ */ (0, Y.jsx)("div", { className: "executive-kpi-skeleton executive-kpi-skeleton--caption" }),
			/* @__PURE__ */ (0, Y.jsx)("div", { className: "executive-kpi-skeleton executive-kpi-skeleton--chart" })
		]
	});
}
function $P({ state: e }) {
	if (e.status === "loading") return /* @__PURE__ */ (0, Y.jsx)("div", {
		className: "executive-kpi-dashboard kpi-grid kpi-grid-cols-1 sm:kpi-grid-cols-2 xl:kpi-grid-cols-4 kpi-gap-3",
		"aria-label": "Loading executive queue metrics",
		children: KP.map((e) => /* @__PURE__ */ (0, Y.jsx)(QP, { metric: e }, e.key))
	});
	let t = e.status === "error", n = t ? {
		queueRows: null,
		nextSteps: null,
		undecidedJobReviews: null,
		undecidedMaybeTailor: null
	} : e.metrics, r = JP(n.queueRows);
	return /* @__PURE__ */ (0, Y.jsx)("div", {
		className: "executive-kpi-dashboard kpi-grid kpi-grid-cols-1 sm:kpi-grid-cols-2 xl:kpi-grid-cols-4 kpi-gap-3",
		"aria-label": "Executive queue metrics",
		children: KP.map((e) => {
			let i = e.icon, a = n[e.key], o = JP(a);
			return /* @__PURE__ */ (0, Y.jsxs)("article", {
				className: `executive-kpi-card executive-kpi-card--${e.tone}`,
				children: [
					/* @__PURE__ */ (0, Y.jsxs)("div", {
						className: "executive-kpi-card-header",
						children: [/* @__PURE__ */ (0, Y.jsx)("span", {
							className: "executive-kpi-label",
							children: e.label
						}), /* @__PURE__ */ (0, Y.jsx)("span", {
							className: "executive-kpi-icon",
							"aria-hidden": "true",
							children: /* @__PURE__ */ (0, Y.jsx)(i, {
								size: 17,
								strokeWidth: 2
							})
						})]
					}),
					/* @__PURE__ */ (0, Y.jsx)("strong", {
						className: "executive-kpi-value",
						children: t ? "Unavailable" : YP(a)
					}),
					/* @__PURE__ */ (0, Y.jsx)("span", {
						className: "executive-kpi-caption",
						children: t ? "Status data could not be loaded" : "Current snapshot"
					}),
					t ? /* @__PURE__ */ (0, Y.jsx)("div", {
						className: "executive-kpi-error",
						role: "status",
						children: "Refresh Status to try again."
					}) : /* @__PURE__ */ (0, Y.jsx)(ZP, {
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
function eF(e, t) {
	return typeof e == "function" ? e(t) : e;
}
function tF(e, t) {
	return (n) => {
		t.setState((t) => ({
			...t,
			[e]: eF(n, t[e])
		}));
	};
}
function nF(e) {
	return e instanceof Function;
}
function rF(e) {
	return Array.isArray(e) && e.every((e) => typeof e == "number");
}
function iF(e, t) {
	let n = [], r = (e) => {
		e.forEach((e) => {
			n.push(e);
			let i = t(e);
			i != null && i.length && r(i);
		});
	};
	return r(e), n;
}
function X(e, t, n) {
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
function Z(e, t, n, r) {
	return {
		debug: () => {
			var n;
			return (n = e == null ? void 0 : e.debugAll) == null ? e[t] : n;
		},
		key: !1,
		onChange: r
	};
}
function aF(e, t, n, r) {
	let i = {
		id: `${t.id}_${n.id}`,
		row: t,
		column: n,
		getValue: () => t.getValue(r),
		renderValue: () => {
			var t;
			return (t = i.getValue()) == null ? e.options.renderFallbackValue : t;
		},
		getContext: X(() => [
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
		}), Z(e.options, "debugCells", "cell.getContext"))
	};
	return e._features.forEach((r) => {
		r.createCell == null || r.createCell(i, n, t, e);
	}, {}), i;
}
function oF(e, t, n, r) {
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
		getFlatColumns: X(() => [!0], () => {
			var e;
			return [u, ...(e = u.columns) == null ? void 0 : e.flatMap((e) => e.getFlatColumns())];
		}, Z(e.options, "debugColumns", "column.getFlatColumns")),
		getLeafColumns: X(() => [e._getOrderColumnsFn()], (e) => {
			var t;
			return (t = u.columns) != null && t.length ? e(u.columns.flatMap((e) => e.getLeafColumns())) : [u];
		}, Z(e.options, "debugColumns", "column.getLeafColumns"))
	};
	for (let t of e._features) t.createColumn == null || t.createColumn(u, e);
	return u;
}
var sF = "debugHeaders";
function cF(e, t, n) {
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
var lF = { createTable: (e) => {
	e.getHeaderGroups = X(() => [
		e.getAllColumns(),
		e.getVisibleLeafColumns(),
		e.getState().columnPinning.left,
		e.getState().columnPinning.right
	], (t, n, r, i) => {
		var a, o;
		let s = (a = r == null ? void 0 : r.map((e) => n.find((t) => t.id === e)).filter(Boolean)) == null ? [] : a, c = (o = i == null ? void 0 : i.map((e) => n.find((t) => t.id === e)).filter(Boolean)) == null ? [] : o, l = n.filter((e) => !(r != null && r.includes(e.id)) && !(i != null && i.includes(e.id)));
		return uF(t, [
			...s,
			...l,
			...c
		], e);
	}, Z(e.options, sF, "getHeaderGroups")), e.getCenterHeaderGroups = X(() => [
		e.getAllColumns(),
		e.getVisibleLeafColumns(),
		e.getState().columnPinning.left,
		e.getState().columnPinning.right
	], (t, n, r, i) => (n = n.filter((e) => !(r != null && r.includes(e.id)) && !(i != null && i.includes(e.id))), uF(t, n, e, "center")), Z(e.options, sF, "getCenterHeaderGroups")), e.getLeftHeaderGroups = X(() => [
		e.getAllColumns(),
		e.getVisibleLeafColumns(),
		e.getState().columnPinning.left
	], (t, n, r) => {
		var i;
		return uF(t, (i = r == null ? void 0 : r.map((e) => n.find((t) => t.id === e)).filter(Boolean)) == null ? [] : i, e, "left");
	}, Z(e.options, sF, "getLeftHeaderGroups")), e.getRightHeaderGroups = X(() => [
		e.getAllColumns(),
		e.getVisibleLeafColumns(),
		e.getState().columnPinning.right
	], (t, n, r) => {
		var i;
		return uF(t, (i = r == null ? void 0 : r.map((e) => n.find((t) => t.id === e)).filter(Boolean)) == null ? [] : i, e, "right");
	}, Z(e.options, sF, "getRightHeaderGroups")), e.getFooterGroups = X(() => [e.getHeaderGroups()], (e) => [...e].reverse(), Z(e.options, sF, "getFooterGroups")), e.getLeftFooterGroups = X(() => [e.getLeftHeaderGroups()], (e) => [...e].reverse(), Z(e.options, sF, "getLeftFooterGroups")), e.getCenterFooterGroups = X(() => [e.getCenterHeaderGroups()], (e) => [...e].reverse(), Z(e.options, sF, "getCenterFooterGroups")), e.getRightFooterGroups = X(() => [e.getRightHeaderGroups()], (e) => [...e].reverse(), Z(e.options, sF, "getRightFooterGroups")), e.getFlatHeaders = X(() => [e.getHeaderGroups()], (e) => e.map((e) => e.headers).flat(), Z(e.options, sF, "getFlatHeaders")), e.getLeftFlatHeaders = X(() => [e.getLeftHeaderGroups()], (e) => e.map((e) => e.headers).flat(), Z(e.options, sF, "getLeftFlatHeaders")), e.getCenterFlatHeaders = X(() => [e.getCenterHeaderGroups()], (e) => e.map((e) => e.headers).flat(), Z(e.options, sF, "getCenterFlatHeaders")), e.getRightFlatHeaders = X(() => [e.getRightHeaderGroups()], (e) => e.map((e) => e.headers).flat(), Z(e.options, sF, "getRightFlatHeaders")), e.getCenterLeafHeaders = X(() => [e.getCenterFlatHeaders()], (e) => e.filter((e) => {
		var t;
		return !((t = e.subHeaders) != null && t.length);
	}), Z(e.options, sF, "getCenterLeafHeaders")), e.getLeftLeafHeaders = X(() => [e.getLeftFlatHeaders()], (e) => e.filter((e) => {
		var t;
		return !((t = e.subHeaders) != null && t.length);
	}), Z(e.options, sF, "getLeftLeafHeaders")), e.getRightLeafHeaders = X(() => [e.getRightFlatHeaders()], (e) => e.filter((e) => {
		var t;
		return !((t = e.subHeaders) != null && t.length);
	}), Z(e.options, sF, "getRightLeafHeaders")), e.getLeafHeaders = X(() => [
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
	}, Z(e.options, sF, "getLeafHeaders"));
} };
function uF(e, t, n, r) {
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
				let i = cF(n, c, {
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
	l(t.map((e, t) => cF(n, e, {
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
var dF = (e, t, n, r, i, a, o) => {
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
		getLeafRows: () => iF(s.subRows, (e) => e.subRows),
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
		getAllCells: X(() => [e.getAllLeafColumns()], (t) => t.map((t) => aF(e, s, t, t.id)), Z(e.options, "debugRows", "getAllCells")),
		_getAllCellsByColumnId: X(() => [s.getAllCells()], (e) => e.reduce((e, t) => (e[t.column.id] = t, e), {}), Z(e.options, "debugRows", "getAllCellsByColumnId"))
	};
	for (let t = 0; t < e._features.length; t++) {
		let n = e._features[t];
		n == null || n.createRow == null || n.createRow(s, e);
	}
	return s;
}, fF = { createColumn: (e, t) => {
	e._getFacetedRowModel = t.options.getFacetedRowModel && t.options.getFacetedRowModel(t, e.id), e.getFacetedRowModel = () => e._getFacetedRowModel ? e._getFacetedRowModel() : t.getPreFilteredRowModel(), e._getFacetedUniqueValues = t.options.getFacetedUniqueValues && t.options.getFacetedUniqueValues(t, e.id), e.getFacetedUniqueValues = () => e._getFacetedUniqueValues ? e._getFacetedUniqueValues() : /* @__PURE__ */ new Map(), e._getFacetedMinMaxValues = t.options.getFacetedMinMaxValues && t.options.getFacetedMinMaxValues(t, e.id), e.getFacetedMinMaxValues = () => {
		if (e._getFacetedMinMaxValues) return e._getFacetedMinMaxValues();
	};
} }, pF = (e, t, n) => {
	var r, i;
	let a = n == null || (r = n.toString()) == null ? void 0 : r.toLowerCase();
	return !!(!((i = e.getValue(t)) == null || (i = i.toString()) == null || (i = i.toLowerCase()) == null) && i.includes(a));
};
pF.autoRemove = (e) => CF(e);
var mF = (e, t, n) => {
	var r;
	return !!(!((r = e.getValue(t)) == null || (r = r.toString()) == null) && r.includes(n));
};
mF.autoRemove = (e) => CF(e);
var hF = (e, t, n) => {
	var r;
	return ((r = e.getValue(t)) == null || (r = r.toString()) == null ? void 0 : r.toLowerCase()) === (n == null ? void 0 : n.toLowerCase());
};
hF.autoRemove = (e) => CF(e);
var gF = (e, t, n) => {
	var r;
	return (r = e.getValue(t)) == null ? void 0 : r.includes(n);
};
gF.autoRemove = (e) => CF(e);
var _F = (e, t, n) => !n.some((n) => {
	var r;
	return !((r = e.getValue(t)) != null && r.includes(n));
});
_F.autoRemove = (e) => CF(e) || !(e != null && e.length);
var vF = (e, t, n) => n.some((n) => {
	var r;
	return (r = e.getValue(t)) == null ? void 0 : r.includes(n);
});
vF.autoRemove = (e) => CF(e) || !(e != null && e.length);
var yF = (e, t, n) => e.getValue(t) === n;
yF.autoRemove = (e) => CF(e);
var bF = (e, t, n) => e.getValue(t) == n;
bF.autoRemove = (e) => CF(e);
var xF = (e, t, n) => {
	let [r, i] = n, a = e.getValue(t);
	return a >= r && a <= i;
};
xF.resolveFilterValue = (e) => {
	let [t, n] = e, r = typeof t == "number" ? t : parseFloat(t), i = typeof n == "number" ? n : parseFloat(n), a = t === null || Number.isNaN(r) ? -Infinity : r, o = n === null || Number.isNaN(i) ? Infinity : i;
	if (a > o) {
		let e = a;
		a = o, o = e;
	}
	return [a, o];
}, xF.autoRemove = (e) => CF(e) || CF(e[0]) && CF(e[1]);
var SF = {
	includesString: pF,
	includesStringSensitive: mF,
	equalsString: hF,
	arrIncludes: gF,
	arrIncludesAll: _F,
	arrIncludesSome: vF,
	equals: yF,
	weakEquals: bF,
	inNumberRange: xF
};
function CF(e) {
	return e == null || e === "";
}
var wF = {
	getDefaultColumnDef: () => ({ filterFn: "auto" }),
	getInitialState: (e) => ({
		columnFilters: [],
		...e
	}),
	getDefaultOptions: (e) => ({
		onColumnFiltersChange: tF("columnFilters", e),
		filterFromLeafRows: !1,
		maxLeafRowFilterDepth: 100
	}),
	createColumn: (e, t) => {
		e.getAutoFilterFn = () => {
			let n = t.getCoreRowModel().flatRows[0], r = n == null ? void 0 : n.getValue(e.id);
			return typeof r == "string" ? SF.includesString : typeof r == "number" ? SF.inNumberRange : typeof r == "boolean" || typeof r == "object" && r ? SF.equals : Array.isArray(r) ? SF.arrIncludes : SF.weakEquals;
		}, e.getFilterFn = () => {
			var n, r;
			return nF(e.columnDef.filterFn) ? e.columnDef.filterFn : e.columnDef.filterFn === "auto" ? e.getAutoFilterFn() : (n = (r = t.options.filterFns) == null ? void 0 : r[e.columnDef.filterFn]) == null ? SF[e.columnDef.filterFn] : n;
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
				let r = e.getFilterFn(), i = t == null ? void 0 : t.find((t) => t.id === e.id), a = eF(n, i ? i.value : void 0);
				if (TF(r, a, e)) {
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
				return (r = eF(t, e)) == null ? void 0 : r.filter((e) => {
					let t = n.find((t) => t.id === e.id);
					return !(t && TF(t.getFilterFn(), e.value, t));
				});
			});
		}, e.resetColumnFilters = (t) => {
			var n, r;
			e.setColumnFilters(t || (n = (r = e.initialState) == null ? void 0 : r.columnFilters) == null ? [] : n);
		}, e.getPreFilteredRowModel = () => e.getCoreRowModel(), e.getFilteredRowModel = () => (!e._getFilteredRowModel && e.options.getFilteredRowModel && (e._getFilteredRowModel = e.options.getFilteredRowModel(e)), e.options.manualFiltering || !e._getFilteredRowModel ? e.getPreFilteredRowModel() : e._getFilteredRowModel());
	}
};
function TF(e, t, n) {
	return (e && e.autoRemove ? e.autoRemove(t, n) : !1) || t === void 0 || typeof t == "string" && !t;
}
var EF = {
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
		if (!rF(n)) return;
		if (n.length === 1) return n[0];
		let r = Math.floor(n.length / 2), i = n.sort((e, t) => e - t);
		return n.length % 2 == 0 ? (i[r - 1] + i[r]) / 2 : i[r];
	},
	unique: (e, t) => Array.from(new Set(t.map((t) => t.getValue(e))).values()),
	uniqueCount: (e, t) => new Set(t.map((t) => t.getValue(e))).size,
	count: (e, t) => t.length
}, DF = {
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
		onGroupingChange: tF("grouping", e),
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
			if (typeof r == "number") return EF.sum;
			if (Object.prototype.toString.call(r) === "[object Date]") return EF.extent;
		}, e.getAggregationFn = () => {
			var n, r;
			if (!e) throw Error();
			return nF(e.columnDef.aggregationFn) ? e.columnDef.aggregationFn : e.columnDef.aggregationFn === "auto" ? e.getAutoAggregationFn() : (n = (r = t.options.aggregationFns) == null ? void 0 : r[e.columnDef.aggregationFn]) == null ? EF[e.columnDef.aggregationFn] : n;
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
function OF(e, t, n) {
	if (!(t != null && t.length) || !n) return e;
	let r = e.filter((e) => !t.includes(e.id));
	return n === "remove" ? r : [...t.map((t) => e.find((e) => e.id === t)).filter(Boolean), ...r];
}
var kF = {
	getInitialState: (e) => ({
		columnOrder: [],
		...e
	}),
	getDefaultOptions: (e) => ({ onColumnOrderChange: tF("columnOrder", e) }),
	createColumn: (e, t) => {
		e.getIndex = X((e) => [BF(t, e)], (t) => t.findIndex((t) => t.id === e.id), Z(t.options, "debugColumns", "getIndex")), e.getIsFirstColumn = (n) => {
			var r;
			return ((r = BF(t, n)[0]) == null ? void 0 : r.id) === e.id;
		}, e.getIsLastColumn = (n) => {
			var r;
			let i = BF(t, n);
			return ((r = i[i.length - 1]) == null ? void 0 : r.id) === e.id;
		};
	},
	createTable: (e) => {
		e.setColumnOrder = (t) => e.options.onColumnOrderChange == null ? void 0 : e.options.onColumnOrderChange(t), e.resetColumnOrder = (t) => {
			var n;
			e.setColumnOrder(t || (n = e.initialState.columnOrder) == null ? [] : n);
		}, e._getOrderColumnsFn = X(() => [
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
			return OF(i, t, n);
		}, Z(e.options, "debugTable", "_getOrderColumnsFn"));
	}
}, AF = () => ({
	left: [],
	right: []
}), jF = {
	getInitialState: (e) => ({
		columnPinning: AF(),
		...e
	}),
	getDefaultOptions: (e) => ({ onColumnPinningChange: tF("columnPinning", e) }),
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
		e.getCenterVisibleCells = X(() => [
			e._getAllVisibleCells(),
			t.getState().columnPinning.left,
			t.getState().columnPinning.right
		], (e, t, n) => {
			let r = [...t == null ? [] : t, ...n == null ? [] : n];
			return e.filter((e) => !r.includes(e.column.id));
		}, Z(t.options, "debugRows", "getCenterVisibleCells")), e.getLeftVisibleCells = X(() => [e._getAllVisibleCells(), t.getState().columnPinning.left], (e, t) => (t == null ? [] : t).map((t) => e.find((e) => e.column.id === t)).filter(Boolean).map((e) => ({
			...e,
			position: "left"
		})), Z(t.options, "debugRows", "getLeftVisibleCells")), e.getRightVisibleCells = X(() => [e._getAllVisibleCells(), t.getState().columnPinning.right], (e, t) => (t == null ? [] : t).map((t) => e.find((e) => e.column.id === t)).filter(Boolean).map((e) => ({
			...e,
			position: "right"
		})), Z(t.options, "debugRows", "getRightVisibleCells"));
	},
	createTable: (e) => {
		e.setColumnPinning = (t) => e.options.onColumnPinningChange == null ? void 0 : e.options.onColumnPinningChange(t), e.resetColumnPinning = (t) => {
			var n, r;
			return e.setColumnPinning(t || (n = (r = e.initialState) == null ? void 0 : r.columnPinning) == null ? AF() : n);
		}, e.getIsSomeColumnsPinned = (t) => {
			var n;
			let r = e.getState().columnPinning;
			if (!t) {
				var i, a;
				return !!((i = r.left) != null && i.length || (a = r.right) != null && a.length);
			}
			return !!((n = r[t]) != null && n.length);
		}, e.getLeftLeafColumns = X(() => [e.getAllLeafColumns(), e.getState().columnPinning.left], (e, t) => (t == null ? [] : t).map((t) => e.find((e) => e.id === t)).filter(Boolean), Z(e.options, "debugColumns", "getLeftLeafColumns")), e.getRightLeafColumns = X(() => [e.getAllLeafColumns(), e.getState().columnPinning.right], (e, t) => (t == null ? [] : t).map((t) => e.find((e) => e.id === t)).filter(Boolean), Z(e.options, "debugColumns", "getRightLeafColumns")), e.getCenterLeafColumns = X(() => [
			e.getAllLeafColumns(),
			e.getState().columnPinning.left,
			e.getState().columnPinning.right
		], (e, t, n) => {
			let r = [...t == null ? [] : t, ...n == null ? [] : n];
			return e.filter((e) => !r.includes(e.id));
		}, Z(e.options, "debugColumns", "getCenterLeafColumns"));
	}
};
function MF(e) {
	return e || (typeof document < "u" ? document : null);
}
var NF = {
	size: 150,
	minSize: 20,
	maxSize: 2 ** 53 - 1
}, PF = () => ({
	startOffset: null,
	startSize: null,
	deltaOffset: null,
	deltaPercentage: null,
	isResizingColumn: !1,
	columnSizingStart: []
}), FF = {
	getDefaultColumnDef: () => NF,
	getInitialState: (e) => ({
		columnSizing: {},
		columnSizingInfo: PF(),
		...e
	}),
	getDefaultOptions: (e) => ({
		columnResizeMode: "onEnd",
		columnResizeDirection: "ltr",
		onColumnSizingChange: tF("columnSizing", e),
		onColumnSizingInfoChange: tF("columnSizingInfo", e)
	}),
	createColumn: (e, t) => {
		e.getSize = () => {
			var n, r, i;
			let a = t.getState().columnSizing[e.id];
			return Math.min(Math.max((n = e.columnDef.minSize) == null ? NF.minSize : n, (r = a == null ? e.columnDef.size : a) == null ? NF.size : r), (i = e.columnDef.maxSize) == null ? NF.maxSize : i);
		}, e.getStart = X((e) => [
			e,
			BF(t, e),
			t.getState().columnSizing
		], (t, n) => n.slice(0, e.getIndex(t)).reduce((e, t) => e + t.getSize(), 0), Z(t.options, "debugColumns", "getStart")), e.getAfter = X((e) => [
			e,
			BF(t, e),
			t.getState().columnSizing
		], (t, n) => n.slice(e.getIndex(t) + 1).reduce((e, t) => e + t.getSize(), 0), Z(t.options, "debugColumns", "getAfter")), e.resetSize = () => {
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
				if (!r || !i || (a.persist == null || a.persist(), RF(a) && a.touches && a.touches.length > 1)) return;
				let o = e.getSize(), s = e ? e.getLeafHeaders().map((e) => [e.column.id, e.column.getSize()]) : [[r.id, r.getSize()]], c = RF(a) ? Math.round(a.touches[0].clientX) : a.clientX, l = {}, u = (e, n) => {
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
				}, p = MF(n), m = {
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
				}, g = LF() ? { passive: !1 } : !1;
				RF(a) ? (p == null || p.addEventListener("touchmove", h.moveHandler, g), p == null || p.addEventListener("touchend", h.upHandler, g)) : (p == null || p.addEventListener("mousemove", m.moveHandler, g), p == null || p.addEventListener("mouseup", m.upHandler, g)), t.setColumnSizingInfo((e) => ({
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
			e.setColumnSizingInfo(t || (n = e.initialState.columnSizingInfo) == null ? PF() : n);
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
}, IF = null;
function LF() {
	if (typeof IF == "boolean") return IF;
	let e = !1;
	try {
		let t = { get passive() {
			return e = !0, !1;
		} }, n = () => {};
		window.addEventListener("test", n, t), window.removeEventListener("test", n);
	} catch (t) {
		e = !1;
	}
	return IF = e, IF;
}
function RF(e) {
	return e.type === "touchstart";
}
var zF = {
	getInitialState: (e) => ({
		columnVisibility: {},
		...e
	}),
	getDefaultOptions: (e) => ({ onColumnVisibilityChange: tF("columnVisibility", e) }),
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
		e._getAllVisibleCells = X(() => [e.getAllCells(), t.getState().columnVisibility], (e) => e.filter((e) => e.column.getIsVisible()), Z(t.options, "debugRows", "_getAllVisibleCells")), e.getVisibleCells = X(() => [
			e.getLeftVisibleCells(),
			e.getCenterVisibleCells(),
			e.getRightVisibleCells()
		], (e, t, n) => [
			...e,
			...t,
			...n
		], Z(t.options, "debugRows", "getVisibleCells"));
	},
	createTable: (e) => {
		let t = (t, n) => X(() => [n(), n().filter((e) => e.getIsVisible()).map((e) => e.id).join("_")], (e) => e.filter((e) => e.getIsVisible == null ? void 0 : e.getIsVisible()), Z(e.options, "debugColumns", t));
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
function BF(e, t) {
	return t ? t === "center" ? e.getCenterVisibleLeafColumns() : t === "left" ? e.getLeftVisibleLeafColumns() : e.getRightVisibleLeafColumns() : e.getVisibleLeafColumns();
}
var VF = { createTable: (e) => {
	e._getGlobalFacetedRowModel = e.options.getFacetedRowModel && e.options.getFacetedRowModel(e, "__global__"), e.getGlobalFacetedRowModel = () => e.options.manualFiltering || !e._getGlobalFacetedRowModel ? e.getPreFilteredRowModel() : e._getGlobalFacetedRowModel(), e._getGlobalFacetedUniqueValues = e.options.getFacetedUniqueValues && e.options.getFacetedUniqueValues(e, "__global__"), e.getGlobalFacetedUniqueValues = () => e._getGlobalFacetedUniqueValues ? e._getGlobalFacetedUniqueValues() : /* @__PURE__ */ new Map(), e._getGlobalFacetedMinMaxValues = e.options.getFacetedMinMaxValues && e.options.getFacetedMinMaxValues(e, "__global__"), e.getGlobalFacetedMinMaxValues = () => {
		if (e._getGlobalFacetedMinMaxValues) return e._getGlobalFacetedMinMaxValues();
	};
} }, HF = {
	getInitialState: (e) => ({
		globalFilter: void 0,
		...e
	}),
	getDefaultOptions: (e) => ({
		onGlobalFilterChange: tF("globalFilter", e),
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
		e.getGlobalAutoFilterFn = () => SF.includesString, e.getGlobalFilterFn = () => {
			var t, n;
			let { globalFilterFn: r } = e.options;
			return nF(r) ? r : r === "auto" ? e.getGlobalAutoFilterFn() : (t = (n = e.options.filterFns) == null ? void 0 : n[r]) == null ? SF[r] : t;
		}, e.setGlobalFilter = (t) => {
			e.options.onGlobalFilterChange == null || e.options.onGlobalFilterChange(t);
		}, e.resetGlobalFilter = (t) => {
			e.setGlobalFilter(t ? void 0 : e.initialState.globalFilter);
		};
	}
}, UF = {
	getInitialState: (e) => ({
		expanded: {},
		...e
	}),
	getDefaultOptions: (e) => ({
		onExpandedChange: tF("expanded", e),
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
}, WF = 0, GF = 10, KF = () => ({
	pageIndex: WF,
	pageSize: GF
}), qF = {
	getInitialState: (e) => ({
		...e,
		pagination: {
			...KF(),
			...e == null ? void 0 : e.pagination
		}
	}),
	getDefaultOptions: (e) => ({ onPaginationChange: tF("pagination", e) }),
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
		}, e.setPagination = (t) => e.options.onPaginationChange == null ? void 0 : e.options.onPaginationChange((e) => eF(t, e)), e.resetPagination = (t) => {
			var n;
			e.setPagination(t || (n = e.initialState.pagination) == null ? KF() : n);
		}, e.setPageIndex = (t) => {
			e.setPagination((n) => {
				let r = eF(t, n.pageIndex), i = e.options.pageCount === void 0 || e.options.pageCount === -1 ? 2 ** 53 - 1 : e.options.pageCount - 1;
				return r = Math.max(0, Math.min(r, i)), {
					...n,
					pageIndex: r
				};
			});
		}, e.resetPageIndex = (t) => {
			var n, r;
			e.setPageIndex(t || (n = (r = e.initialState) == null || (r = r.pagination) == null ? void 0 : r.pageIndex) == null ? WF : n);
		}, e.resetPageSize = (t) => {
			var n, r;
			e.setPageSize(t || (n = (r = e.initialState) == null || (r = r.pagination) == null ? void 0 : r.pageSize) == null ? GF : n);
		}, e.setPageSize = (t) => {
			e.setPagination((e) => {
				let n = Math.max(1, eF(t, e.pageSize)), r = e.pageSize * e.pageIndex, i = Math.floor(r / n);
				return {
					...e,
					pageIndex: i,
					pageSize: n
				};
			});
		}, e.setPageCount = (t) => e.setPagination((n) => {
			var r;
			let i = eF(t, (r = e.options.pageCount) == null ? -1 : r);
			return typeof i == "number" && (i = Math.max(-1, i)), {
				...n,
				pageCount: i
			};
		}), e.getPageOptions = X(() => [e.getPageCount()], (e) => {
			let t = [];
			return e && e > 0 && (t = [...Array(e)].fill(null).map((e, t) => t)), t;
		}, Z(e.options, "debugTable", "getPageOptions")), e.getCanPreviousPage = () => e.getState().pagination.pageIndex > 0, e.getCanNextPage = () => {
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
}, JF = () => ({
	top: [],
	bottom: []
}), YF = {
	getInitialState: (e) => ({
		rowPinning: JF(),
		...e
	}),
	getDefaultOptions: (e) => ({ onRowPinningChange: tF("rowPinning", e) }),
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
			return e.setRowPinning(t || (n = (r = e.initialState) == null ? void 0 : r.rowPinning) == null ? JF() : n);
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
		}, e.getTopRows = X(() => [e.getRowModel().rows, e.getState().rowPinning.top], (t, n) => e._getPinnedRows(t, n, "top"), Z(e.options, "debugRows", "getTopRows")), e.getBottomRows = X(() => [e.getRowModel().rows, e.getState().rowPinning.bottom], (t, n) => e._getPinnedRows(t, n, "bottom"), Z(e.options, "debugRows", "getBottomRows")), e.getCenterRows = X(() => [
			e.getRowModel().rows,
			e.getState().rowPinning.top,
			e.getState().rowPinning.bottom
		], (e, t, n) => {
			let r = /* @__PURE__ */ new Set([...t == null ? [] : t, ...n == null ? [] : n]);
			return e.filter((e) => !r.has(e.id));
		}, Z(e.options, "debugRows", "getCenterRows"));
	}
}, XF = {
	getInitialState: (e) => ({
		rowSelection: {},
		...e
	}),
	getDefaultOptions: (e) => ({
		onRowSelectionChange: tF("rowSelection", e),
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
				ZF(i, t.id, r, !0, e);
			}), i;
		}), e.getPreSelectedRowModel = () => e.getCoreRowModel(), e.getSelectedRowModel = X(() => [e.getState().rowSelection, e.getCoreRowModel()], (t, n) => Object.keys(t).length ? QF(e, n) : {
			rows: [],
			flatRows: [],
			rowsById: {}
		}, Z(e.options, "debugTable", "getSelectedRowModel")), e.getFilteredSelectedRowModel = X(() => [e.getState().rowSelection, e.getFilteredRowModel()], (t, n) => Object.keys(t).length ? QF(e, n) : {
			rows: [],
			flatRows: [],
			rowsById: {}
		}, Z(e.options, "debugTable", "getFilteredSelectedRowModel")), e.getGroupedSelectedRowModel = X(() => [e.getState().rowSelection, e.getSortedRowModel()], (t, n) => Object.keys(t).length ? QF(e, n) : {
			rows: [],
			flatRows: [],
			rowsById: {}
		}, Z(e.options, "debugTable", "getGroupedSelectedRowModel")), e.getIsAllRowsSelected = () => {
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
				return ZF(s, e.id, n, (o = r == null ? void 0 : r.selectChildren) == null || o, t), s;
			});
		}, e.getIsSelected = () => {
			let { rowSelection: n } = t.getState();
			return $F(e, n);
		}, e.getIsSomeSelected = () => {
			let { rowSelection: n } = t.getState();
			return eI(e, n) === "some";
		}, e.getIsAllSubRowsSelected = () => {
			let { rowSelection: n } = t.getState();
			return eI(e, n) === "all";
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
}, ZF = (e, t, n, r, i) => {
	var a;
	let o = i.getRow(t, !0);
	n ? (o.getCanMultiSelect() || Object.keys(e).forEach((t) => delete e[t]), o.getCanSelect() && (e[t] = !0)) : delete e[t], r && (a = o.subRows) != null && a.length && o.getCanSelectSubRows() && o.subRows.forEach((t) => ZF(e, t.id, n, r, i));
};
function QF(e, t) {
	let n = e.getState().rowSelection, r = [], i = {}, a = function(e, t) {
		return e.map((e) => {
			var t;
			let o = $F(e, n);
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
function $F(e, t) {
	var n;
	return (n = t[e.id]) != null && n;
}
function eI(e, t, n) {
	var r;
	if (!((r = e.subRows) != null && r.length)) return !1;
	let i = !0, a = !1;
	return e.subRows.forEach((e) => {
		if (!(a && !i) && (e.getCanSelect() && ($F(e, t) ? a = !0 : i = !1), e.subRows && e.subRows.length)) {
			let n = eI(e, t);
			n === "all" ? a = !0 : (n === "some" && (a = !0), i = !1);
		}
	}), i ? "all" : a ? "some" : !1;
}
var tI = /([0-9]+)/gm, nI = (e, t, n) => uI(lI(e.getValue(n)).toLowerCase(), lI(t.getValue(n)).toLowerCase()), rI = (e, t, n) => uI(lI(e.getValue(n)), lI(t.getValue(n))), iI = (e, t, n) => cI(lI(e.getValue(n)).toLowerCase(), lI(t.getValue(n)).toLowerCase()), aI = (e, t, n) => cI(lI(e.getValue(n)), lI(t.getValue(n))), oI = (e, t, n) => {
	let r = e.getValue(n), i = t.getValue(n);
	return r > i ? 1 : r < i ? -1 : 0;
}, sI = (e, t, n) => cI(e.getValue(n), t.getValue(n));
function cI(e, t) {
	return e === t ? 0 : e > t ? 1 : -1;
}
function lI(e) {
	return typeof e == "number" ? isNaN(e) || e === Infinity || e === -Infinity ? "" : String(e) : typeof e == "string" ? e : "";
}
function uI(e, t) {
	let n = e.split(tI).filter(Boolean), r = t.split(tI).filter(Boolean);
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
var dI = {
	alphanumeric: nI,
	alphanumericCaseSensitive: rI,
	text: iI,
	textCaseSensitive: aI,
	datetime: oI,
	basic: sI
}, fI = [
	lF,
	zF,
	kF,
	jF,
	fF,
	wF,
	VF,
	HF,
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
			onSortingChange: tF("sorting", e),
			isMultiSortEvent: (e) => e.shiftKey
		}),
		createColumn: (e, t) => {
			e.getAutoSortingFn = () => {
				let n = t.getFilteredRowModel().flatRows.slice(10), r = !1;
				for (let t of n) {
					let n = t == null ? void 0 : t.getValue(e.id);
					if (Object.prototype.toString.call(n) === "[object Date]") return dI.datetime;
					if (typeof n == "string" && (r = !0, n.split(tI).length > 1)) return dI.alphanumeric;
				}
				return r ? dI.text : dI.basic;
			}, e.getAutoSortDir = () => {
				let n = t.getFilteredRowModel().flatRows[0];
				return typeof (n == null ? void 0 : n.getValue(e.id)) == "string" ? "asc" : "desc";
			}, e.getSortingFn = () => {
				var n, r;
				if (!e) throw Error();
				return nF(e.columnDef.sortingFn) ? e.columnDef.sortingFn : e.columnDef.sortingFn === "auto" ? e.getAutoSortingFn() : (n = (r = t.options.sortingFns) == null ? void 0 : r[e.columnDef.sortingFn]) == null ? dI[e.columnDef.sortingFn] : n;
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
	DF,
	UF,
	qF,
	YF,
	XF,
	FF
];
function pI(e) {
	var t, n;
	let r = [...fI, ...(t = e._features) == null ? [] : t], i = { _features: r }, a = i._features.reduce((e, t) => Object.assign(e, t.getDefaultOptions == null ? void 0 : t.getDefaultOptions(i)), {}), o = (e) => i.options.mergeOptions ? i.options.mergeOptions(a, e) : {
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
			let t = eF(e, i.options);
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
		_getDefaultColumnDef: X(() => [i.options.defaultColumn], (e) => {
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
		}, Z(e, "debugColumns", "_getDefaultColumnDef")),
		_getColumnDefs: () => i.options.columns,
		getAllColumns: X(() => [i._getColumnDefs()], (e) => {
			let t = function(e, n, r) {
				return r === void 0 && (r = 0), e.map((e) => {
					let a = oF(i, e, r, n), o = e;
					return a.columns = o.columns ? t(o.columns, a, r + 1) : [], a;
				});
			};
			return t(e);
		}, Z(e, "debugColumns", "getAllColumns")),
		getAllFlatColumns: X(() => [i.getAllColumns()], (e) => e.flatMap((e) => e.getFlatColumns()), Z(e, "debugColumns", "getAllFlatColumns")),
		_getAllFlatColumnsById: X(() => [i.getAllFlatColumns()], (e) => e.reduce((e, t) => (e[t.id] = t, e), {}), Z(e, "debugColumns", "getAllFlatColumnsById")),
		getAllLeafColumns: X(() => [i.getAllColumns(), i._getOrderColumnsFn()], (e, t) => t(e.flatMap((e) => e.getLeafColumns())), Z(e, "debugColumns", "getAllLeafColumns")),
		getColumn: (e) => i._getAllFlatColumnsById()[e]
	};
	Object.assign(i, u);
	for (let e = 0; e < i._features.length; e++) {
		let t = i._features[e];
		t == null || t.createTable == null || t.createTable(i);
	}
	return i;
}
function mI() {
	return (e) => X(() => [e.options.data], (t) => {
		let n = {
			rows: [],
			flatRows: [],
			rowsById: {}
		}, r = function(t, i, a) {
			i === void 0 && (i = 0);
			let o = [];
			for (let c = 0; c < t.length; c++) {
				let l = dF(e, e._getRowId(t[c], c, a), t[c], c, i, void 0, a == null ? void 0 : a.id);
				if (n.flatRows.push(l), n.rowsById[l.id] = l, o.push(l), e.options.getSubRows) {
					var s;
					l.originalSubRows = e.options.getSubRows(t[c], c), (s = l.originalSubRows) != null && s.length && (l.subRows = r(l.originalSubRows, i + 1, l));
				}
			}
			return o;
		};
		return n.rows = r(t), n;
	}, Z(e.options, "debugTable", "getRowModel", () => e._autoResetPageIndex()));
}
function hI() {
	return (e) => X(() => [e.getState().sorting, e.getPreSortedRowModel()], (t, n) => {
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
	}, Z(e.options, "debugTable", "getSortedRowModel", () => e._autoResetPageIndex()));
}
//#endregion
//#region node_modules/@tanstack/react-table/build/lib/index.mjs
function gI(e, t) {
	return e ? _I(e) ? /*#__PURE__*/ C.createElement(e, t) : e : null;
}
function _I(e) {
	return vI(e) || typeof e == "function" || yI(e);
}
function vI(e) {
	return typeof e == "function" && (() => {
		let t = Object.getPrototypeOf(e);
		return t.prototype && t.prototype.isReactComponent;
	})();
}
function yI(e) {
	return typeof e == "object" && typeof e.$$typeof == "symbol" && ["react.memo", "react.forward_ref"].includes(e.$$typeof.description);
}
function bI(e) {
	let t = {
		state: {},
		onStateChange: () => {},
		renderFallbackValue: null,
		...e
	}, [n] = C.useState(() => ({ current: pI(t) })), [r, i] = C.useState(() => n.current.initialState);
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
//#region src/filter/FilterSelect.tsx
var xI = "applylens:shared-filter-select-open";
function SI(e) {
	return e.toLowerCase().replace(/[\/_-]+/g, " ").trim().replace(/\s+/g, " ");
}
function CI({ id: e, label: t, options: n, values: r, onChange: i, placeholder: a, allLabel: o, mode: s, searchable: c = !1, disabled: l = !1 }) {
	let [u, d] = (0, C.useState)(!1), [f, p] = (0, C.useState)(""), [m, h] = (0, C.useState)(0), [g, _] = (0, C.useState)(null), v = (0, C.useId)(), y = (0, C.useRef)(null), b = (0, C.useRef)(null), x = (0, C.useRef)([]), S = `${e}-label`, w = `${e}-menu`, T = SI(f), E = (0, C.useMemo)(() => n.filter((e) => SI(e.label).includes(T)), [T, n]), D = !!(o && (!T || SI(o).includes(T))), O = (0, C.useMemo)(() => [...D ? [{
		value: "__all__",
		label: o || a,
		isAll: !0
	}] : [], ...E.map((e) => ({
		...e,
		isAll: !1
	}))], [
		o,
		D,
		a,
		E
	]), k = r.map((e) => {
		var t;
		return (t = n.find((t) => t.value === e)) == null ? void 0 : t.label;
	}).filter(Boolean), A = k.length === 0 ? a : k.length === 1 ? k[0] : `${k.length} selected`, N = () => {
		let e = y.current;
		if (!e) return;
		let t = e.getBoundingClientRect(), n = Math.max(220, window.innerWidth - 24), r = Math.min(Math.max(t.width, 240), n), i = Math.min(Math.max(t.left, 12), window.innerWidth - r - 12), a = window.innerHeight - t.bottom - 12, o = t.top - 12, s = a < 190 && o > a ? "top" : "bottom", c = Math.max(150, Math.min(320, (s === "top" ? o : a) - 8));
		_({
			left: i,
			width: r,
			maxHeight: c,
			placement: s,
			...s === "top" ? { bottom: window.innerHeight - t.top + 6 } : { top: t.bottom + 6 }
		});
	}, P = (e = !1) => {
		d(!1), p(""), h(0), e && window.requestAnimationFrame(() => {
			var e;
			return (e = y.current) == null ? void 0 : e.focus();
		});
	}, ee = () => {
		l || (window.dispatchEvent(new CustomEvent(xI, { detail: { instanceId: v } })), d(!0), h(0));
	};
	(0, C.useLayoutEffect)(() => {
		u && N();
	}, [u, O.length]), (0, C.useEffect)(() => {
		if (!u) return;
		let e = (e) => {
			var t;
			((t = e.detail) == null ? void 0 : t.instanceId) !== v && P(!1);
		}, t = (e) => {
			var t, n;
			let r = e.target;
			!((t = y.current) != null && t.contains(r)) && !((n = b.current) != null && n.contains(r)) && P(!1);
		}, n = (e) => {
			e.key === "Escape" && (e.preventDefault(), P(!0));
		}, r = () => N();
		return window.addEventListener(xI, e), document.addEventListener("pointerdown", t), document.addEventListener("keydown", n), window.addEventListener("resize", r), window.addEventListener("scroll", r, !0), () => {
			window.removeEventListener(xI, e), document.removeEventListener("pointerdown", t), document.removeEventListener("keydown", n), window.removeEventListener("resize", r), window.removeEventListener("scroll", r, !0);
		};
	}, [v, u]), (0, C.useEffect)(() => {
		!u || c || window.requestAnimationFrame(() => {
			var e;
			return (e = x.current[m]) == null ? void 0 : e.focus();
		});
	}, [
		m,
		u,
		c
	]);
	let te = (e, t) => {
		i(t ? [] : s === "single" ? [e] : r.includes(e) ? r.filter((t) => t !== e) : [...r, e]), s === "single" && P(!0);
	}, ne = (e) => {
		if (!O.length) return;
		let t = (e + O.length) % O.length;
		h(t), window.requestAnimationFrame(() => {
			var e;
			return (e = x.current[t]) == null ? void 0 : e.focus();
		});
	}, re = (e, t) => {
		if (e.key === "Enter" || e.key === " ") {
			e.preventDefault();
			let n = O[t];
			n && te(n.value, n.isAll);
		} else e.key === "ArrowDown" ? (e.preventDefault(), ne(t + 1)) : e.key === "ArrowUp" ? (e.preventDefault(), ne(t - 1)) : e.key === "Home" ? (e.preventDefault(), ne(0)) : e.key === "End" ? (e.preventDefault(), ne(O.length - 1)) : e.key === "Tab" && P(!1);
	}, ie = g ? {
		left: g.left,
		top: g.top,
		bottom: g.bottom,
		width: g.width,
		maxHeight: g.maxHeight
	} : void 0, ae = u && g ? (0, zw.createPortal)(/* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "shared-filter-select__menu",
		id: w,
		ref: b,
		role: "listbox",
		"aria-labelledby": S,
		"aria-multiselectable": s === "multiple",
		"data-placement": g.placement,
		style: ie,
		children: [c ? /* @__PURE__ */ (0, Y.jsxs)("label", {
			className: "shared-filter-select__search",
			children: [
				/* @__PURE__ */ (0, Y.jsxs)("span", {
					className: "sr-only",
					children: ["Search ", t.toLowerCase()]
				}),
				/* @__PURE__ */ (0, Y.jsx)(he, {
					size: 15,
					"aria-hidden": "true"
				}),
				/* @__PURE__ */ (0, Y.jsx)("input", {
					autoFocus: !0,
					type: "search",
					value: f,
					onChange: (e) => {
						p(e.target.value), h(0);
					},
					onKeyDown: (e) => {
						if (e.key === "ArrowDown" && O.length) {
							var t;
							e.preventDefault(), (t = x.current[0]) == null || t.focus();
						} else e.key === "Tab" && P(!1);
					},
					placeholder: `Search ${t.toLowerCase()}`
				})
			]
		}) : null, /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "shared-filter-select__options",
			children: [O.map((e, t) => {
				let n = e.isAll ? r.length === 0 : r.includes(e.value);
				return /* @__PURE__ */ (0, Y.jsxs)("button", {
					type: "button",
					className: `shared-filter-select__option ${n ? "is-selected" : ""} ${"tone" in e && e.tone ? "has-tone" : ""}`,
					ref: (e) => {
						x.current[t] = e;
					},
					role: "option",
					"aria-selected": n,
					tabIndex: t === m ? 0 : -1,
					onFocus: () => h(t),
					onKeyDown: (e) => re(e, t),
					onClick: () => te(e.value, e.isAll),
					children: [
						/* @__PURE__ */ (0, Y.jsx)(j, {
							className: "shared-filter-select__check",
							size: 15,
							"aria-hidden": "true"
						}),
						"tone" in e && e.tone ? /* @__PURE__ */ (0, Y.jsx)("span", {
							className: `shared-filter-select__dot shared-filter-select__dot--${e.tone}`,
							"aria-hidden": "true"
						}) : null,
						/* @__PURE__ */ (0, Y.jsx)("span", { children: e.label })
					]
				}, e.value);
			}), O.length ? null : /* @__PURE__ */ (0, Y.jsx)("div", {
				className: "shared-filter-select__empty",
				children: "No options found"
			})]
		})]
	}), document.body) : null;
	return /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "shared-filter-select",
		"data-filter-select-id": e,
		children: [
			/* @__PURE__ */ (0, Y.jsx)("span", {
				className: "shared-filter-select__label",
				id: S,
				children: t
			}),
			/* @__PURE__ */ (0, Y.jsxs)("button", {
				type: "button",
				className: "shared-filter-select__trigger",
				id: e,
				ref: y,
				"aria-labelledby": `${S} ${e}-value`,
				"aria-haspopup": "listbox",
				"aria-controls": w,
				"aria-expanded": u,
				disabled: l,
				onClick: () => u ? P(!1) : ee(),
				onKeyDown: (e) => {
					[
						"Enter",
						" ",
						"ArrowDown",
						"ArrowUp"
					].includes(e.key) && (e.preventDefault(), u || ee());
				},
				children: [/* @__PURE__ */ (0, Y.jsx)("span", {
					id: `${e}-value`,
					title: A,
					children: A
				}), /* @__PURE__ */ (0, Y.jsx)(M, {
					size: 15,
					"aria-hidden": "true"
				})]
			}),
			ae
		]
	});
}
//#endregion
//#region src/table/TablePrimitives.tsx
var wI = "preferences-secondary-action";
function TI({ expanded: e, label: t, controls: n, className: r = "", onClick: i }) {
	return /* @__PURE__ */ (0, Y.jsx)("button", {
		type: "button",
		className: `${wI} shared-table-expand-btn ${r}`.trim(),
		"aria-label": t,
		"aria-expanded": e,
		"aria-controls": e ? n : void 0,
		onClick: i,
		children: e ? /* @__PURE__ */ (0, Y.jsx)(M, {
			size: 15,
			"aria-hidden": "true"
		}) : /* @__PURE__ */ (0, Y.jsx)(N, {
			size: 15,
			"aria-hidden": "true"
		})
	});
}
function EI({ value: e, strength: t, label: n = "Match score", unavailableLabel: r = "Unavailable", className: i = "" }) {
	if (e == null || String(e).trim() === "") return /* @__PURE__ */ (0, Y.jsx)("span", {
		className: "shared-table-muted",
		children: r
	});
	let a = Number(String(e).replace(/,/g, ""));
	if (!Number.isFinite(a)) return /* @__PURE__ */ (0, Y.jsx)("span", {
		className: "shared-table-muted",
		children: r
	});
	let o = Math.abs(a) <= 1 ? a * 100 : a, s = Math.max(0, Math.min(100, o)), c = o.toFixed(2);
	return /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: `shared-match-meter ${i}`.trim(),
		children: [
			/* @__PURE__ */ (0, Y.jsx)("span", {
				className: "shared-match-meter__value",
				children: c
			}),
			t ? /* @__PURE__ */ (0, Y.jsx)("span", {
				className: "shared-match-meter__strength",
				children: t
			}) : null,
			/* @__PURE__ */ (0, Y.jsx)("span", {
				className: "shared-match-meter__track",
				role: "progressbar",
				"aria-label": `${n} ${c} out of 100${t ? `, ${t}` : ""}`,
				"aria-valuemin": 0,
				"aria-valuemax": 100,
				"aria-valuenow": Number(s.toFixed(2)),
				children: /* @__PURE__ */ (0, Y.jsx)("span", { style: { width: `${s}%` } })
			})
		]
	});
}
function DI({ label: e, children: t }) {
	let [n, r] = (0, C.useState)(!1), i = (0, C.useRef)(null), a = (0, C.useRef)(null), o = (0, C.useId)();
	return (0, C.useEffect)(() => {
		if (!n) return;
		let e = (e) => {
			var t;
			(t = i.current) != null && t.contains(e.target) || r(!1);
		}, t = (e) => {
			var t;
			e.key === "Escape" && (r(!1), (t = a.current) == null || t.focus());
		};
		return document.addEventListener("mousedown", e), document.addEventListener("keydown", t), () => {
			document.removeEventListener("mousedown", e), document.removeEventListener("keydown", t);
		};
	}, [n]), /* @__PURE__ */ (0, Y.jsxs)("span", {
		className: "shared-info-popover",
		ref: i,
		onMouseEnter: () => r(!0),
		onMouseLeave: () => r(!1),
		onFocus: () => r(!0),
		onBlur: (e) => {
			e.currentTarget.contains(e.relatedTarget) || r(!1);
		},
		children: [/* @__PURE__ */ (0, Y.jsx)("button", {
			ref: a,
			type: "button",
			className: `${wI} shared-info-popover__trigger`,
			"aria-label": e,
			"aria-expanded": n,
			"aria-controls": o,
			onClick: () => r((e) => !e),
			children: /* @__PURE__ */ (0, Y.jsx)(ce, {
				size: 13,
				"aria-hidden": "true"
			})
		}), /* @__PURE__ */ (0, Y.jsx)("span", {
			className: "shared-info-popover__content",
			id: o,
			role: "tooltip",
			hidden: !n,
			children: t
		})]
	});
}
function OI({ title: e, location: t, children: n }) {
	let r = (0, C.useId)();
	return /* @__PURE__ */ (0, Y.jsxs)("span", {
		className: "shared-job-preview",
		tabIndex: 0,
		"aria-describedby": r,
		children: [n, /* @__PURE__ */ (0, Y.jsxs)("span", {
			className: "shared-job-preview__popover",
			role: "tooltip",
			id: r,
			children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: e || "Untitled job" }), /* @__PURE__ */ (0, Y.jsx)("span", { children: t || "Location unavailable" })]
		})]
	});
}
function kI({ children: e }) {
	return /* @__PURE__ */ (0, Y.jsx)("div", {
		className: "shared-table-details",
		children: e
	});
}
function AI({ pagination: e, visibleCount: t, noun: n = "jobs", ariaLabel: r, onPageChange: i }) {
	let { page: a, pageSize: o, totalCount: s, totalPages: c, hasPrevPage: l, hasNextPage: u } = e, d = s ? (a - 1) * o + 1 : 0, f = s ? Math.min(d + Math.max(t - 1, 0), s) : 0;
	return /* @__PURE__ */ (0, Y.jsxs)("nav", {
		className: "shared-table-pagination",
		"aria-label": r,
		children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: s ? `Showing ${d}-${f} of ${s} ${n}` : `0 ${n}` }), /* @__PURE__ */ (0, Y.jsxs)("div", { children: [
			/* @__PURE__ */ (0, Y.jsx)("button", {
				type: "button",
				className: wI,
				disabled: !l,
				"aria-label": `Previous ${r.toLowerCase()}`,
				onClick: () => i(a - 1),
				children: "Previous"
			}),
			/* @__PURE__ */ (0, Y.jsxs)("span", {
				"aria-current": "page",
				children: [
					a,
					" / ",
					Math.max(c, 1)
				]
			}),
			/* @__PURE__ */ (0, Y.jsx)("button", {
				type: "button",
				className: wI,
				disabled: !u,
				"aria-label": `Next ${r.toLowerCase()}`,
				onClick: () => i(a + 1),
				children: "Next"
			})
		] })]
	});
}
function jI(e) {
	let t = e.column.columnDef.header;
	return typeof t == "string" ? t : e.column.id.replace(/_/g, " ");
}
function MI({ header: e, sticky: t }) {
	let n = e.column.getIsSorted(), r = jI(e);
	return /* @__PURE__ */ (0, Y.jsxs)("th", {
		style: { width: e.getSize() },
		className: `shared-table-column--${e.column.id} ${t ? "is-sticky-action" : ""} ${n ? "is-sorted" : ""}`.trim(),
		"aria-sort": n === "asc" ? "ascending" : n === "desc" ? "descending" : e.column.getCanSort() ? "none" : void 0,
		children: [e.isPlaceholder ? null : /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "shared-table-header-content",
			children: [gI(e.column.columnDef.header, e.getContext()), e.column.getCanSort() ? /* @__PURE__ */ (0, Y.jsx)("button", {
				type: "button",
				className: `${wI} shared-table-sort-btn ${n ? "is-sorted" : ""}`,
				"aria-label": r,
				onClick: e.column.getToggleSortingHandler(),
				children: n === "asc" ? /* @__PURE__ */ (0, Y.jsx)(P, {
					size: 14,
					"aria-hidden": "true"
				}) : n === "desc" ? /* @__PURE__ */ (0, Y.jsx)(M, {
					size: 14,
					"aria-hidden": "true"
				}) : /* @__PURE__ */ (0, Y.jsx)(k, {
					className: "shared-table-sort-placeholder",
					size: 13,
					"aria-hidden": "true"
				})
			}) : null]
		}), e.column.getCanResize() ? /* @__PURE__ */ (0, Y.jsx)("span", {
			className: `shared-table-resize-handle ${e.column.getIsResizing() ? "is-resizing" : ""}`,
			onMouseDown: (t) => {
				t.stopPropagation(), e.getResizeHandler()(t);
			},
			onTouchStart: (t) => {
				t.stopPropagation(), e.getResizeHandler()(t);
			},
			role: "separator",
			"aria-orientation": "vertical",
			"aria-label": `Resize ${jI(e)} column`
		}) : null]
	}, e.id);
}
function NI({ className: e, ariaLabel: t, title: n, subtitle: r, count: i, table: a, columns: o, status: s, error: c, headerActions: l, pagination: u, paginationNoun: d = "jobs", paginationLabel: f, stickyColumnId: p, rowClassName: m, detailId: h, renderDetails: g, empty: _, onPageChange: v, onRetry: y, fillAvailableWidth: b = !1, deferPaginationWhileLoading: x = !1 }) {
	let S = (e) => x && s === "loading" ? /* @__PURE__ */ (0, Y.jsx)("div", {
		className: "shared-table-pagination shared-table-pagination--loading",
		role: "status",
		children: /* @__PURE__ */ (0, Y.jsxs)("span", { children: [
			"Loading ",
			d,
			"..."
		] })
	}) : /* @__PURE__ */ (0, Y.jsx)(AI, {
		pagination: u,
		visibleCount: a.getRowModel().rows.length,
		noun: d,
		ariaLabel: `${f} ${e} pagination`,
		onPageChange: v
	});
	return /* @__PURE__ */ (0, Y.jsxs)("section", {
		className: `shared-table-card ${e}`,
		"aria-label": t,
		children: [
			/* @__PURE__ */ (0, Y.jsxs)("header", {
				className: "shared-table-header",
				children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
					className: "shared-table-heading",
					children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
						className: "shared-table-title-line",
						children: [/* @__PURE__ */ (0, Y.jsx)("h2", { children: n }), /* @__PURE__ */ (0, Y.jsx)("span", { children: x && s === "loading" ? "-" : i })]
					}), /* @__PURE__ */ (0, Y.jsx)("p", { children: x && s === "loading" ? `Loading ${d}...` : r })]
				}), /* @__PURE__ */ (0, Y.jsxs)("div", {
					className: "shared-table-header-actions",
					children: [l, S("top")]
				})]
			}),
			s === "error" ? /* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "shared-table-error",
				role: "alert",
				children: [/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: "Table data is unavailable" }), /* @__PURE__ */ (0, Y.jsx)("span", { children: c || "Try the request again." })] }), /* @__PURE__ */ (0, Y.jsx)("button", {
					type: "button",
					className: wI,
					onClick: y,
					children: "Retry"
				})]
			}) : /* @__PURE__ */ (0, Y.jsx)("div", {
				className: "shared-table-viewport",
				"aria-busy": s === "loading",
				children: /* @__PURE__ */ (0, Y.jsxs)("table", {
					style: {
						width: b ? "100%" : a.getTotalSize(),
						minWidth: a.getTotalSize()
					},
					children: [/* @__PURE__ */ (0, Y.jsx)("thead", { children: a.getHeaderGroups().map((e) => /* @__PURE__ */ (0, Y.jsx)("tr", { children: e.headers.map((e) => /* @__PURE__ */ (0, Y.jsx)(MI, {
						header: e,
						sticky: e.column.id === p
					}, e.id)) }, e.id)) }), /* @__PURE__ */ (0, Y.jsx)("tbody", { children: s === "loading" ? Array.from({ length: 5 }, (e, t) => /* @__PURE__ */ (0, Y.jsx)("tr", {
						className: "shared-table-skeleton-row",
						children: /* @__PURE__ */ (0, Y.jsx)("td", {
							colSpan: o.length,
							children: /* @__PURE__ */ (0, Y.jsx)("span", {})
						})
					}, `skeleton-${t}`)) : a.getRowModel().rows.length ? a.getRowModel().rows.flatMap((e, t) => [/* @__PURE__ */ (0, Y.jsx)("tr", {
						className: m(e, t),
						children: e.getVisibleCells().map((e) => /* @__PURE__ */ (0, Y.jsx)("td", {
							style: { width: e.column.getSize() },
							className: `shared-table-column--${e.column.id} ${e.column.id === p ? "is-sticky-action" : ""}`.trim(),
							children: gI(e.column.columnDef.cell, e.getContext())
						}, e.id))
					}, e.id), e.getIsExpanded() ? /* @__PURE__ */ (0, Y.jsx)("tr", {
						className: "shared-table-detail-row",
						id: h(e),
						children: /* @__PURE__ */ (0, Y.jsx)("td", {
							colSpan: e.getVisibleCells().length,
							children: g(e)
						})
					}, `${e.id}-details`) : null]) : /* @__PURE__ */ (0, Y.jsx)("tr", { children: /* @__PURE__ */ (0, Y.jsx)("td", {
						colSpan: o.length,
						children: _
					}) }) })]
				})
			}),
			S("bottom")
		]
	});
}
//#endregion
//#region src/ExecutiveQueue.tsx
var PI = "applylens:executive-queue-state", FI = "applylens:executive-queue-action", II = "queueTableColumnWidths", LI = wI, RI = {
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
	},
	sort: {
		key: "",
		direction: "asc"
	}
}, zI = [
	{
		value: "APPLY",
		label: "Ready for review",
		tone: "ready"
	},
	{
		value: "APPLY_REVIEW_VARIANTS",
		label: "Review resume choice",
		tone: "choice"
	},
	{
		value: "MAYBE_TAILOR",
		label: "Tailor first",
		tone: "tailor"
	},
	{
		value: "SKIP_FOR_NOW",
		label: "Review later",
		tone: "later"
	}
], BI = "A packet is a review bundle for this job. It includes the job, selected resume, match signals, gaps, and tailoring guidance. It does not apply to the job.";
function VI(e) {
	window.dispatchEvent(new CustomEvent(FI, { detail: e }));
}
function HI(e) {
	return String(e == null ? "" : e).trim();
}
function UI(e) {
	return {
		APPLY: "Ready for review",
		APPLY_REVIEW_VARIANTS: "Review resume choice",
		MAYBE_TAILOR: "Tailor first",
		SKIP_FOR_NOW: "Review later"
	}[HI(e).toUpperCase()] || HI(e) || "Unavailable";
}
function WI(e) {
	return {
		APPLY: "ready",
		APPLY_REVIEW_VARIANTS: "choice",
		MAYBE_TAILOR: "tailor",
		SKIP_FOR_NOW: "later"
	}[HI(e).toUpperCase()] || "unavailable";
}
function GI(e) {
	let t = HI(e).toLowerCase();
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
function KI(e) {
	return {
		no_deterministic_winner: "No clear resume match",
		borderline_deterministic_score: "Borderline match",
		tailoring_signal: "Tailoring may improve fit",
		tailoring_likely_worthwhile: "Tailoring may improve fit",
		packet_generation_blocked: "Packet unavailable",
		deterministic_equivalent_variants: "Close resume match",
		fallback_only_no_deterministic_match: "No credible resume match"
	}[HI(e).toLowerCase()] || HI(e).replace(/_/g, " ");
}
function qI(e) {
	return {
		SELECT_RESUME: "Choose resume",
		MAYBE_TAILOR: "Tailor first",
		SKIP_FOR_NOW: "Review later",
		APPLY: "Ready for review",
		APPLY_REVIEW_VARIANTS: "Review resume choice"
	}[HI(e.operator_decision).toUpperCase()] || {
		ready_to_apply: "Ready for review",
		tailor_then_apply: "Tailor then apply",
		review_before_action: "Review first",
		hold_or_skip: "Skip for now",
		source_watch: "Source watch"
	}[HI(e.operator_review_lane).toLowerCase()] || "—";
}
function JI(e) {
	let t = HI(e);
	return t ? t.replace(/\.pdf$/i, "").replace(/_/g, " ") : "—";
}
function YI(e) {
	if (e == null || HI(e) === "") return null;
	let t = Number(HI(e).replace(/,/g, ""));
	return Number.isFinite(t) ? Math.abs(t) <= 1 ? t * 100 : t : null;
}
function XI(e, t) {
	let n = HI(e);
	if (!n) return t === "unknown_timestamp_allowed" ? "Timestamp unavailable" : "—";
	let r = new Date(n);
	return Number.isNaN(r.getTime()) ? n : new Intl.DateTimeFormat(void 0, {
		month: "short",
		day: "numeric",
		year: "numeric"
	}).format(r);
}
function ZI(e, t) {
	return HI(e.job_doc_id) || `${HI(e.queue_rank) || "row"}-${t}`;
}
function QI() {
	try {
		let e = JSON.parse(localStorage.getItem("queueTableColumnWidths") || "{}");
		return e && typeof e == "object" ? e : {};
	} catch (e) {
		return {};
	}
}
function $I({ state: e }) {
	let [t, n] = (0, C.useState)(e.filters);
	(0, C.useEffect)(() => n(e.filters), [e.filters]);
	let r = e.preferenceOptions.map((e) => ({
		value: e.role_family_id,
		label: e.display_name || e.role_family_id
	}));
	return /* @__PURE__ */ (0, Y.jsxs)("section", {
		className: "executive-queue-filter-card",
		"aria-label": "Queue filters",
		children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "executive-queue-filter-grid",
			children: [
				/* @__PURE__ */ (0, Y.jsx)(CI, {
					id: "executiveActionFilter",
					label: "Action",
					options: zI,
					values: t.actions,
					onChange: (e) => n((t) => ({
						...t,
						actions: e
					})),
					placeholder: "All actions",
					mode: "single"
				}),
				/* @__PURE__ */ (0, Y.jsx)(CI, {
					id: "executivePreferenceFilter",
					label: "Preferences",
					options: r,
					values: t.preferenceIds,
					onChange: (e) => n((t) => ({
						...t,
						preferenceIds: e
					})),
					placeholder: "All Preferences",
					allLabel: "All Preferences",
					searchable: !0,
					mode: "multiple"
				}),
				/* @__PURE__ */ (0, Y.jsxs)("label", {
					className: "executive-queue-limit-field",
					children: [/* @__PURE__ */ (0, Y.jsx)("span", {
						className: "executive-queue-field-label",
						children: "Limit"
					}), /* @__PURE__ */ (0, Y.jsx)("input", {
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
				/* @__PURE__ */ (0, Y.jsxs)("fieldset", {
					className: "executive-queue-undecided-field",
					children: [/* @__PURE__ */ (0, Y.jsxs)("legend", { children: ["Undecided only", /* @__PURE__ */ (0, Y.jsx)("span", {
						title: "Shows only browse rows without an operator decision.",
						children: /* @__PURE__ */ (0, Y.jsx)(ce, {
							size: 14,
							"aria-label": "Shows only browse rows without an operator decision."
						})
					})] }), /* @__PURE__ */ (0, Y.jsxs)("div", {
						className: "executive-queue-segmented",
						children: [/* @__PURE__ */ (0, Y.jsx)("button", {
							type: "button",
							className: `${LI} ${t.undecidedOnly ? "" : "is-active"}`,
							"aria-pressed": !t.undecidedOnly,
							onClick: () => n((e) => ({
								...e,
								undecidedOnly: !1
							})),
							children: "No"
						}), /* @__PURE__ */ (0, Y.jsx)("button", {
							type: "button",
							className: `${LI} ${t.undecidedOnly ? "is-active" : ""}`,
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
		}), /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "executive-queue-filter-actions",
			children: [/* @__PURE__ */ (0, Y.jsxs)("button", {
				type: "button",
				className: `${LI} executive-queue-clear-btn`,
				onClick: () => VI({ type: "clear_filters" }),
				children: [/* @__PURE__ */ (0, Y.jsx)(pe, {
					size: 15,
					"aria-hidden": "true"
				}), " Clear"]
			}), /* @__PURE__ */ (0, Y.jsx)("button", {
				type: "button",
				className: "executive-queue-apply-btn",
				onClick: () => VI({
					type: "apply_filters",
					filters: t
				}),
				children: "Apply Filters"
			})]
		})]
	});
}
function eL({ row: e }) {
	return /* @__PURE__ */ (0, Y.jsx)(kI, { children: /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "executive-queue-details executive-queue-details--neutral",
		children: [
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Priority reason" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: KI(e.queue_priority_reason) || "—" })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Next step" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: qI(e) })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Selected resume" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: JI(e.operator_selected_resume || e.winner_resume) })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Runner-up" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: JI(e.runner_up_resume) })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Score gap" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: HI(e.score_gap) || "—" })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Missing requirements" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: HI(e.missing_requirement_count) || "0" })] }),
			/* @__PURE__ */ (0, Y.jsxs)("p", { children: [
				/* @__PURE__ */ (0, Y.jsx)(ce, {
					size: 14,
					"aria-hidden": "true"
				}),
				" ",
				BI
			] })
		]
	}) });
}
function tL(e) {
	let t = {
		id: "expand",
		header: "",
		size: 42,
		minSize: 42,
		maxSize: 42,
		enableSorting: !1,
		enableResizing: !1,
		cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)(TI, {
			expanded: e.getIsExpanded(),
			label: `${e.getIsExpanded() ? "Collapse" : "Expand"} details for ${HI(e.original.job_title) || "job"}`,
			controls: `executive-queue-detail-${e.id}`,
			className: "executive-queue-expand-btn",
			onClick: e.getToggleExpandedHandler()
		})
	}, n = {
		id: "review",
		header: "Review",
		size: 128,
		minSize: 128,
		maxSize: 128,
		enableSorting: !1,
		enableResizing: !1,
		cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)("button", {
			type: "button",
			className: "executive-queue-review-btn",
			disabled: !!e.original.is_applied,
			"aria-label": `Review ${HI(e.original.job_title) || "job"}`,
			onClick: () => VI({
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
			accessorFn: (e) => `${HI(e.job_title)} ${HI(e.job_company)}`,
			cell: ({ row: t }) => /* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "executive-queue-job-cell",
				children: [
					/* @__PURE__ */ (0, Y.jsx)("a", {
						href: HI(t.original.job_url || t.original.job_doc_id) || void 0,
						target: "_blank",
						rel: "noreferrer",
						children: HI(t.original.job_title) || "Untitled job"
					}),
					e === "simple" ? /* @__PURE__ */ (0, Y.jsx)("span", { children: HI(t.original.job_company) || "—" }) : null,
					/* @__PURE__ */ (0, Y.jsx)("small", { children: HI(t.original.job_location) || "Location unavailable" })
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
			cell: ({ row: e }) => XI(e.original.posted_at, e.original.freshness_status)
		},
		{
			id: "recommendation",
			header: "Recommendation",
			size: 180,
			minSize: 150,
			accessorFn: (e) => UI(e.action),
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)("span", {
				className: `executive-queue-badge executive-queue-badge--${WI(e.original.action)}`,
				children: UI(e.original.action)
			})
		},
		{
			id: "packet_status",
			header: () => /* @__PURE__ */ (0, Y.jsxs)("span", {
				className: "executive-queue-packet-head",
				children: ["Packet ", /* @__PURE__ */ (0, Y.jsx)(DI, {
					label: "About review packets",
					children: BI
				})]
			}),
			size: 138,
			minSize: 120,
			accessorFn: (e) => GI(e.packet_generation_allowed),
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)("span", {
				className: `executive-queue-badge executive-queue-badge--packet ${GI(e.original.packet_generation_allowed) === "Packet ready" ? "is-ready" : ""}`,
				children: GI(e.original.packet_generation_allowed)
			})
		},
		{
			id: "winner_score",
			header: "Match",
			size: 132,
			minSize: 112,
			accessorFn: (e) => YI(e.winner_score),
			sortUndefined: "last",
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)(EI, {
				value: e.original.winner_score,
				unavailableLabel: "—",
				className: "executive-queue-match"
			})
		},
		{
			id: "selected_resume",
			header: "Selected Resume",
			size: 240,
			minSize: 220,
			accessorFn: (e) => HI(e.operator_selected_resume || e.winner_resume),
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)("span", {
				className: "executive-queue-selected-resume-value",
				title: HI(e.original.operator_selected_resume || e.original.winner_resume),
				children: JI(e.original.operator_selected_resume || e.original.winner_resume)
			})
		},
		...e === "detailed" ? [
			{
				id: "runner_up_resume",
				header: "Runner-up resume",
				size: 210,
				minSize: 170,
				accessorFn: (e) => HI(e.runner_up_resume),
				cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)("span", {
					title: HI(e.original.runner_up_resume),
					children: JI(e.original.runner_up_resume)
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
				accessorFn: (e) => qI(e),
				enableSorting: !1
			},
			{
				id: "queue_priority_reason",
				header: "Priority reason",
				size: 180,
				minSize: 150,
				accessorFn: (e) => KI(e.queue_priority_reason) || "—",
				enableSorting: !1
			}
		] : [],
		n
	];
}
function nL({ state: e }) {
	let [t, n] = (0, C.useState)(QI), [r, i] = (0, C.useState)(""), a = (0, C.useMemo)(() => tL(e.viewMode), [e.viewMode]), o = (0, C.useMemo)(() => e.rows.slice(), [e.rows]), s = (0, C.useMemo)(() => e.sort.key ? [{
		id: e.sort.key,
		desc: e.sort.direction === "desc"
	}] : [], [e.sort]);
	(0, C.useEffect)(() => i(""), [
		e.rows,
		e.pagination.page,
		e.viewMode
	]);
	let c = bI({
		data: o,
		columns: a,
		state: {
			sorting: s,
			columnSizing: t,
			expanded: r ? { [r]: !0 } : {}
		},
		getRowId: (e, t) => ZI(e, t),
		onSortingChange: (e) => {
			let t = (typeof e == "function" ? e(s) : e)[0];
			t && (i(""), VI({
				type: "sort_change",
				key: t.id,
				direction: t.desc ? "desc" : "asc"
			}));
		},
		onColumnSizingChange: (e) => {
			n((t) => {
				let n = typeof e == "function" ? e(t) : e;
				return localStorage.setItem(II, JSON.stringify(n)), n;
			});
		},
		onExpandedChange: (e) => {
			let t = r ? { [r]: !0 } : {}, n = typeof e == "function" ? e(t) : e, a = n === !0 ? t : n, o = Object.keys(a).find((e) => a[e] && !t[e]);
			i(o || Object.keys(a).find((e) => a[e]) || "");
		},
		getRowCanExpand: () => !0,
		getCoreRowModel: mI(),
		manualSorting: !0,
		enableSortingRemoval: !1,
		columnResizeMode: "onChange"
	}), l = /* @__PURE__ */ (0, Y.jsx)("div", {
		className: "executive-queue-view-toggle",
		role: "radiogroup",
		"aria-label": "Executive view mode",
		children: ["detailed", "simple"].map((t) => /* @__PURE__ */ (0, Y.jsx)("button", {
			type: "button",
			role: "radio",
			"aria-checked": e.viewMode === t,
			className: `${LI} ${e.viewMode === t ? "is-active" : ""}`,
			onClick: () => VI({
				type: "view_mode_change",
				viewMode: t
			}),
			children: t === "detailed" ? "Detailed" : "Simple"
		}, t))
	});
	return /* @__PURE__ */ (0, Y.jsx)(NI, {
		className: `executive-queue-table-card executive-queue-table-card--${e.viewMode}`,
		ariaLabel: "Executive queue table",
		title: "Queue Table",
		subtitle: e.metaLabel,
		count: e.pagination.totalCount,
		table: c,
		columns: a,
		status: e.status,
		error: e.message,
		headerActions: l,
		pagination: e.pagination,
		paginationLabel: "Executive queue",
		stickyColumnId: "review",
		rowClassName: (e) => `executive-queue-row ${e.getIsExpanded() ? "is-expanded" : ""}`.trim(),
		detailId: (e) => `executive-queue-detail-${e.id}`,
		renderDetails: (e) => /* @__PURE__ */ (0, Y.jsx)(eL, { row: e.original }),
		empty: /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "executive-queue-empty",
			children: [
				/* @__PURE__ */ (0, Y.jsx)("strong", { children: "No jobs match these filters" }),
				/* @__PURE__ */ (0, Y.jsx)("span", { children: "Clear filters to return to the complete Executive queue." }),
				/* @__PURE__ */ (0, Y.jsx)("button", {
					type: "button",
					className: LI,
					onClick: () => VI({ type: "clear_filters" }),
					children: "Clear Filters"
				})
			]
		}),
		onPageChange: (e) => VI({
			type: "page_change",
			page: e
		}),
		onRetry: () => VI({ type: "retry" })
	});
}
function rL({ state: e }) {
	return /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: `executive-queue-dashboard executive-queue-dashboard--${e.viewMode}`,
		children: [/* @__PURE__ */ (0, Y.jsx)($I, { state: e }), /* @__PURE__ */ (0, Y.jsx)(nL, { state: e })]
	});
}
//#endregion
//#region src/pipeline/pipelineModel.ts
var iL = 2e3;
iL * 15;
var aL = [
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
], oL = {
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
}, sL = [
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
], cL = [
	["scraped_jobs", "Collected"],
	["filtered_jobs", "Filtered"],
	["deduped_jobs", "Deduplicated"],
	["ranked_jobs", "Ranked"],
	["ai_jobs", "Evaluated"],
	["resume_matched_jobs", "Resume matched"],
	["final_jobs", "Final"]
];
function lL(e) {
	let t = String(e || "idle").trim().toLowerCase();
	return t === "idle" ? "idle" : t === "queued" || t === "starting" ? "starting" : t === "running" ? "running" : t === "succeeded" ? "succeeded" : [
		"failed",
		"cancelled",
		"canceled",
		"stopped"
	].includes(t) ? "failed" : "unavailable";
}
function uL(e) {
	let t = Array.isArray(e.stage_order) ? e.stage_order.filter((e) => typeof e == "string" && e.length > 0) : [];
	return t.length ? t : [...aL];
}
function dL(e) {
	if (e === "" || e == null || typeof e == "boolean") return null;
	let t = typeof e == "number" ? e : Number(e);
	return Number.isFinite(t) && t >= 0 ? t : null;
}
function fL(e) {
	return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(e);
}
function pL(e) {
	if (!e) return "";
	let t = new Date(String(e));
	return Number.isNaN(t.getTime()) ? "" : new Intl.DateTimeFormat("en-US", {
		month: "short",
		day: "numeric",
		hour: "numeric",
		minute: "2-digit"
	}).format(t);
}
function mL(e, t, n = Date.now()) {
	let r = new Date(String(e || ""));
	if (Number.isNaN(r.getTime())) return "";
	let i = t ? new Date(String(t)) : null, a = i && !Number.isNaN(i.getTime()) ? i.getTime() : n, o = Math.max(0, Math.floor((a - r.getTime()) / 1e3)), s = Math.floor(o / 3600), c = Math.floor(o % 3600 / 60), l = o % 60;
	return s ? `${s}h ${c}m` : c ? `${c}m ${l}s` : `${l}s`;
}
function hL(e) {
	return String(e.updated_at_utc || e.updated_at || "").trim();
}
function gL(e, t = Date.now()) {
	if (lL(e.status) !== "running") return !1;
	let n = hL(e);
	if (!n) return !1;
	let r = new Date(n);
	return !Number.isNaN(r.getTime()) && t - r.getTime() > 3e4;
}
//#endregion
//#region src/pipeline/PipelineDashboard.tsx
var _L = "applylens:pipeline-run-accepted", vL = "applylens_pipeline_accepted_run_id", yL = [
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
function bL(e) {
	return oL[e] || e.replace(/_/g, " ").replace(/\b\w/g, (e) => e.toUpperCase());
}
function xL(e) {
	return e === "unavailable" ? "Unavailable" : e.charAt(0).toUpperCase() + e.slice(1);
}
function SL(e, t, n) {
	return new Set(Array.isArray(e.completed_stages) ? e.completed_stages : []).has(t) ? "complete" : t === e.current_stage && n === "failed" ? "failed" : t === e.current_stage && (n === "running" || n === "starting") ? "active" : "pending";
}
function CL(e) {
	if (typeof e == "boolean") return e ? "Enabled" : "Disabled";
	if (typeof e == "number" && Number.isFinite(e)) return fL(e);
	if (typeof e == "string") {
		let t = e.trim();
		return t ? t.toLowerCase() === "yes" ? "Enabled" : t.toLowerCase() === "no" ? "Disabled" : t : "";
	}
	return "";
}
async function wL() {
	let e = await fetch("/pipeline/status", {
		method: "GET",
		credentials: "same-origin",
		headers: { Accept: "application/json" }
	});
	if (!e.ok) throw Error(`Pipeline status request failed (${e.status})`);
	return e.json();
}
function TL() {
	if (typeof window.openApplyLensPipelineConfig == "function") {
		window.openApplyLensPipelineConfig();
		return;
	}
	console.error("The reviewed Pipeline launch flow is unavailable on this page.");
}
function EL() {
	try {
		return String(window.sessionStorage.getItem("applylens_pipeline_accepted_run_id") || "").trim();
	} catch (e) {
		return "";
	}
}
function DL(e) {
	try {
		window.sessionStorage.getItem("applylens_pipeline_accepted_run_id") === e && window.sessionStorage.removeItem(vL);
	} catch (e) {}
}
function OL(e, t = {}) {
	return { pipeline: {
		...t,
		status: t.status || "starting",
		run_id: e || t.run_id,
		current_stage: t.current_stage || "startup",
		stage_message: t.stage_message || "Synchronizing the accepted pipeline run."
	} };
}
function kL() {
	return /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "pipeline-dashboard pipeline-dashboard--loading",
		"aria-busy": "true",
		"aria-label": "Loading pipeline status",
		children: [
			/* @__PURE__ */ (0, Y.jsx)("div", { className: "pipeline-dashboard-skeleton pipeline-dashboard-skeleton--header" }),
			/* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "pipeline-dashboard-top-grid",
				children: [/* @__PURE__ */ (0, Y.jsx)("div", { className: "pipeline-dashboard-skeleton pipeline-dashboard-skeleton--summary" }), /* @__PURE__ */ (0, Y.jsx)("div", { className: "pipeline-dashboard-skeleton pipeline-dashboard-skeleton--stage" })]
			}),
			/* @__PURE__ */ (0, Y.jsx)("div", { className: "pipeline-dashboard-skeleton pipeline-dashboard-skeleton--counts" })
		]
	});
}
function AL({ onRefresh: e, onRun: t, refreshing: n, runActive: r }) {
	return /* @__PURE__ */ (0, Y.jsxs)("header", {
		className: "pipeline-dashboard-header",
		children: [/* @__PURE__ */ (0, Y.jsxs)("div", { children: [
			/* @__PURE__ */ (0, Y.jsx)("p", {
				className: "pipeline-dashboard-eyebrow",
				children: "Operations"
			}),
			/* @__PURE__ */ (0, Y.jsx)("h1", { children: "Pipeline" }),
			/* @__PURE__ */ (0, Y.jsx)("p", { children: "Monitor job collection, filtering, evaluation, resume matching, and planning." })
		] }), /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "pipeline-dashboard-actions",
			children: [/* @__PURE__ */ (0, Y.jsxs)("button", {
				className: "pipeline-dashboard-btn pipeline-dashboard-btn--secondary",
				type: "button",
				onClick: e,
				disabled: n,
				children: [/* @__PURE__ */ (0, Y.jsx)(fe, {
					size: 17,
					"aria-hidden": "true"
				}), n ? "Refreshing" : "Refresh Status"]
			}), /* @__PURE__ */ (0, Y.jsxs)("button", {
				className: "pipeline-dashboard-btn pipeline-dashboard-btn--primary",
				type: "button",
				onClick: t,
				disabled: r,
				children: [r ? /* @__PURE__ */ (0, Y.jsx)(O, {
					size: 17,
					"aria-hidden": "true"
				}) : /* @__PURE__ */ (0, Y.jsx)(de, {
					size: 17,
					"aria-hidden": "true"
				}), r ? "Pipeline Running..." : "Run Pipeline"]
			})]
		})]
	});
}
function jL({ pipeline: e, checkedAt: t }) {
	let n = lL(e.status), r = n === "starting" || n === "running", i = uL(e), a = new Set(Array.isArray(e.completed_stages) ? e.completed_stages : []), o = i.filter((e) => a.has(e)).length, s = i.length ? Math.min(o, i.length) : 0, c = String(e.current_stage || "").trim(), l = c && c.toLowerCase() !== "unknown" ? bL(c) : n === "failed" ? "Pipeline failed" : "Not active", u = mL(e.started_at, e.finished_at, t), d = hL(e), f = gL(e, t), p = n === "failed" ? e.error || e.summary_message || e.stage_message || "The latest pipeline run did not complete." : e.summary_message || e.stage_message || (n === "idle" ? "No pipeline run is active." : n === "succeeded" ? "The latest pipeline run completed successfully." : "Waiting for pipeline status details."), m = [
		["Run ID", e.run_id],
		["Started", pL(e.started_at)],
		["Last updated", pL(d)],
		["Completed", pL(e.finished_at)],
		["Elapsed", u],
		["Return code", e.return_code === null || e.return_code === void 0 ? "" : String(e.return_code)]
	].filter((e) => !!e[1]);
	return /* @__PURE__ */ (0, Y.jsxs)("section", {
		className: `pipeline-panel pipeline-run-summary pipeline-run-summary--${n}`,
		"aria-labelledby": "pipeline-current-run-title",
		"aria-busy": r,
		children: [
			/* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "pipeline-panel-heading",
				children: [/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("p", {
					className: "pipeline-panel-kicker",
					children: "Current run"
				}), /* @__PURE__ */ (0, Y.jsx)("h2", {
					id: "pipeline-current-run-title",
					children: l
				})] }), /* @__PURE__ */ (0, Y.jsxs)("span", {
					className: `pipeline-status-badge pipeline-status-badge--${n}`,
					role: "status",
					children: [/* @__PURE__ */ (0, Y.jsx)("span", { "aria-hidden": "true" }), xL(n)]
				})]
			}),
			/* @__PURE__ */ (0, Y.jsx)("p", {
				className: "pipeline-run-message",
				children: p
			}),
			r ? /* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "pipeline-running-indicator",
				role: "status",
				children: [/* @__PURE__ */ (0, Y.jsx)("span", {
					className: "pipeline-running-indicator__spinner",
					"aria-hidden": "true"
				}), /* @__PURE__ */ (0, Y.jsxs)("span", { children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: "Live run in progress" }), e.stage_message || "Waiting for the next pipeline update."] })]
			}) : null,
			f ? /* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "pipeline-stale-notice",
				role: "status",
				children: [/* @__PURE__ */ (0, Y.jsx)(ve, {
					size: 16,
					"aria-hidden": "true"
				}), " Status may be stale. The backend still reports this run as running."]
			}) : null,
			/* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "pipeline-stage-progress-copy",
				children: [/* @__PURE__ */ (0, Y.jsxs)("span", { children: [
					o,
					" of ",
					i.length,
					" stages complete"
				] }), e.stage_message ? /* @__PURE__ */ (0, Y.jsx)("strong", { children: e.stage_message }) : null]
			}),
			/* @__PURE__ */ (0, Y.jsx)("progress", {
				className: "pipeline-stage-progress",
				max: i.length || 1,
				value: s,
				"aria-label": `${o} of ${i.length} pipeline stages complete`
			}),
			r ? /* @__PURE__ */ (0, Y.jsx)("div", {
				className: "pipeline-running-strip",
				"aria-hidden": "true",
				children: /* @__PURE__ */ (0, Y.jsx)("span", {})
			}) : null,
			m.length ? /* @__PURE__ */ (0, Y.jsx)("dl", {
				className: "pipeline-run-details",
				children: m.map(([e, t]) => /* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("dt", { children: e }), /* @__PURE__ */ (0, Y.jsx)("dd", { children: t })] }, e))
			}) : null,
			e.final_job_count !== null && e.final_job_count !== void 0 ? /* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "pipeline-final-count",
				children: [
					/* @__PURE__ */ (0, Y.jsx)(ae, {
						size: 18,
						"aria-hidden": "true"
					}),
					/* @__PURE__ */ (0, Y.jsx)("span", { children: "Final jobs" }),
					/* @__PURE__ */ (0, Y.jsx)("strong", { children: fL(Number(e.final_job_count)) })
				]
			}) : null
		]
	});
}
function ML({ pipeline: e }) {
	let t = lL(e.status);
	return /* @__PURE__ */ (0, Y.jsxs)("section", {
		className: "pipeline-panel pipeline-stage-panel",
		"aria-labelledby": "pipeline-stage-title",
		children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "pipeline-panel-heading",
			children: [/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("p", {
				className: "pipeline-panel-kicker",
				children: "Stage progress"
			}), /* @__PURE__ */ (0, Y.jsx)("h2", {
				id: "pipeline-stage-title",
				children: "Execution timeline"
			})] }), /* @__PURE__ */ (0, Y.jsx)(O, {
				size: 20,
				"aria-hidden": "true"
			})]
		}), /* @__PURE__ */ (0, Y.jsx)("ol", {
			className: "pipeline-stage-list",
			"aria-label": "Pipeline stages",
			children: uL(e).map((n, r) => {
				let i = SL(e, n, t);
				return /* @__PURE__ */ (0, Y.jsxs)("li", {
					className: `pipeline-stage pipeline-stage--${i}`,
					"aria-current": i === "active" ? "step" : void 0,
					"data-stage-index": r + 1,
					children: [
						/* @__PURE__ */ (0, Y.jsx)("span", {
							className: "pipeline-stage-marker",
							"aria-hidden": "true",
							children: i === "complete" ? /* @__PURE__ */ (0, Y.jsx)(j, { size: 13 }) : i === "failed" ? /* @__PURE__ */ (0, Y.jsx)(ve, { size: 13 }) : /* @__PURE__ */ (0, Y.jsx)(te, { size: 9 })
						}),
						/* @__PURE__ */ (0, Y.jsxs)("span", {
							className: "pipeline-stage-name",
							title: bL(n),
							children: [/* @__PURE__ */ (0, Y.jsx)("span", {
								"aria-hidden": "true",
								children: String(r + 1).padStart(2, "0")
							}), bL(n)]
						}),
						/* @__PURE__ */ (0, Y.jsx)("small", { children: i === "complete" ? "Complete" : i === "active" ? "Active" : i === "failed" ? "Failed" : "Pending" })
					]
				}, n);
			})
		})]
	});
}
function NL({ pipeline: e }) {
	let t = e.counts || {}, n = sL.map((e) => ({
		label: e.label,
		values: e.keys.flatMap(([e, n]) => {
			let r = dL(t[e]);
			return r === null ? (t[e] !== void 0 && t[e] !== null && console.warn(`Ignoring malformed pipeline count: ${e}`), []) : [{
				key: e,
				label: n,
				value: r
			}];
		})
	})).filter((e) => e.values.length);
	return /* @__PURE__ */ (0, Y.jsxs)("section", {
		className: "pipeline-section",
		"aria-labelledby": "pipeline-counts-title",
		children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "pipeline-section-heading",
			children: [/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("p", {
				className: "pipeline-panel-kicker",
				children: "Live counts"
			}), /* @__PURE__ */ (0, Y.jsx)("h2", {
				id: "pipeline-counts-title",
				children: "Jobs through the pipeline"
			})] }), /* @__PURE__ */ (0, Y.jsx)("span", { children: "Only recorded values are shown" })]
		}), n.length ? /* @__PURE__ */ (0, Y.jsx)("div", {
			className: "pipeline-count-groups",
			children: n.map((e) => /* @__PURE__ */ (0, Y.jsxs)("section", {
				className: "pipeline-count-group",
				"aria-label": e.label,
				children: [/* @__PURE__ */ (0, Y.jsx)("h3", { children: e.label }), /* @__PURE__ */ (0, Y.jsx)("div", {
					className: "pipeline-count-grid",
					children: e.values.map((e) => /* @__PURE__ */ (0, Y.jsxs)("article", {
						className: "pipeline-count-card",
						children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: e.label }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: fL(e.value) })]
					}, e.key))
				})]
			}, e.label))
		}) : /* @__PURE__ */ (0, Y.jsx)("div", {
			className: "pipeline-empty-panel pipeline-empty-panel--compact",
			children: "Stage counts are not available for this run yet."
		})]
	});
}
function PL({ pipeline: e }) {
	let t = e.counts || {}, n = cL.flatMap(([n, r]) => {
		var i;
		let a = n === "final_jobs" ? e.final_job_count : void 0, o = dL((i = t[n]) == null ? a : i);
		return o === null ? [] : [{
			key: n,
			label: r,
			value: o
		}];
	}), r = Math.max(...n.map((e) => e.value), 0);
	return /* @__PURE__ */ (0, Y.jsxs)("section", {
		className: `pipeline-panel pipeline-flow-panel${n.length ? "" : " pipeline-flow-panel--empty"}`,
		"aria-labelledby": "pipeline-flow-title",
		children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "pipeline-panel-heading",
			children: [/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("p", {
				className: "pipeline-panel-kicker",
				children: "Pipeline flow"
			}), /* @__PURE__ */ (0, Y.jsx)("h2", {
				id: "pipeline-flow-title",
				children: "Current-run volume"
			})] }), /* @__PURE__ */ (0, Y.jsx)("span", {
				className: "pipeline-panel-note",
				children: "Relative to the largest recorded stage"
			})]
		}), n.length ? /* @__PURE__ */ (0, Y.jsx)("div", {
			className: "pipeline-flow",
			role: "img",
			"aria-label": n.map((e) => `${e.label}: ${fL(e.value)}`).join(", "),
			children: n.map((e, t) => {
				let i = r > 0 ? Math.max(e.value / r * 100, e.value > 0 ? 3 : 0) : 0;
				return /* @__PURE__ */ (0, Y.jsxs)("div", {
					className: "pipeline-flow-step",
					children: [
						/* @__PURE__ */ (0, Y.jsxs)("div", {
							className: "pipeline-flow-meta",
							children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: e.label }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: fL(e.value) })]
						}),
						/* @__PURE__ */ (0, Y.jsx)("div", {
							className: "pipeline-flow-track",
							"aria-hidden": "true",
							children: /* @__PURE__ */ (0, Y.jsx)("span", { style: { width: `${i}%` } })
						}),
						t < n.length - 1 ? /* @__PURE__ */ (0, Y.jsx)("span", {
							className: "pipeline-flow-connector",
							"aria-hidden": "true"
						}) : null
					]
				}, e.key);
			})
		}) : /* @__PURE__ */ (0, Y.jsx)("div", {
			className: "pipeline-empty-panel pipeline-empty-panel--compact",
			children: "Flow data will appear when the run records stage counts."
		})]
	});
}
function FL({ pipeline: e }) {
	let t = e.config || {}, n = yL.flatMap(([e, n]) => {
		let r = CL(t[e]);
		return r ? [{
			key: e,
			label: n,
			value: r
		}] : [];
	});
	return /* @__PURE__ */ (0, Y.jsxs)("section", {
		className: "pipeline-panel pipeline-compact-panel",
		"aria-labelledby": "pipeline-config-title",
		children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "pipeline-panel-heading",
			children: [/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("p", {
				className: "pipeline-panel-kicker",
				children: "Run configuration"
			}), /* @__PURE__ */ (0, Y.jsx)("h2", {
				id: "pipeline-config-title",
				children: "Safe settings snapshot"
			})] }), /* @__PURE__ */ (0, Y.jsx)(ge, {
				size: 20,
				"aria-hidden": "true"
			})]
		}), n.length ? /* @__PURE__ */ (0, Y.jsx)("dl", {
			className: "pipeline-config-list",
			children: n.map((e) => /* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("dt", { children: e.label }), /* @__PURE__ */ (0, Y.jsx)("dd", { children: e.value })] }, e.key))
		}) : /* @__PURE__ */ (0, Y.jsx)("div", {
			className: "pipeline-empty-panel",
			children: "No safe configuration fields were recorded for this run."
		})]
	});
}
function IL({ pipeline: e }) {
	let t = Array.isArray(e.source_health) ? e.source_health.filter((e) => e && typeof e.source == "string" && e.source.trim()) : [];
	return /* @__PURE__ */ (0, Y.jsxs)("section", {
		className: "pipeline-panel pipeline-compact-panel",
		"aria-labelledby": "pipeline-health-title",
		children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "pipeline-panel-heading",
			children: [/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("p", {
				className: "pipeline-panel-kicker",
				children: "Source health"
			}), /* @__PURE__ */ (0, Y.jsx)("h2", {
				id: "pipeline-health-title",
				children: "Collection evidence"
			})] }), /* @__PURE__ */ (0, Y.jsx)(_e, {
				size: 20,
				"aria-hidden": "true"
			})]
		}), t.length ? /* @__PURE__ */ (0, Y.jsx)("ul", {
			className: "pipeline-health-list",
			children: t.map((e) => /* @__PURE__ */ (0, Y.jsxs)("li", { children: [
				/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: e.source }), /* @__PURE__ */ (0, Y.jsx)("span", { children: e.status || "Status unavailable" })] }),
				dL(e.jobs_returned) === null ? null : /* @__PURE__ */ (0, Y.jsxs)("span", { children: [fL(Number(e.jobs_returned)), " jobs"] }),
				e.last_success ? /* @__PURE__ */ (0, Y.jsx)("time", {
					dateTime: e.last_success,
					children: pL(e.last_success)
				}) : null
			] }, e.source))
		}) : /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "pipeline-source-unavailable",
			role: "status",
			children: [/* @__PURE__ */ (0, Y.jsx)(_e, {
				size: 18,
				"aria-hidden": "true"
			}), /* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: "Source health data is not available yet" }), /* @__PURE__ */ (0, Y.jsx)("span", { children: "No source status is inferred from missing job counts." })] })]
		})]
	});
}
function LL({ readStatus: e = wL, launchPipeline: t = TL, pollIntervalMs: n = iL }) {
	let r = EL(), i = (0, C.useRef)(r), [a, o] = (0, C.useState)(() => r ? {
		kind: "ready",
		payload: OL(r),
		checkedAt: Date.now()
	} : { kind: "loading" }), [s, c] = (0, C.useState)(!1), l = (0, C.useCallback)(async (t = !1) => {
		t && c(!0);
		try {
			var n, r;
			let t = await e(), a = i.current, s = String(((n = t.pipeline) == null ? void 0 : n.run_id) || "").trim();
			if (a && s !== a) {
				o({
					kind: "ready",
					payload: OL(a),
					checkedAt: Date.now()
				});
				return;
			}
			a && s === a && (i.current = "", DL(a)), o({
				kind: "ready",
				payload: t,
				checkedAt: Date.now()
			});
			let c = (r = t.pipeline) == null ? void 0 : r.status;
			lL(c) === "unavailable" && console.warn(`Unsupported pipeline status: ${String(c || "")}`);
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
				payload: OL(r, n.pipeline),
				checkedAt: Date.now()
			}), l());
		};
		return window.addEventListener(_L, e), () => window.removeEventListener(_L, e);
	}, [l]);
	let u = a.kind === "ready" && a.payload.pipeline || {}, d = lL(u.status), f = a.kind === "ready" && (d === "starting" || d === "running");
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
	return a.kind === "loading" ? /* @__PURE__ */ (0, Y.jsx)(kL, {}) : a.kind === "error" ? /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "pipeline-dashboard pipeline-dashboard--error",
		children: [/* @__PURE__ */ (0, Y.jsx)(AL, {
			onRefresh: () => void l(!0),
			onRun: t,
			refreshing: s,
			runActive: !1
		}), /* @__PURE__ */ (0, Y.jsxs)("section", {
			className: "pipeline-status-error",
			role: "alert",
			children: [
				/* @__PURE__ */ (0, Y.jsx)(ve, {
					size: 22,
					"aria-hidden": "true"
				}),
				/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("h2", { children: "Pipeline status is unavailable" }), /* @__PURE__ */ (0, Y.jsx)("p", { children: a.message })] }),
				/* @__PURE__ */ (0, Y.jsx)("button", {
					type: "button",
					onClick: () => void l(!0),
					children: "Retry"
				})
			]
		})]
	}) : /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: m,
		"data-theme-surface": "pipeline",
		"aria-busy": f,
		children: [
			/* @__PURE__ */ (0, Y.jsx)(AL, {
				onRefresh: () => void l(!0),
				onRun: t,
				refreshing: s,
				runActive: d === "starting" || d === "running"
			}),
			d === "idle" ? /* @__PURE__ */ (0, Y.jsxs)("section", {
				className: "pipeline-idle-banner",
				role: "status",
				children: [/* @__PURE__ */ (0, Y.jsx)(ie, {
					size: 20,
					"aria-hidden": "true"
				}), /* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: "Pipeline is idle" }), /* @__PURE__ */ (0, Y.jsx)("span", { children: "Start a run through the existing reviewed launch flow." })] })]
			}) : null,
			/* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "pipeline-dashboard-top-grid",
				children: [/* @__PURE__ */ (0, Y.jsx)(jL, {
					pipeline: u,
					checkedAt: p
				}), /* @__PURE__ */ (0, Y.jsx)(ML, { pipeline: u })]
			}),
			/* @__PURE__ */ (0, Y.jsx)(NL, { pipeline: u }),
			/* @__PURE__ */ (0, Y.jsx)(PL, { pipeline: u }),
			/* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "pipeline-dashboard-bottom-grid",
				children: [/* @__PURE__ */ (0, Y.jsx)(FL, { pipeline: u }), /* @__PURE__ */ (0, Y.jsx)(IL, { pipeline: u })]
			})
		]
	});
}
//#endregion
//#region src/PlanningWorklist.tsx
var RL = "applylens:planning-worklist-state", zL = "applylens:planning-worklist-action", BL = "applylens.planning.columnWidths.v1", VL = {
	status: "loading",
	rows: [],
	metaLabel: "Planning view · loading",
	pagination: {
		page: 1,
		pageSize: 15,
		totalCount: 0,
		totalPages: 1,
		hasPrevPage: !1,
		hasNextPage: !1
	},
	sort: {
		key: "",
		direction: "asc"
	},
	resultKey: "initial",
	metrics: {
		total: 0,
		readyForReview: 0,
		packetReady: 0,
		needsDecision: 0
	},
	filters: {
		actions: [],
		winnerBuckets: [],
		tailoringStates: [],
		preferenceIds: [],
		undecidedOnly: !1,
		limit: 15
	},
	preferenceOptions: []
}, HL = [
	{
		value: "APPLY",
		label: "Ready for review",
		tone: "ready"
	},
	{
		value: "APPLY_REVIEW_VARIANTS",
		label: "Review resume choice",
		tone: "choice"
	},
	{
		value: "MAYBE_TAILOR",
		label: "Tailor first",
		tone: "tailor"
	},
	{
		value: "SKIP_FOR_NOW",
		label: "Review later",
		tone: "later"
	}
], UL = [
	{
		value: "strong",
		label: "Excellent match",
		tone: "strong"
	},
	{
		value: "solid",
		label: "Strong match",
		tone: "solid"
	},
	{
		value: "moderate",
		label: "Moderate match",
		tone: "moderate"
	},
	{
		value: "weak",
		label: "Weak match",
		tone: "weak"
	},
	{
		value: "filtered_out",
		label: "No credible match",
		tone: "unavailable"
	}
], WL = [
	{
		value: "ready",
		label: "Ready",
		tone: "ready"
	},
	{
		value: "review",
		label: "Review",
		tone: "choice"
	},
	{
		value: "no_safe_rewrites",
		label: "No safe rewrites",
		tone: "later"
	},
	{
		value: "unavailable",
		label: "Unavailable",
		tone: "unavailable"
	}
], GL = {
	queue_rank: {
		min: 72,
		max: 110
	},
	job_title: {
		min: 210,
		max: 420
	},
	posted_at: {
		min: 112,
		max: 180
	},
	recommendation: {
		min: 150,
		max: 260
	},
	winner_score: {
		min: 112,
		max: 180
	},
	selected_resume: {
		min: 200,
		max: 360
	},
	packet_status: {
		min: 160,
		max: 280
	}
};
function KL(e) {
	window.dispatchEvent(new CustomEvent(zL, { detail: e }));
}
function Q(e) {
	return String(e == null ? "" : e).trim();
}
function qL(e) {
	let t = Q(e).replace(/_/g, " ");
	return t ? t.charAt(0).toUpperCase() + t.slice(1) : "Unavailable";
}
function JL(e) {
	let t = Q(e);
	return t ? t.replace(/\.pdf$/i, "").replace(/_/g, " ") : "Not selected";
}
function YL(e) {
	return Q(e.operator_selected_resume || e.selected_resume || e.winner_resume);
}
function XL(e) {
	let t = Q(e);
	if (!t) return "Unavailable";
	let n = new Date(t);
	return Number.isNaN(n.getTime()) ? t : new Intl.DateTimeFormat(void 0, {
		month: "short",
		day: "numeric",
		year: "numeric"
	}).format(n);
}
function ZL(e) {
	return {
		APPLY: {
			label: "Ready for review",
			tone: "ready"
		},
		APPLY_REVIEW_VARIANTS: {
			label: "Review resume choice",
			tone: "choice"
		},
		MAYBE_TAILOR: {
			label: "Tailor first",
			tone: "tailor"
		},
		SKIP_FOR_NOW: {
			label: "Review later",
			tone: "later"
		}
	}[Q(e.action).toUpperCase()] || {
		label: Q(e.action) || "Unavailable",
		tone: "unavailable"
	};
}
function QL(e) {
	let t = Q(e).toLowerCase();
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
	].includes(t) ? "No packet" : "Packet unavailable";
}
function $L() {
	try {
		let e = JSON.parse(localStorage.getItem("applylens.planning.columnWidths.v1") || "{}");
		if (!e || typeof e != "object" || Array.isArray(e)) return {};
		let t = "version" in e && e.version === 1 ? e.widths : e;
		return !t || typeof t != "object" || Array.isArray(t) ? {} : Object.fromEntries(Object.entries(t).flatMap(([e, t]) => {
			let n = GL[e], r = Number(t);
			return !n || !Number.isFinite(r) ? [] : [[e, Math.min(n.max, Math.max(n.min, r))]];
		}));
	} catch (e) {
		return {};
	}
}
function eR(e) {
	localStorage.setItem(BL, JSON.stringify({
		version: 1,
		widths: e
	}));
}
function tR(e, t) {
	return Q(e.job_doc_id || e.job_url || e.queue_rank) || `planning-row-${t}`;
}
function nR(e) {
	if (e && typeof e == "object" && !Array.isArray(e)) return e;
	let t = Q(e);
	if (!t) return null;
	try {
		let e = JSON.parse(t);
		return e && typeof e == "object" && !Array.isArray(e) ? e : null;
	} catch (e) {
		return null;
	}
}
function rR({ row: e }) {
	let t = nR(e.llm_adjudicator_readback), n = Q((t == null ? void 0 : t.status) || e.llm_adjudicator_readback_status || "Unavailable"), r = Array.isArray(t == null ? void 0 : t.candidate_resume_names) ? t.candidate_resume_names.map(Q).filter(Boolean).join(", ") : "", i = [
		["Status", qL(n)],
		["Provider", Q((t == null ? void 0 : t.provider_used) || (t == null ? void 0 : t.provider_requested))],
		["Model", Q((t == null ? void 0 : t.model_used) || (t == null ? void 0 : t.model_requested))],
		["Candidates", r],
		["Recommendation", Q(t == null ? void 0 : t.adjudicator_recommendation_label)],
		["Summary", Q(t == null ? void 0 : t.adjudicator_summary)]
	].filter((e) => e[1]);
	return /* @__PURE__ */ (0, Y.jsxs)("details", {
		className: "planning-react-ai-review",
		children: [
			/* @__PURE__ */ (0, Y.jsx)("summary", { children: "View AI Review" }),
			/* @__PURE__ */ (0, Y.jsx)("dl", { children: i.map(([e, t]) => /* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("dt", { children: e }), /* @__PURE__ */ (0, Y.jsx)("dd", { children: t })] }, e)) }),
			/* @__PURE__ */ (0, Y.jsx)("p", { children: "Advisory only. Does not override the selected resume or score." })
		]
	});
}
function iR({ row: e }) {
	let t = [
		"true",
		"1",
		"yes",
		"on"
	].includes(Q(e.llm_adjudicator_readback_enabled).toLowerCase());
	return /* @__PURE__ */ (0, Y.jsxs)(kI, { children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "planning-react-details-grid",
		children: [
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Full location" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: Q(e.job_location) || "Unavailable" })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Prefilter relevance" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: qL(e.selection_signal) })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "AI evaluation" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: qL(e.llm_adjudicator_readback_status) })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Runner-up resume" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: JL(e.runner_up_resume || e.runnerup_resume) })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Runner-up score" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: Q(e.runner_up_score) || "Unavailable" })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Score gap" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: Q(e.score_gap) || "Unavailable" })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Operator decision" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: qL(e.operator_decision || "Not decided") })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Priority reason" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: Q(e.queue_priority_reason) || "Unavailable" })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Missing requirements" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: Q(e.missing_requirement_count) || "0" })] })
		]
	}), t ? /* @__PURE__ */ (0, Y.jsx)(rR, { row: e }) : null] });
}
function aR() {
	return [
		{
			id: "expand",
			header: "",
			size: 42,
			minSize: 42,
			maxSize: 42,
			enableSorting: !1,
			enableResizing: !1,
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)(TI, {
				expanded: e.getIsExpanded(),
				label: `${e.getIsExpanded() ? "Collapse" : "Expand"} planning details for ${Q(e.original.job_title) || "job"}`,
				controls: `planning-react-detail-${e.id}`,
				onClick: e.getToggleExpandedHandler()
			})
		},
		{
			accessorKey: "queue_rank",
			header: "Rank",
			size: 78,
			minSize: 72,
			maxSize: 110
		},
		{
			id: "job_title",
			header: "Job",
			size: 270,
			minSize: 210,
			maxSize: 420,
			accessorFn: (e) => Q(e.job_title),
			cell: ({ row: e }) => {
				let t = Q(e.original.job_title) || "Untitled job", n = Q(e.original.job_company) || "Company unavailable", r = Q(e.original.job_location) || "Location unavailable", i = Q(e.original.job_url || e.original.job_doc_id);
				return /* @__PURE__ */ (0, Y.jsx)(OI, {
					title: t,
					location: r,
					children: /* @__PURE__ */ (0, Y.jsxs)("span", {
						className: "planning-react-job-cell",
						children: [i ? /* @__PURE__ */ (0, Y.jsx)("a", {
							href: i,
							target: "_blank",
							rel: "noreferrer",
							children: t
						}) : /* @__PURE__ */ (0, Y.jsx)("strong", { children: t }), /* @__PURE__ */ (0, Y.jsxs)("span", { children: [
							n,
							" · ",
							r
						] })]
					})
				});
			}
		},
		{
			id: "posted_at",
			header: "Posted at",
			size: 128,
			minSize: 112,
			maxSize: 180,
			accessorFn: (e) => e.posted_at ? new Date(e.posted_at).getTime() : null,
			sortUndefined: "last",
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)("time", {
				dateTime: Q(e.original.posted_at),
				children: XL(e.original.posted_at)
			})
		},
		{
			id: "recommendation",
			header: "Review readiness",
			size: 184,
			minSize: 150,
			maxSize: 260,
			accessorFn: (e) => ZL(e).label,
			cell: ({ row: e }) => {
				let t = ZL(e.original), n = [
					"true",
					"1",
					"yes",
					"on"
				].includes(Q(e.original.llm_adjudicator_readback_enabled).toLowerCase());
				return /* @__PURE__ */ (0, Y.jsxs)("span", {
					className: "planning-react-readiness",
					children: [/* @__PURE__ */ (0, Y.jsx)("span", {
						className: `planning-react-badge planning-react-badge--${t.tone}`,
						children: t.label
					}), n ? /* @__PURE__ */ (0, Y.jsx)("span", {
						className: "planning-react-advisory",
						children: "AI notes · advisory"
					}) : null]
				});
			}
		},
		{
			id: "winner_score",
			header: "Match score",
			size: 132,
			minSize: 112,
			maxSize: 180,
			accessorFn: (e) => e.winner_score,
			sortUndefined: "last",
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)(EI, {
				value: e.original.winner_score,
				strength: qL(e.original.winner_bucket)
			})
		},
		{
			id: "selected_resume",
			header: "Resume selection",
			size: 230,
			minSize: 200,
			maxSize: 360,
			accessorFn: YL,
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)("span", {
				className: "planning-react-resume",
				title: YL(e.original),
				children: JL(YL(e.original))
			})
		},
		{
			id: "packet_status",
			header: () => /* @__PURE__ */ (0, Y.jsxs)("span", {
				className: "planning-react-packet-header",
				children: ["Packet / workspace", /* @__PURE__ */ (0, Y.jsx)(DI, {
					label: "About packet and workspace status",
					children: "A packet is a review bundle for this job. It does not apply to the job."
				})]
			}),
			size: 188,
			minSize: 160,
			maxSize: 280,
			accessorFn: (e) => QL(e.packet_generation_allowed),
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsxs)("span", {
				className: "planning-react-status-stack",
				children: [/* @__PURE__ */ (0, Y.jsx)("span", {
					className: `planning-react-badge ${QL(e.original.packet_generation_allowed) === "Packet ready" ? "is-ready" : ""}`,
					children: QL(e.original.packet_generation_allowed)
				}), /* @__PURE__ */ (0, Y.jsx)("span", { children: qL(e.original.tailoring_workspace_state || "Workspace unavailable") })]
			})
		},
		{
			id: "next_step",
			header: "Next step",
			size: 190,
			minSize: 190,
			maxSize: 190,
			enableSorting: !1,
			enableResizing: !1,
			cell: ({ row: e }) => {
				let t = e.original.__planning_action || {
					kind: "unavailable",
					label: "Unavailable",
					disabled: !0,
					title: "No action available."
				};
				return /* @__PURE__ */ (0, Y.jsx)("button", {
					type: "button",
					className: `planning-react-next-step ${t.kind === "generate_suggestions" ? "is-primary" : ""}`,
					disabled: t.disabled,
					title: t.title,
					onClick: () => KL({
						type: "next_step",
						row: e.original
					}),
					children: t.label
				});
			}
		}
	];
}
function oR({ state: e }) {
	let [t, n] = (0, C.useState)(e.filters);
	(0, C.useEffect)(() => n(e.filters), [e.filters]);
	let r = (e) => {
		n(e), KL({
			type: "filters_change",
			filters: e
		});
	}, i = e.preferenceOptions.map((e) => ({
		value: e.role_family_id,
		label: e.display_name || e.role_family_id
	}));
	return /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "planning-react-filter-grid",
		"aria-label": "Planning filters",
		children: [
			/* @__PURE__ */ (0, Y.jsx)(CI, {
				id: "planningActionFilter",
				label: "Action",
				options: HL,
				values: t.actions,
				onChange: (e) => r({
					...t,
					actions: e
				}),
				placeholder: "All",
				mode: "single"
			}),
			/* @__PURE__ */ (0, Y.jsx)(CI, {
				id: "planningPreferenceFilter",
				label: "Preferences",
				options: i,
				values: t.preferenceIds,
				onChange: (e) => r({
					...t,
					preferenceIds: e
				}),
				placeholder: "All Preferences",
				allLabel: "All Preferences",
				searchable: !0,
				mode: "multiple"
			}),
			/* @__PURE__ */ (0, Y.jsx)(CI, {
				id: "planningWinnerBucket",
				label: "Match Strength",
				options: UL,
				values: t.winnerBuckets,
				onChange: (e) => r({
					...t,
					winnerBuckets: e
				}),
				placeholder: "All",
				mode: "single"
			}),
			/* @__PURE__ */ (0, Y.jsx)(CI, {
				id: "planningTailoringFilter",
				label: "Tailoring",
				options: WL,
				values: t.tailoringStates,
				onChange: (e) => r({
					...t,
					tailoringStates: e
				}),
				placeholder: "All",
				mode: "single"
			}),
			/* @__PURE__ */ (0, Y.jsxs)("fieldset", {
				className: "planning-react-undecided-field",
				children: [/* @__PURE__ */ (0, Y.jsx)("legend", { children: "Undecided only" }), /* @__PURE__ */ (0, Y.jsxs)("div", {
					className: "planning-react-segmented",
					role: "radiogroup",
					"aria-label": "Planning undecided only",
					children: [/* @__PURE__ */ (0, Y.jsx)("button", {
						type: "button",
						"aria-pressed": !t.undecidedOnly,
						className: `${wI} ${t.undecidedOnly ? "" : "is-active"}`.trim(),
						onClick: () => r({
							...t,
							undecidedOnly: !1
						}),
						children: "No"
					}), /* @__PURE__ */ (0, Y.jsx)("button", {
						type: "button",
						"aria-pressed": t.undecidedOnly,
						className: `${wI} ${t.undecidedOnly ? "is-active" : ""}`.trim(),
						onClick: () => r({
							...t,
							undecidedOnly: !0
						}),
						children: "Yes"
					})]
				})]
			}),
			/* @__PURE__ */ (0, Y.jsxs)("label", {
				className: "planning-react-limit-field",
				htmlFor: "planningLimitInput",
				children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Limit" }), /* @__PURE__ */ (0, Y.jsx)("input", {
					id: "planningLimitInput",
					type: "number",
					min: 1,
					max: 100,
					value: t.limit,
					onChange: (e) => r({
						...t,
						limit: Math.min(100, Math.max(1, Number(e.target.value) || 15))
					})
				})]
			}),
			/* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "planning-react-filter-actions",
				children: [/* @__PURE__ */ (0, Y.jsx)("button", {
					type: "button",
					className: "planning-filter-apply",
					id: "planningApplyFiltersBtn",
					onClick: () => KL({
						type: "apply_filters",
						filters: t
					}),
					children: "Apply Filters"
				}), /* @__PURE__ */ (0, Y.jsx)("button", {
					type: "button",
					className: "planning-filter-clear",
					id: "planningClearFiltersBtn",
					onClick: () => KL({ type: "clear_filters" }),
					children: "Clear"
				})]
			})
		]
	});
}
function sR({ state: e }) {
	let [t, n] = (0, C.useState)($L), [r, i] = (0, C.useState)(""), a = (0, C.useMemo)(aR, []), o = (0, C.useMemo)(() => e.rows.slice(), [e.rows]), s = (0, C.useMemo)(() => e.sort.key ? [{
		id: e.sort.key,
		desc: e.sort.direction === "desc"
	}] : [], [e.sort]);
	(0, C.useEffect)(() => i(""), [
		e.resultKey,
		e.pagination.page,
		e.sort.key,
		e.sort.direction
	]);
	let c = bI({
		data: o,
		columns: a,
		state: {
			sorting: s,
			columnSizing: t,
			expanded: r ? { [r]: !0 } : {}
		},
		getRowId: tR,
		onSortingChange: (e) => {
			let t = (typeof e == "function" ? e(s) : e)[0];
			t && (i(""), KL({
				type: "sort_change",
				key: t.id,
				direction: t.desc ? "desc" : "asc"
			}));
		},
		onColumnSizingChange: (e) => {
			n((t) => {
				let n = typeof e == "function" ? e(t) : e;
				return eR(n), n;
			});
		},
		onExpandedChange: (e) => {
			let t = r ? { [r]: !0 } : {}, n = typeof e == "function" ? e(t) : e, a = n === !0 ? t : n, o = Object.keys(a).find((e) => a[e] && !t[e]);
			i(o || Object.keys(a).find((e) => a[e]) || "");
		},
		getRowCanExpand: () => !0,
		getCoreRowModel: mI(),
		manualSorting: !0,
		enableSortingRemoval: !1,
		columnResizeMode: "onChange"
	});
	return /* @__PURE__ */ (0, Y.jsx)(NI, {
		className: "planning-react-table-card",
		ariaLabel: "Planning worklist table",
		title: "Planning worklist",
		subtitle: `Planning view · ${e.pagination.totalCount} total job${e.pagination.totalCount === 1 ? "" : "s"}`,
		count: e.pagination.totalCount,
		table: c,
		columns: a,
		status: e.status,
		error: e.message,
		pagination: e.pagination,
		paginationLabel: "Planning worklist",
		stickyColumnId: "next_step",
		rowClassName: (e, t) => `planning-react-row ${t % 2 ? "is-alternate" : ""} ${e.getIsExpanded() ? "is-expanded" : ""}`.trim(),
		detailId: (e) => `planning-react-detail-${e.id}`,
		renderDetails: (e) => /* @__PURE__ */ (0, Y.jsx)(iR, { row: e.original }),
		empty: /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "planning-react-empty",
			children: [
				/* @__PURE__ */ (0, Y.jsx)("strong", { children: "No planning rows match these filters" }),
				/* @__PURE__ */ (0, Y.jsx)("span", { children: "Clear the current filters to return to the complete planning worklist." }),
				/* @__PURE__ */ (0, Y.jsx)("button", {
					type: "button",
					className: wI,
					onClick: () => KL({ type: "clear_filters" }),
					children: "Clear filters"
				})
			]
		}),
		onPageChange: (e) => KL({
			type: "page_change",
			page: e
		}),
		onRetry: () => KL({ type: "retry" })
	});
}
var cR = [
	{
		key: "total",
		label: "Total results",
		caption: "Across all result pages",
		help: "All planning rows matching the applied filters.",
		icon: re
	},
	{
		key: "readyForReview",
		label: "Ready for review",
		caption: "On this page",
		help: "Rows on this page whose current recommendation is ready for review.",
		icon: ee
	},
	{
		key: "packetReady",
		label: "Packet ready",
		caption: "On this page",
		help: "Rows on this page with an explicitly ready planning packet.",
		icon: oe
	},
	{
		key: "needsDecision",
		label: "Needs decision",
		caption: "Operator attention",
		help: "Rows on this page that do not yet have an operator decision.",
		icon: ye
	}
];
function lR({ state: e }) {
	return /* @__PURE__ */ (0, Y.jsx)("section", {
		className: "planning-react-summary-grid",
		"aria-label": "Planning summary",
		children: cR.map((t) => {
			let n = t.icon;
			return /* @__PURE__ */ (0, Y.jsxs)("article", {
				className: `planning-react-summary-card planning-react-summary-card--${t.key}`,
				children: [
					/* @__PURE__ */ (0, Y.jsxs)("div", {
						className: "planning-react-summary-topline",
						children: [/* @__PURE__ */ (0, Y.jsxs)("span", {
							className: "planning-react-summary-heading",
							children: [/* @__PURE__ */ (0, Y.jsx)(n, {
								size: 18,
								"aria-hidden": "true"
							}), /* @__PURE__ */ (0, Y.jsx)("span", { children: t.label })]
						}), /* @__PURE__ */ (0, Y.jsx)(DI, {
							label: `About ${t.label.toLowerCase()}`,
							children: t.help
						})]
					}),
					/* @__PURE__ */ (0, Y.jsx)("strong", { children: e.metrics[t.key] }),
					/* @__PURE__ */ (0, Y.jsx)("span", { children: t.caption })
				]
			}, t.key);
		})
	});
}
//#endregion
//#region src/OperationalDashboards.tsx
var uR = "applylens:decisions-dashboard-state", dR = "applylens:decisions-dashboard-action", fR = "applylens:decisions-dashboard-ready", pR = "applylens:applications-dashboard-state", mR = "applylens:applications-dashboard-action", hR = "applylens:applications-dashboard-ready", gR = "applylens.decisions.columnWidths.v1", _R = "applylens.applications.columnWidths.v1", vR = {
	status: "loading",
	rows: [],
	metaLabel: "Loading...",
	resultKey: "initial",
	pagination: {
		page: 1,
		pageSize: 15,
		totalCount: 0,
		totalPages: 1,
		hasPrevPage: !1,
		hasNextPage: !1
	},
	sort: {
		key: "",
		direction: "asc"
	},
	filters: {
		decisions: [],
		companyContains: "",
		limit: 15
	}
}, yR = {
	status: "loading",
	rows: [],
	metaLabel: "Loading...",
	resultKey: "initial",
	activeTab: "APPLIED",
	pagination: {
		page: 1,
		pageSize: 15,
		totalCount: 0,
		totalPages: 1,
		hasPrevPage: !1,
		hasNextPage: !1
	},
	sort: {
		key: "",
		direction: "asc"
	},
	filters: {
		companyContains: "",
		titleContains: "",
		limit: 15
	}
}, bR = [
	"APPLY",
	"TAILOR",
	"SKIP",
	"HOLD"
].map((e) => ({
	value: e,
	label: e
})), $ = (e) => String(e == null ? "" : e).trim(), xR = (e, t = "Unavailable") => $(e) || t, SR = (e) => {
	let t = $(e);
	if (!t) return "Unavailable";
	let n = new Date(t);
	return Number.isNaN(n.getTime()) ? t : new Intl.DateTimeFormat(void 0, {
		month: "short",
		day: "numeric",
		year: "numeric",
		hour: "numeric",
		minute: "2-digit"
	}).format(n);
}, CR = (e, t) => $(e.action_key) || [
	$(e.decision_timestamp || e.action_timestamp),
	$(e.job_doc_id || e.job_url),
	$(e.decision || e.application_status),
	t
].join("|"), wR = (e) => e.key ? [{
	id: e.key,
	desc: e.direction === "desc"
}] : [];
function TR(e, t) {
	window.dispatchEvent(new CustomEvent(e, { detail: t }));
}
function ER(e) {
	try {
		let t = JSON.parse(localStorage.getItem(e) || "{}"), n = (t == null ? void 0 : t.version) === 1 ? t.widths : t;
		return n && typeof n == "object" && !Array.isArray(n) ? n : {};
	} catch (e) {
		return {};
	}
}
function DR(e, t) {
	localStorage.setItem(e, JSON.stringify({
		version: 1,
		widths: t
	}));
}
function OR(e, t) {
	let n = xR(e);
	return /* @__PURE__ */ (0, Y.jsx)("span", {
		className: `${t}-badge ${t}-badge--${$(e).toLowerCase().replace(/[^a-z0-9]+/g, "-") || "unknown"}`,
		children: n
	});
}
function kR({ cards: e, label: t, loading: n = !1 }) {
	return /* @__PURE__ */ (0, Y.jsx)("section", {
		className: "operational-summary-grid",
		"aria-label": t,
		children: e.map(({ label: e, value: t, caption: r, help: i, icon: a }) => /* @__PURE__ */ (0, Y.jsxs)("article", {
			className: "operational-summary-card",
			children: [
				/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsxs)("span", { children: [/* @__PURE__ */ (0, Y.jsx)(a, {
					size: 17,
					"aria-hidden": "true"
				}), e] }), /* @__PURE__ */ (0, Y.jsx)(DI, {
					label: `About ${e.toLowerCase()}`,
					children: i
				})] }),
				/* @__PURE__ */ (0, Y.jsx)("strong", { children: n ? "-" : t }),
				/* @__PURE__ */ (0, Y.jsx)("small", { children: n ? "Loading snapshot" : r })
			]
		}, e))
	});
}
function AR({ state: e }) {
	let [t, n] = (0, C.useState)(e.filters);
	return (0, C.useEffect)(() => n(e.filters), [e.filters]), /* @__PURE__ */ (0, Y.jsx)("section", {
		className: "operational-filter-card",
		"aria-label": "Decision filters",
		children: /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "operational-filter-grid decisions-filter-grid",
			children: [
				/* @__PURE__ */ (0, Y.jsx)(CI, {
					id: "decisionFilter",
					label: "Decision",
					options: bR,
					values: t.decisions,
					onChange: (e) => n({
						...t,
						decisions: e
					}),
					placeholder: "All",
					allLabel: "All",
					mode: "multiple"
				}),
				/* @__PURE__ */ (0, Y.jsxs)("label", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Company contains" }), /* @__PURE__ */ (0, Y.jsx)("input", {
					id: "decisionCompanyFilter",
					value: t.companyContains,
					placeholder: "e.g. Waymo",
					onChange: (e) => n({
						...t,
						companyContains: e.target.value
					})
				})] }),
				/* @__PURE__ */ (0, Y.jsxs)("label", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Limit" }), /* @__PURE__ */ (0, Y.jsx)("input", {
					id: "decisionLimitInput",
					type: "number",
					min: 1,
					max: 300,
					value: t.limit,
					onChange: (e) => n({
						...t,
						limit: Math.min(300, Math.max(1, Number(e.target.value) || 15))
					})
				})] }),
				/* @__PURE__ */ (0, Y.jsxs)("div", {
					className: "operational-filter-actions",
					children: [/* @__PURE__ */ (0, Y.jsx)("button", {
						id: "decisionApplyFiltersBtn",
						className: "operational-primary-action",
						onClick: () => TR(dR, {
							type: "apply_filters",
							filters: t
						}),
						children: "Apply Filters"
					}), /* @__PURE__ */ (0, Y.jsx)("button", {
						id: "decisionClearFiltersBtn",
						className: `${wI} operational-secondary-action`,
						onClick: () => TR(dR, { type: "clear_filters" }),
						children: "Clear"
					})]
				})
			]
		})
	});
}
function jR({ row: e }) {
	return /* @__PURE__ */ (0, Y.jsx)(kI, { children: /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "operational-detail-grid",
		children: [
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Queue rank" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: xR(e.queue_rank) })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Posted at" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: SR(e.posted_at) })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Winner resume" }), /* @__PURE__ */ (0, Y.jsx)("strong", {
				title: $(e.winner_resume),
				children: xR(e.winner_resume)
			})] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Runner-up resume" }), /* @__PURE__ */ (0, Y.jsx)("strong", {
				title: $(e.runner_up_resume),
				children: xR(e.runner_up_resume)
			})] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Selected resume" }), /* @__PURE__ */ (0, Y.jsx)("strong", {
				title: $(e.selected_resume),
				children: xR(e.selected_resume)
			})] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Note" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: xR(e.note, "No note recorded") })] })
		]
	}) });
}
function MR() {
	return [
		{
			id: "expand",
			header: "",
			size: 42,
			minSize: 42,
			maxSize: 42,
			enableSorting: !1,
			enableResizing: !1,
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)(TI, {
				expanded: e.getIsExpanded(),
				label: `${e.getIsExpanded() ? "Collapse" : "Expand"} decision details for ${xR(e.original.job_title, "job")}`,
				controls: `decision-detail-${e.id}`,
				onClick: e.getToggleExpandedHandler()
			})
		},
		{
			id: "decision_timestamp",
			header: "Date / time",
			accessorFn: (e) => $(e.decision_timestamp),
			size: 156,
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)("time", {
				dateTime: $(e.original.decision_timestamp),
				children: SR(e.original.decision_timestamp)
			})
		},
		{
			id: "decision",
			header: "Decision",
			accessorFn: (e) => $(e.decision),
			size: 118,
			cell: ({ row: e }) => OR(e.original.decision, "operational")
		},
		{
			id: "job",
			header: "Job",
			accessorFn: (e) => $(e.job_title),
			size: 270,
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsxs)("span", {
				className: "operational-job-cell",
				children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: xR(e.original.job_title, "Untitled job") }), /* @__PURE__ */ (0, Y.jsx)("span", { children: xR(e.original.job_company, "Company unavailable") })]
			})
		},
		{
			id: "planning_action",
			header: "Planning action",
			accessorFn: (e) => $(e.planning_action),
			size: 150,
			cell: ({ row: e }) => xR(e.original.planning_action)
		},
		{
			id: "selected_resume",
			header: "Selected resume",
			accessorFn: (e) => $(e.selected_resume),
			size: 220,
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)("span", {
				className: "operational-truncate",
				title: $(e.original.selected_resume),
				children: xR(e.original.selected_resume)
			})
		},
		{
			id: "application_action",
			header: "Manual action",
			size: 150,
			minSize: 150,
			maxSize: 150,
			enableSorting: !1,
			enableResizing: !1,
			cell: ({ row: e }) => e.original.is_applied ? /* @__PURE__ */ (0, Y.jsx)("button", {
				disabled: !0,
				className: "operational-row-action is-complete",
				children: "Applied"
			}) : /* @__PURE__ */ (0, Y.jsx)("button", {
				className: "operational-row-action",
				onClick: () => TR(dR, {
					type: "open_application",
					row: e.original
				}),
				children: "Open job"
			})
		}
	];
}
function NR({ state: e }) {
	let [t, n] = (0, C.useState)(() => ER(gR)), [r, i] = (0, C.useState)(""), a = (0, C.useMemo)(MR, []), o = (0, C.useMemo)(() => wR(e.sort), [e.sort]);
	(0, C.useEffect)(() => i(""), [
		e.resultKey,
		e.pagination.page,
		e.sort
	]);
	let s = bI({
		data: e.rows,
		columns: a,
		state: {
			sorting: o,
			columnSizing: t,
			expanded: r ? { [r]: !0 } : {}
		},
		getRowId: CR,
		getCoreRowModel: mI(),
		getSortedRowModel: hI(),
		getRowCanExpand: () => !0,
		enableSortingRemoval: !1,
		columnResizeMode: "onChange",
		onSortingChange: (e) => {
			let t = (typeof e == "function" ? e(o) : e)[0];
			t && TR(dR, {
				type: "sort_change",
				key: t.id,
				direction: t.desc ? "desc" : "asc"
			});
		},
		onColumnSizingChange: (e) => n((t) => {
			let n = typeof e == "function" ? e(t) : e;
			return DR(gR, n), n;
		}),
		onExpandedChange: (e) => {
			let t = r ? { [r]: !0 } : {}, n = typeof e == "function" ? e(t) : e, a = n === !0 ? t : n;
			i(Object.keys(a).find((e) => a[e] && e !== r) || Object.keys(a).find((e) => a[e]) || "");
		}
	});
	return /* @__PURE__ */ (0, Y.jsx)(NI, {
		className: "operational-table-card decisions-table-card",
		ariaLabel: "Operator decisions table",
		title: "Operator decisions",
		subtitle: `Decision history · ${e.pagination.totalCount} total records`,
		count: e.pagination.totalCount,
		table: s,
		columns: a,
		status: e.status,
		error: e.message,
		pagination: e.pagination,
		paginationNoun: "records",
		paginationLabel: "Operator decisions",
		stickyColumnId: "application_action",
		rowClassName: (e, t) => `operational-row ${t % 2 ? "is-alternate" : ""}`,
		detailId: (e) => `decision-detail-${e.id}`,
		renderDetails: (e) => /* @__PURE__ */ (0, Y.jsx)(jR, { row: e.original }),
		empty: /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "operational-empty",
			children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: "No operator decisions match the current filters." }), /* @__PURE__ */ (0, Y.jsx)("button", {
				className: wI,
				onClick: () => TR(dR, { type: "clear_filters" }),
				children: "Clear filters"
			})]
		}),
		onPageChange: (e) => TR(dR, {
			type: "page_change",
			page: e
		}),
		onRetry: () => TR(dR, { type: "retry" }),
		fillAvailableWidth: !0,
		deferPaginationWhileLoading: !0
	});
}
function PR({ state: e }) {
	let t = e.rows, n = new Set(t.map((e) => $(e.job_doc_id || e.job_url || `${e.job_company}|${e.job_title}`)).filter(Boolean));
	return /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "operational-dashboard",
		children: [
			/* @__PURE__ */ (0, Y.jsx)(kR, {
				cards: [
					{
						label: "Total decisions",
						value: e.pagination.totalCount,
						caption: "Across filtered results",
						help: "All recorded decisions matching the applied filters.",
						icon: ne
					},
					{
						label: "Jobs touched",
						value: n.size,
						caption: "On this page",
						help: "Distinct jobs represented on the current page.",
						icon: A
					},
					{
						label: "Apply decisions",
						value: t.filter((e) => $(e.decision).toUpperCase() === "APPLY").length,
						caption: "On this page",
						help: "Current-page decisions recorded as APPLY.",
						icon: ee
					},
					{
						label: "Tailor decisions",
						value: t.filter((e) => $(e.decision).toUpperCase() === "TAILOR").length,
						caption: "On this page",
						help: "Current-page decisions recorded as TAILOR.",
						icon: oe
					}
				],
				label: "Decision summary",
				loading: e.status === "loading"
			}),
			/* @__PURE__ */ (0, Y.jsx)(AR, { state: e }),
			/* @__PURE__ */ (0, Y.jsx)(NR, { state: e })
		]
	});
}
function FR({ state: e }) {
	let [t, n] = (0, C.useState)(e.filters);
	(0, C.useEffect)(() => n(e.filters), [e.filters]);
	let r = (t) => {
		t !== e.activeTab && TR(mR, {
			type: "tab_change",
			tab: t
		});
	}, i = (e, t) => {
		e.key !== "ArrowLeft" && e.key !== "ArrowRight" || (e.preventDefault(), r(t === "APPLIED" ? "SAVED" : "APPLIED"));
	}, a = (e) => `${wI} applications-tab ${e ? "is-active" : "is-inactive"}`;
	return /* @__PURE__ */ (0, Y.jsxs)("section", {
		className: "operational-filter-card applications-filter-card",
		children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "applications-tabs",
			role: "tablist",
			"aria-label": "Application view",
			children: [/* @__PURE__ */ (0, Y.jsx)("button", {
				role: "tab",
				"aria-selected": e.activeTab === "APPLIED",
				tabIndex: e.activeTab === "APPLIED" ? 0 : -1,
				className: a(e.activeTab === "APPLIED"),
				onKeyDown: (e) => i(e, "APPLIED"),
				onClick: () => r("APPLIED"),
				children: "Applied Jobs"
			}), /* @__PURE__ */ (0, Y.jsx)("button", {
				role: "tab",
				"aria-selected": e.activeTab === "SAVED",
				tabIndex: e.activeTab === "SAVED" ? 0 : -1,
				className: a(e.activeTab === "SAVED"),
				onKeyDown: (e) => i(e, "SAVED"),
				onClick: () => r("SAVED"),
				children: "Saved for Later"
			})]
		}), /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "operational-filter-grid applications-filter-grid",
			children: [
				/* @__PURE__ */ (0, Y.jsxs)("label", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Company contains" }), /* @__PURE__ */ (0, Y.jsx)("input", {
					id: "applicationCompanyFilter",
					value: t.companyContains,
					onChange: (e) => n({
						...t,
						companyContains: e.target.value
					})
				})] }),
				/* @__PURE__ */ (0, Y.jsxs)("label", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Title contains" }), /* @__PURE__ */ (0, Y.jsx)("input", {
					id: "applicationTitleFilter",
					value: t.titleContains,
					onChange: (e) => n({
						...t,
						titleContains: e.target.value
					})
				})] }),
				/* @__PURE__ */ (0, Y.jsxs)("label", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Limit" }), /* @__PURE__ */ (0, Y.jsx)("input", {
					id: "applicationLimitInput",
					type: "number",
					min: 1,
					max: 100,
					value: t.limit,
					onChange: (e) => n({
						...t,
						limit: Math.min(100, Math.max(1, Number(e.target.value) || 15))
					})
				})] }),
				/* @__PURE__ */ (0, Y.jsxs)("div", {
					className: "operational-filter-actions",
					children: [/* @__PURE__ */ (0, Y.jsx)("button", {
						id: "applicationApplyFiltersBtn",
						className: "operational-primary-action",
						onClick: () => TR(mR, {
							type: "apply_filters",
							filters: t
						}),
						children: "Apply Filters"
					}), /* @__PURE__ */ (0, Y.jsx)("button", {
						id: "applicationClearFiltersBtn",
						className: `${wI} operational-secondary-action`,
						onClick: () => TR(mR, { type: "clear_filters" }),
						children: "Clear"
					})]
				})
			]
		})]
	});
}
function IR({ row: e }) {
	return /* @__PURE__ */ (0, Y.jsx)(kI, { children: /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "operational-detail-grid",
		children: [
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Complete timestamp" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: SR(e.action_timestamp) })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Source view" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: xR(e.source_view) })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "is-wide",
				children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Note" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: xR(e.note, "No note recorded") })]
			})
		]
	}) });
}
function LR() {
	return [
		{
			id: "expand",
			header: "",
			size: 42,
			minSize: 42,
			maxSize: 42,
			enableSorting: !1,
			enableResizing: !1,
			cell: ({ row: e }) => e.getCanExpand() ? /* @__PURE__ */ (0, Y.jsx)(TI, {
				expanded: e.getIsExpanded(),
				label: `${e.getIsExpanded() ? "Collapse" : "Expand"} application details for ${xR(e.original.job_title, "job")}`,
				controls: `application-detail-${e.id}`,
				onClick: e.getToggleExpandedHandler()
			}) : null
		},
		{
			id: "action_timestamp",
			header: "Date / time",
			accessorFn: (e) => $(e.action_timestamp),
			size: 156,
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)("time", { children: SR(e.original.action_timestamp) })
		},
		{
			id: "job",
			header: "Job",
			accessorFn: (e) => $(e.job_title),
			size: 300,
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsxs)("span", {
				className: "operational-job-cell",
				children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: xR(e.original.job_title, "Untitled job") }), /* @__PURE__ */ (0, Y.jsx)("span", { children: xR(e.original.job_company, "Company unavailable") })]
			})
		},
		{
			id: "application_status",
			header: "Status",
			accessorFn: (e) => $(e.application_status),
			size: 130,
			cell: ({ row: e }) => OR(e.original.application_status, "application")
		},
		{
			id: "source_view",
			header: "Source view",
			accessorFn: (e) => $(e.source_view),
			size: 140,
			cell: ({ row: e }) => xR(e.original.source_view)
		},
		{
			id: "note",
			header: "Note",
			accessorFn: (e) => $(e.note),
			size: 230,
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)("span", {
				className: "operational-truncate",
				title: $(e.original.note),
				children: xR(e.original.note, "No note")
			})
		},
		{
			id: "open",
			header: "Open",
			size: 112,
			minSize: 112,
			maxSize: 112,
			enableSorting: !1,
			enableResizing: !1,
			cell: ({ row: e }) => {
				let t = $(e.original.job_url || e.original.job_doc_id);
				return t ? /* @__PURE__ */ (0, Y.jsx)("a", {
					className: "operational-row-action",
					href: t,
					target: "_blank",
					rel: "noopener noreferrer",
					children: "Open job"
				}) : /* @__PURE__ */ (0, Y.jsx)("button", {
					className: "operational-row-action",
					disabled: !0,
					children: "Unavailable"
				});
			}
		}
	];
}
function RR({ state: e }) {
	let [t, n] = (0, C.useState)(() => ER(_R)), [r, i] = (0, C.useState)(""), a = (0, C.useMemo)(LR, []), o = (0, C.useMemo)(() => wR(e.sort), [e.sort]);
	(0, C.useEffect)(() => i(""), [
		e.resultKey,
		e.activeTab,
		e.pagination.page,
		e.sort
	]);
	let s = bI({
		data: e.rows,
		columns: a,
		state: {
			sorting: o,
			columnSizing: t,
			expanded: r ? { [r]: !0 } : {}
		},
		getRowId: CR,
		getCoreRowModel: mI(),
		getSortedRowModel: hI(),
		getRowCanExpand: (e) => !!$(e.original.note),
		enableSortingRemoval: !1,
		columnResizeMode: "onChange",
		onSortingChange: (e) => {
			let t = (typeof e == "function" ? e(o) : e)[0];
			t && TR(mR, {
				type: "sort_change",
				key: t.id,
				direction: t.desc ? "desc" : "asc"
			});
		},
		onColumnSizingChange: (e) => n((t) => {
			let n = typeof e == "function" ? e(t) : e;
			return DR(_R, n), n;
		}),
		onExpandedChange: (e) => {
			let t = r ? { [r]: !0 } : {}, n = typeof e == "function" ? e(t) : e, a = n === !0 ? t : n;
			i(Object.keys(a).find((e) => a[e] && e !== r) || Object.keys(a).find((e) => a[e]) || "");
		}
	}), c = e.activeTab === "APPLIED" ? "Applied Jobs" : "Saved for Later", l = e.activeTab === "APPLIED" ? "No applied jobs yet." : "No jobs have been saved for later.";
	return /* @__PURE__ */ (0, Y.jsx)(NI, {
		className: "operational-table-card applications-table-card",
		ariaLabel: `${c} table`,
		title: c,
		subtitle: `Application tracking · ${e.pagination.totalCount} total jobs`,
		count: e.pagination.totalCount,
		table: s,
		columns: a,
		status: e.status,
		error: e.message,
		pagination: e.pagination,
		paginationLabel: c,
		stickyColumnId: "open",
		rowClassName: (e, t) => `operational-row ${t % 2 ? "is-alternate" : ""}`,
		detailId: (e) => `application-detail-${e.id}`,
		renderDetails: (e) => /* @__PURE__ */ (0, Y.jsx)(IR, { row: e.original }),
		empty: /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "operational-empty",
			children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: l }), /* @__PURE__ */ (0, Y.jsx)("span", { children: e.activeTab === "APPLIED" ? "Applied jobs will appear after an explicit manual status update." : "Jobs explicitly saved for later will appear here." })]
		}),
		onPageChange: (e) => TR(mR, {
			type: "page_change",
			page: e
		}),
		onRetry: () => TR(mR, { type: "retry" }),
		fillAvailableWidth: !0,
		deferPaginationWhileLoading: !0
	});
}
function zR({ state: e }) {
	return /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "operational-dashboard",
		children: [
			/* @__PURE__ */ (0, Y.jsx)(kR, {
				cards: [
					{
						label: "Current view",
						value: e.pagination.totalCount,
						caption: e.activeTab === "APPLIED" ? "Applied jobs" : "Saved jobs",
						help: "All jobs in the active view matching the applied filters.",
						icon: se
					},
					{
						label: "Current page",
						value: e.rows.length,
						caption: "Visible jobs",
						help: "Jobs returned on the current server page.",
						icon: A
					},
					{
						label: "With notes",
						value: e.rows.filter((e) => $(e.note)).length,
						caption: "On this page",
						help: "Current-page jobs with a recorded operator note.",
						icon: oe
					},
					{
						label: "Companies",
						value: new Set(e.rows.map((e) => $(e.job_company)).filter(Boolean)).size,
						caption: "On this page",
						help: "Distinct companies represented on the current page.",
						icon: be
					}
				],
				label: "Application summary",
				loading: e.status === "loading"
			}),
			/* @__PURE__ */ (0, Y.jsx)(FR, { state: e }),
			/* @__PURE__ */ (0, Y.jsx)(RR, { state: e })
		]
	});
}
//#endregion
//#region src/main.tsx
var BR = "applylens:executive-kpi-state", VR = { status: "loading" };
function HR() {
	let [e, t] = (0, C.useState)(() => window.__APPLYLENS_EXECUTIVE_KPI_STATE__ || VR);
	return (0, C.useEffect)(() => {
		let e = (e) => {
			let n = e.detail;
			n != null && n.status && t(n);
		};
		return window.addEventListener(BR, e), () => window.removeEventListener(BR, e);
	}, []), /* @__PURE__ */ (0, Y.jsx)($P, { state: e });
}
function UR() {
	let [e, t] = (0, C.useState)(() => window.__APPLYLENS_EXECUTIVE_QUEUE_STATE__ || RI);
	return (0, C.useEffect)(() => {
		let e = (e) => {
			let n = e.detail;
			n != null && n.status && t(n);
		};
		return window.addEventListener(PI, e), () => window.removeEventListener(PI, e);
	}, []), /* @__PURE__ */ (0, Y.jsx)(rL, { state: e });
}
function WR({ view: e }) {
	let [t, n] = (0, C.useState)(() => window.__APPLYLENS_PLANNING_WORKLIST_STATE__ || VL);
	return (0, C.useEffect)(() => {
		let e = (e) => {
			let t = e.detail;
			t != null && t.status && n(t);
		};
		return window.addEventListener(RL, e), () => window.removeEventListener(RL, e);
	}, []), e === "filters" ? /* @__PURE__ */ (0, Y.jsx)(oR, { state: t }) : e === "summary" ? /* @__PURE__ */ (0, Y.jsx)(lR, { state: t }) : /* @__PURE__ */ (0, Y.jsx)(sR, { state: t });
}
function GR() {
	let [e, t] = (0, C.useState)(() => window.__APPLYLENS_DECISIONS_STATE__ || vR);
	return (0, C.useEffect)(() => {
		let e = (e) => t(e.detail);
		return window.addEventListener(uR, e), window.__APPLYLENS_DECISIONS_REACT_READY__ = !0, window.__APPLYLENS_DECISIONS_STATE__ && t(window.__APPLYLENS_DECISIONS_STATE__), window.dispatchEvent(new CustomEvent(fR)), () => window.removeEventListener(uR, e);
	}, []), /* @__PURE__ */ (0, Y.jsx)(PR, { state: e });
}
function KR() {
	let [e, t] = (0, C.useState)(() => window.__APPLYLENS_APPLICATIONS_STATE__ || yR);
	return (0, C.useEffect)(() => {
		let e = (e) => t(e.detail);
		return window.addEventListener(pR, e), window.__APPLYLENS_APPLICATIONS_REACT_READY__ = !0, window.__APPLYLENS_APPLICATIONS_STATE__ && t(window.__APPLYLENS_APPLICATIONS_STATE__), window.dispatchEvent(new CustomEvent(hR)), () => window.removeEventListener(pR, e);
	}, []), /* @__PURE__ */ (0, Y.jsx)(zR, { state: e });
}
var qR = document.getElementById("executiveKpiRoot");
qR && (0, GP.createRoot)(qR).render(/* @__PURE__ */ (0, Y.jsx)(C.StrictMode, { children: /* @__PURE__ */ (0, Y.jsx)(HR, {}) }));
var JR = document.getElementById("executiveQueueRoot");
JR && (0, GP.createRoot)(JR).render(/* @__PURE__ */ (0, Y.jsx)(C.StrictMode, { children: /* @__PURE__ */ (0, Y.jsx)(UR, {}) }));
var YR = document.getElementById("pipelineDashboardRoot");
YR && (0, GP.createRoot)(YR).render(/* @__PURE__ */ (0, Y.jsx)(C.StrictMode, { children: /* @__PURE__ */ (0, Y.jsx)(LL, {}) }));
var XR = document.getElementById("planningSummaryRoot");
XR && (0, GP.createRoot)(XR).render(/* @__PURE__ */ (0, Y.jsx)(C.StrictMode, { children: /* @__PURE__ */ (0, Y.jsx)(WR, { view: "summary" }) }));
var ZR = document.getElementById("planningFiltersRoot");
ZR && (0, GP.createRoot)(ZR).render(/* @__PURE__ */ (0, Y.jsx)(C.StrictMode, { children: /* @__PURE__ */ (0, Y.jsx)(WR, { view: "filters" }) }));
var QR = document.getElementById("planningWorklistRoot");
QR && (0, GP.createRoot)(QR).render(/* @__PURE__ */ (0, Y.jsx)(C.StrictMode, { children: /* @__PURE__ */ (0, Y.jsx)(WR, { view: "worklist" }) }));
var $R = document.getElementById("decisionsDashboardRoot");
$R && (0, GP.createRoot)($R).render(/* @__PURE__ */ (0, Y.jsx)(C.StrictMode, { children: /* @__PURE__ */ (0, Y.jsx)(GR, {}) }));
var ez = document.getElementById("applicationsDashboardRoot");
ez && (0, GP.createRoot)(ez).render(/* @__PURE__ */ (0, Y.jsx)(C.StrictMode, { children: /* @__PURE__ */ (0, Y.jsx)(KR, {}) }));
//#endregion
