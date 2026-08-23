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
	var P = { current: null }, F = { transition: null }, ee = {
		ReactCurrentDispatcher: P,
		ReactCurrentBatchConfig: F,
		ReactCurrentOwner: C
	};
	function te() {
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
	}, e.Component = _, e.Fragment = r, e.Profiler = a, e.PureComponent = y, e.StrictMode = i, e.Suspense = l, e.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED = ee, e.act = te, e.cloneElement = function(e, n, r) {
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
		var t = F.transition;
		F.transition = {};
		try {
			e();
		} finally {
			F.transition = t;
		}
	}, e.unstable_act = te, e.useCallback = function(e, t) {
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
	var C = t.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED, w = Symbol.for("react.element"), T = Symbol.for("react.portal"), E = Symbol.for("react.fragment"), D = Symbol.for("react.strict_mode"), O = Symbol.for("react.profiler"), k = Symbol.for("react.provider"), A = Symbol.for("react.context"), j = Symbol.for("react.forward_ref"), M = Symbol.for("react.suspense"), N = Symbol.for("react.suspense_list"), P = Symbol.for("react.memo"), F = Symbol.for("react.lazy"), ee = Symbol.for("react.offscreen"), te = Symbol.iterator;
	function ne(e) {
		return typeof e != "object" || !e ? null : (e = te && e[te] || e["@@iterator"], typeof e == "function" ? e : null);
	}
	var re = Object.assign, ie;
	function ae(e) {
		if (ie === void 0) try {
			throw Error();
		} catch (e) {
			var t = e.stack.trim().match(/\n( *(at )?)/);
			ie = t && t[1] || "";
		}
		return "\n" + ie + e;
	}
	var oe = !1;
	function se(e, t) {
		if (!e || oe) return "";
		oe = !0;
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
			oe = !1, Error.prepareStackTrace = n;
		}
		return (e = e ? e.displayName || e.name : "") ? ae(e) : "";
	}
	function ce(e) {
		switch (e.tag) {
			case 5: return ae(e.type);
			case 16: return ae("Lazy");
			case 13: return ae("Suspense");
			case 19: return ae("SuspenseList");
			case 0:
			case 2:
			case 15: return e = se(e.type, !1), e;
			case 11: return e = se(e.type.render, !1), e;
			case 1: return e = se(e.type, !0), e;
			default: return "";
		}
	}
	function le(e) {
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
			case P: return t = e.displayName || null, t === null ? le(e.type) || "Memo" : t;
			case F:
				t = e._payload, e = e._init;
				try {
					return le(e(t));
				} catch (e) {}
		}
		return null;
	}
	function ue(e) {
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
			case 16: return le(t);
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
	function de(e) {
		switch (typeof e) {
			case "boolean":
			case "number":
			case "string":
			case "undefined": return e;
			case "object": return e;
			default: return "";
		}
	}
	function fe(e) {
		var t = e.type;
		return (e = e.nodeName) && e.toLowerCase() === "input" && (t === "checkbox" || t === "radio");
	}
	function pe(e) {
		var t = fe(e) ? "checked" : "value", n = Object.getOwnPropertyDescriptor(e.constructor.prototype, t), r = "" + e[t];
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
	function me(e) {
		e._valueTracker || (e._valueTracker = pe(e));
	}
	function he(e) {
		if (!e) return !1;
		var t = e._valueTracker;
		if (!t) return !0;
		var n = t.getValue(), r = "";
		return e && (r = fe(e) ? e.checked ? "true" : "false" : e.value), e = r, e === n ? !1 : (t.setValue(e), !0);
	}
	function ge(e) {
		if (e = e || (typeof document < "u" ? document : void 0), e === void 0) return null;
		try {
			return e.activeElement || e.body;
		} catch (t) {
			return e.body;
		}
	}
	function _e(e, t) {
		var n = t.checked;
		return re({}, t, {
			defaultChecked: void 0,
			defaultValue: void 0,
			value: void 0,
			checked: n == null ? e._wrapperState.initialChecked : n
		});
	}
	function ve(e, t) {
		var n = t.defaultValue == null ? "" : t.defaultValue, r = t.checked == null ? t.defaultChecked : t.checked;
		n = de(t.value == null ? n : t.value), e._wrapperState = {
			initialChecked: r,
			initialValue: n,
			controlled: t.type === "checkbox" || t.type === "radio" ? t.checked != null : t.value != null
		};
	}
	function ye(e, t) {
		t = t.checked, t != null && S(e, "checked", t, !1);
	}
	function be(e, t) {
		ye(e, t);
		var n = de(t.value), r = t.type;
		if (n != null) r === "number" ? (n === 0 && e.value === "" || e.value != n) && (e.value = "" + n) : e.value !== "" + n && (e.value = "" + n);
		else if (r === "submit" || r === "reset") {
			e.removeAttribute("value");
			return;
		}
		t.hasOwnProperty("value") ? Se(e, t.type, n) : t.hasOwnProperty("defaultValue") && Se(e, t.type, de(t.defaultValue)), t.checked == null && t.defaultChecked != null && (e.defaultChecked = !!t.defaultChecked);
	}
	function xe(e, t, n) {
		if (t.hasOwnProperty("value") || t.hasOwnProperty("defaultValue")) {
			var r = t.type;
			if (!(r !== "submit" && r !== "reset" || t.value !== void 0 && t.value !== null)) return;
			t = "" + e._wrapperState.initialValue, n || t === e.value || (e.value = t), e.defaultValue = t;
		}
		n = e.name, n !== "" && (e.name = ""), e.defaultChecked = !!e._wrapperState.initialChecked, n !== "" && (e.name = n);
	}
	function Se(e, t, n) {
		(t !== "number" || ge(e.ownerDocument) !== e) && (n == null ? e.defaultValue = "" + e._wrapperState.initialValue : e.defaultValue !== "" + n && (e.defaultValue = "" + n));
	}
	var Ce = Array.isArray;
	function we(e, t, n, r) {
		if (e = e.options, t) {
			t = {};
			for (var i = 0; i < n.length; i++) t["$" + n[i]] = !0;
			for (n = 0; n < e.length; n++) i = t.hasOwnProperty("$" + e[n].value), e[n].selected !== i && (e[n].selected = i), i && r && (e[n].defaultSelected = !0);
		} else {
			for (n = "" + de(n), t = null, i = 0; i < e.length; i++) {
				if (e[i].value === n) {
					e[i].selected = !0, r && (e[i].defaultSelected = !0);
					return;
				}
				t !== null || e[i].disabled || (t = e[i]);
			}
			t !== null && (t.selected = !0);
		}
	}
	function Te(e, t) {
		if (t.dangerouslySetInnerHTML != null) throw Error(r(91));
		return re({}, t, {
			value: void 0,
			defaultValue: void 0,
			children: "" + e._wrapperState.initialValue
		});
	}
	function Ee(e, t) {
		var n = t.value;
		if (n == null) {
			if (n = t.children, t = t.defaultValue, n != null) {
				if (t != null) throw Error(r(92));
				if (Ce(n)) {
					if (1 < n.length) throw Error(r(93));
					n = n[0];
				}
				t = n;
			}
			t == null && (t = ""), n = t;
		}
		e._wrapperState = { initialValue: de(n) };
	}
	function De(e, t) {
		var n = de(t.value), r = de(t.defaultValue);
		n != null && (n = "" + n, n !== e.value && (e.value = n), t.defaultValue == null && e.defaultValue !== n && (e.defaultValue = n)), r != null && (e.defaultValue = "" + r);
	}
	function Oe(e) {
		var t = e.textContent;
		t === e._wrapperState.initialValue && t !== "" && t !== null && (e.value = t);
	}
	function ke(e) {
		switch (e) {
			case "svg": return "http://www.w3.org/2000/svg";
			case "math": return "http://www.w3.org/1998/Math/MathML";
			default: return "http://www.w3.org/1999/xhtml";
		}
	}
	function Ae(e, t) {
		return e == null || e === "http://www.w3.org/1999/xhtml" ? ke(t) : e === "http://www.w3.org/2000/svg" && t === "foreignObject" ? "http://www.w3.org/1999/xhtml" : e;
	}
	var je, Me = function(e) {
		return typeof MSApp < "u" && MSApp.execUnsafeLocalFunction ? function(t, n, r, i) {
			MSApp.execUnsafeLocalFunction(function() {
				return e(t, n, r, i);
			});
		} : e;
	}(function(e, t) {
		if (e.namespaceURI !== "http://www.w3.org/2000/svg" || "innerHTML" in e) e.innerHTML = t;
		else {
			for (je = je || document.createElement("div"), je.innerHTML = "<svg>" + t.valueOf().toString() + "</svg>", t = je.firstChild; e.firstChild;) e.removeChild(e.firstChild);
			for (; t.firstChild;) e.appendChild(t.firstChild);
		}
	});
	function Ne(e, t) {
		if (t) {
			var n = e.firstChild;
			if (n && n === e.lastChild && n.nodeType === 3) {
				n.nodeValue = t;
				return;
			}
		}
		e.textContent = t;
	}
	var Pe = {
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
	}, Fe = [
		"Webkit",
		"ms",
		"Moz",
		"O"
	];
	Object.keys(Pe).forEach(function(e) {
		Fe.forEach(function(t) {
			t = t + e.charAt(0).toUpperCase() + e.substring(1), Pe[t] = Pe[e];
		});
	});
	function Ie(e, t, n) {
		return t == null || typeof t == "boolean" || t === "" ? "" : n || typeof t != "number" || t === 0 || Pe.hasOwnProperty(e) && Pe[e] ? ("" + t).trim() : t + "px";
	}
	function Le(e, t) {
		for (var n in e = e.style, t) if (t.hasOwnProperty(n)) {
			var r = n.indexOf("--") === 0, i = Ie(n, t[n], r);
			n === "float" && (n = "cssFloat"), r ? e.setProperty(n, i) : e[n] = i;
		}
	}
	var Re = re({ menuitem: !0 }, {
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
	function ze(e, t) {
		if (t) {
			if (Re[e] && (t.children != null || t.dangerouslySetInnerHTML != null)) throw Error(r(137, e));
			if (t.dangerouslySetInnerHTML != null) {
				if (t.children != null) throw Error(r(60));
				if (typeof t.dangerouslySetInnerHTML != "object" || !("__html" in t.dangerouslySetInnerHTML)) throw Error(r(61));
			}
			if (t.style != null && typeof t.style != "object") throw Error(r(62));
		}
	}
	function Be(e, t) {
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
	var Ve = null;
	function He(e) {
		return e = e.target || e.srcElement || window, e.correspondingUseElement && (e = e.correspondingUseElement), e.nodeType === 3 ? e.parentNode : e;
	}
	var Ue = null, We = null, Ge = null;
	function Ke(e) {
		if (e = Ui(e)) {
			if (typeof Ue != "function") throw Error(r(280));
			var t = e.stateNode;
			t && (t = Gi(t), Ue(e.stateNode, e.type, t));
		}
	}
	function qe(e) {
		We ? Ge ? Ge.push(e) : Ge = [e] : We = e;
	}
	function Je() {
		if (We) {
			var e = We, t = Ge;
			if (Ge = We = null, Ke(e), t) for (e = 0; e < t.length; e++) Ke(t[e]);
		}
	}
	function Ye(e, t) {
		return e(t);
	}
	function Xe() {}
	var Ze = !1;
	function Qe(e, t, n) {
		if (Ze) return e(t, n);
		Ze = !0;
		try {
			return Ye(e, t, n);
		} finally {
			Ze = !1, (We !== null || Ge !== null) && (Xe(), Je());
		}
	}
	function $e(e, t) {
		var n = e.stateNode;
		if (n === null) return null;
		var i = Gi(n);
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
	var et = !1;
	if (c) try {
		var tt = {};
		Object.defineProperty(tt, "passive", { get: function() {
			et = !0;
		} }), window.addEventListener("test", tt, tt), window.removeEventListener("test", tt, tt);
	} catch (e) {
		et = !1;
	}
	function nt(e, t, n, r, i, a, o, s, c) {
		var l = Array.prototype.slice.call(arguments, 3);
		try {
			t.apply(n, l);
		} catch (e) {
			this.onError(e);
		}
	}
	var rt = !1, it = null, at = !1, ot = null, st = { onError: function(e) {
		rt = !0, it = e;
	} };
	function ct(e, t, n, r, i, a, o, s, c) {
		rt = !1, it = null, nt.apply(st, arguments);
	}
	function lt(e, t, n, i, a, o, s, c, l) {
		if (ct.apply(this, arguments), rt) {
			if (rt) {
				var u = it;
				rt = !1, it = null;
			} else throw Error(r(198));
			at || (at = !0, ot = u);
		}
	}
	function ut(e) {
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
	function dt(e) {
		if (e.tag === 13) {
			var t = e.memoizedState;
			if (t === null && (e = e.alternate, e !== null && (t = e.memoizedState)), t !== null) return t.dehydrated;
		}
		return null;
	}
	function ft(e) {
		if (ut(e) !== e) throw Error(r(188));
	}
	function pt(e) {
		var t = e.alternate;
		if (!t) {
			if (t = ut(e), t === null) throw Error(r(188));
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
					if (o === n) return ft(a), e;
					if (o === i) return ft(a), t;
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
	function mt(e) {
		return e = pt(e), e === null ? null : ht(e);
	}
	function ht(e) {
		if (e.tag === 5 || e.tag === 6) return e;
		for (e = e.child; e !== null;) {
			var t = ht(e);
			if (t !== null) return t;
			e = e.sibling;
		}
		return null;
	}
	var gt = n.unstable_scheduleCallback, _t = n.unstable_cancelCallback, vt = n.unstable_shouldYield, yt = n.unstable_requestPaint, bt = n.unstable_now, xt = n.unstable_getCurrentPriorityLevel, St = n.unstable_ImmediatePriority, Ct = n.unstable_UserBlockingPriority, wt = n.unstable_NormalPriority, Tt = n.unstable_LowPriority, Et = n.unstable_IdlePriority, Dt = null, Ot = null;
	function kt(e) {
		if (Ot && typeof Ot.onCommitFiberRoot == "function") try {
			Ot.onCommitFiberRoot(Dt, e, void 0, (e.current.flags & 128) == 128);
		} catch (e) {}
	}
	var At = Math.clz32 ? Math.clz32 : Nt, jt = Math.log, Mt = Math.LN2;
	function Nt(e) {
		return e >>>= 0, e === 0 ? 32 : 31 - (jt(e) / Mt | 0) | 0;
	}
	var Pt = 64, Ft = 4194304;
	function It(e) {
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
	function Lt(e, t) {
		var n = e.pendingLanes;
		if (n === 0) return 0;
		var r = 0, i = e.suspendedLanes, a = e.pingedLanes, o = n & 268435455;
		if (o !== 0) {
			var s = o & ~i;
			s === 0 ? (a &= o, a !== 0 && (r = It(a))) : r = It(s);
		} else o = n & ~i, o === 0 ? a !== 0 && (r = It(a)) : r = It(o);
		if (r === 0) return 0;
		if (t !== 0 && t !== r && (t & i) === 0 && (i = r & -r, a = t & -t, i >= a || i === 16 && a & 4194240)) return t;
		if (r & 4 && (r |= n & 16), t = e.entangledLanes, t !== 0) for (e = e.entanglements, t &= r; 0 < t;) n = 31 - At(t), i = 1 << n, r |= e[n], t &= ~i;
		return r;
	}
	function Rt(e, t) {
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
	function zt(e, t) {
		for (var n = e.suspendedLanes, r = e.pingedLanes, i = e.expirationTimes, a = e.pendingLanes; 0 < a;) {
			var o = 31 - At(a), s = 1 << o, c = i[o];
			c === -1 ? ((s & n) === 0 || (s & r) !== 0) && (i[o] = Rt(s, t)) : c <= t && (e.expiredLanes |= s), a &= ~s;
		}
	}
	function Bt(e) {
		return e = e.pendingLanes & -1073741825, e === 0 ? e & 1073741824 ? 1073741824 : 0 : e;
	}
	function Vt() {
		var e = Pt;
		return Pt <<= 1, !(Pt & 4194240) && (Pt = 64), e;
	}
	function Ht(e) {
		for (var t = [], n = 0; 31 > n; n++) t.push(e);
		return t;
	}
	function Ut(e, t, n) {
		e.pendingLanes |= t, t !== 536870912 && (e.suspendedLanes = 0, e.pingedLanes = 0), e = e.eventTimes, t = 31 - At(t), e[t] = n;
	}
	function Wt(e, t) {
		var n = e.pendingLanes & ~t;
		e.pendingLanes = t, e.suspendedLanes = 0, e.pingedLanes = 0, e.expiredLanes &= t, e.mutableReadLanes &= t, e.entangledLanes &= t, t = e.entanglements;
		var r = e.eventTimes;
		for (e = e.expirationTimes; 0 < n;) {
			var i = 31 - At(n), a = 1 << i;
			t[i] = 0, r[i] = -1, e[i] = -1, n &= ~a;
		}
	}
	function Gt(e, t) {
		var n = e.entangledLanes |= t;
		for (e = e.entanglements; n;) {
			var r = 31 - At(n), i = 1 << r;
			i & t | e[r] & t && (e[r] |= t), n &= ~i;
		}
	}
	var I = 0;
	function Kt(e) {
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
		}, t !== null && (t = Ui(t), t !== null && Jt(t)), e) : (e.eventSystemFlags |= r, t = e.targetContainers, i !== null && t.indexOf(i) === -1 && t.push(i), e);
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
		var t = Hi(e.target);
		if (t !== null) {
			var n = ut(t);
			if (n !== null) {
				if (t = n.tag, t === 13) {
					if (t = dt(n), t !== null) {
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
	function L(e) {
		if (e.blockedOn !== null) return !1;
		for (var t = e.targetContainers; 0 < t.length;) {
			var n = Sn(e.domEventName, e.eventSystemFlags, t[0], e.nativeEvent);
			if (n === null) {
				n = e.nativeEvent;
				var r = new n.constructor(n.type, n);
				Ve = r, n.target.dispatchEvent(r), Ve = null;
			} else return t = Ui(n), t !== null && Jt(t), e.blockedOn = n, !1;
			t.shift();
		}
		return !0;
	}
	function fn(e, t, n) {
		L(e) && n.delete(t);
	}
	function pn() {
		Qt = !1, en !== null && L(en) && (en = null), tn !== null && L(tn) && (tn = null), nn !== null && L(nn) && (nn = null), rn.forEach(fn), an.forEach(fn);
	}
	function mn(e, t) {
		e.blockedOn === t && (e.blockedOn = null, Qt || (Qt = !0, n.unstable_scheduleCallback(n.unstable_NormalPriority, pn)));
	}
	function hn(e) {
		function t(t) {
			return mn(t, e);
		}
		if (0 < $t.length) {
			mn($t[0], e);
			for (var n = 1; n < $t.length; n++) {
				var r = $t[n];
				r.blockedOn === e && (r.blockedOn = null);
			}
		}
		for (en !== null && mn(en, e), tn !== null && mn(tn, e), nn !== null && mn(nn, e), rn.forEach(t), an.forEach(t), n = 0; n < on.length; n++) r = on[n], r.blockedOn === e && (r.blockedOn = null);
		for (; 0 < on.length && (n = on[0], n.blockedOn === null);) dn(n), n.blockedOn === null && on.shift();
	}
	var gn = C.ReactCurrentBatchConfig, _n = !0;
	function vn(e, t, n, r) {
		var i = I, a = gn.transition;
		gn.transition = null;
		try {
			I = 1, bn(e, t, n, r);
		} finally {
			I = i, gn.transition = a;
		}
	}
	function yn(e, t, n, r) {
		var i = I, a = gn.transition;
		gn.transition = null;
		try {
			I = 4, bn(e, t, n, r);
		} finally {
			I = i, gn.transition = a;
		}
	}
	function bn(e, t, n, r) {
		if (_n) {
			var i = Sn(e, t, n, r);
			if (i === null) mi(e, t, r, xn, n), cn(e, r);
			else if (un(i, e, t, n, r)) r.stopPropagation();
			else if (cn(e, r), t & 4 && -1 < sn.indexOf(e)) {
				for (; i !== null;) {
					var a = Ui(i);
					if (a !== null && qt(a), a = Sn(e, t, n, r), a === null && mi(e, t, r, xn, n), a === i) break;
					i = a;
				}
				i !== null && r.stopPropagation();
			} else mi(e, t, r, null, n);
		}
	}
	var xn = null;
	function Sn(e, t, n, r) {
		if (xn = null, e = He(r), e = Hi(e), e !== null) if (t = ut(e), t === null) e = null;
		else if (n = t.tag, n === 13) {
			if (e = dt(t), e !== null) return e;
			e = null;
		} else if (n === 3) {
			if (t.stateNode.current.memoizedState.isDehydrated) return t.tag === 3 ? t.stateNode.containerInfo : null;
			e = null;
		} else t !== e && (e = null);
		return xn = e, null;
	}
	function Cn(e) {
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
			case "message": switch (xt()) {
				case St: return 1;
				case Ct: return 4;
				case wt:
				case Tt: return 16;
				case Et: return 536870912;
				default: return 16;
			}
			default: return 16;
		}
	}
	var wn = null, Tn = null, En = null;
	function Dn() {
		if (En) return En;
		var e, t = Tn, n = t.length, r, i = "value" in wn ? wn.value : wn.textContent, a = i.length;
		for (e = 0; e < n && t[e] === i[e]; e++);
		var o = n - e;
		for (r = 1; r <= o && t[n - r] === i[a - r]; r++);
		return En = i.slice(e, 1 < r ? 1 - r : void 0);
	}
	function On(e) {
		var t = e.keyCode;
		return "charCode" in e ? (e = e.charCode, e === 0 && t === 13 && (e = 13)) : e = t, e === 10 && (e = 13), 32 <= e || e === 13 ? e : 0;
	}
	function kn() {
		return !0;
	}
	function An() {
		return !1;
	}
	function jn(e) {
		function t(t, n, r, i, a) {
			for (var o in this._reactName = t, this._targetInst = r, this.type = n, this.nativeEvent = i, this.target = a, this.currentTarget = null, e) e.hasOwnProperty(o) && (t = e[o], this[o] = t ? t(i) : i[o]);
			return this.isDefaultPrevented = (i.defaultPrevented == null ? !1 === i.returnValue : i.defaultPrevented) ? kn : An, this.isPropagationStopped = An, this;
		}
		return re(t.prototype, {
			preventDefault: function() {
				this.defaultPrevented = !0;
				var e = this.nativeEvent;
				e && (e.preventDefault ? e.preventDefault() : typeof e.returnValue != "unknown" && (e.returnValue = !1), this.isDefaultPrevented = kn);
			},
			stopPropagation: function() {
				var e = this.nativeEvent;
				e && (e.stopPropagation ? e.stopPropagation() : typeof e.cancelBubble != "unknown" && (e.cancelBubble = !0), this.isPropagationStopped = kn);
			},
			persist: function() {},
			isPersistent: kn
		}), t;
	}
	var Mn = {
		eventPhase: 0,
		bubbles: 0,
		cancelable: 0,
		timeStamp: function(e) {
			return e.timeStamp || Date.now();
		},
		defaultPrevented: 0,
		isTrusted: 0
	}, Nn = jn(Mn), Pn = re({}, Mn, {
		view: 0,
		detail: 0
	}), Fn = jn(Pn), In, Ln, Rn, zn = re({}, Pn, {
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
		getModifierState: Xn,
		button: 0,
		buttons: 0,
		relatedTarget: function(e) {
			return e.relatedTarget === void 0 ? e.fromElement === e.srcElement ? e.toElement : e.fromElement : e.relatedTarget;
		},
		movementX: function(e) {
			return "movementX" in e ? e.movementX : (e !== Rn && (Rn && e.type === "mousemove" ? (In = e.screenX - Rn.screenX, Ln = e.screenY - Rn.screenY) : Ln = In = 0, Rn = e), In);
		},
		movementY: function(e) {
			return "movementY" in e ? e.movementY : Ln;
		}
	}), Bn = jn(zn), Vn = jn(re({}, zn, { dataTransfer: 0 })), Hn = jn(re({}, Pn, { relatedTarget: 0 })), Un = jn(re({}, Mn, {
		animationName: 0,
		elapsedTime: 0,
		pseudoElement: 0
	})), Wn = jn(re({}, Mn, { clipboardData: function(e) {
		return "clipboardData" in e ? e.clipboardData : window.clipboardData;
	} })), Gn = jn(re({}, Mn, { data: 0 })), Kn = {
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
	}, qn = {
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
	}, Jn = {
		Alt: "altKey",
		Control: "ctrlKey",
		Meta: "metaKey",
		Shift: "shiftKey"
	};
	function Yn(e) {
		var t = this.nativeEvent;
		return t.getModifierState ? t.getModifierState(e) : (e = Jn[e]) ? !!t[e] : !1;
	}
	function Xn() {
		return Yn;
	}
	var Zn = jn(re({}, Pn, {
		key: function(e) {
			if (e.key) {
				var t = Kn[e.key] || e.key;
				if (t !== "Unidentified") return t;
			}
			return e.type === "keypress" ? (e = On(e), e === 13 ? "Enter" : String.fromCharCode(e)) : e.type === "keydown" || e.type === "keyup" ? qn[e.keyCode] || "Unidentified" : "";
		},
		code: 0,
		location: 0,
		ctrlKey: 0,
		shiftKey: 0,
		altKey: 0,
		metaKey: 0,
		repeat: 0,
		locale: 0,
		getModifierState: Xn,
		charCode: function(e) {
			return e.type === "keypress" ? On(e) : 0;
		},
		keyCode: function(e) {
			return e.type === "keydown" || e.type === "keyup" ? e.keyCode : 0;
		},
		which: function(e) {
			return e.type === "keypress" ? On(e) : e.type === "keydown" || e.type === "keyup" ? e.keyCode : 0;
		}
	})), Qn = jn(re({}, zn, {
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
	})), $n = jn(re({}, Pn, {
		touches: 0,
		targetTouches: 0,
		changedTouches: 0,
		altKey: 0,
		metaKey: 0,
		ctrlKey: 0,
		shiftKey: 0,
		getModifierState: Xn
	})), er = jn(re({}, Mn, {
		propertyName: 0,
		elapsedTime: 0,
		pseudoElement: 0
	})), tr = jn(re({}, zn, {
		deltaX: function(e) {
			return "deltaX" in e ? e.deltaX : "wheelDeltaX" in e ? -e.wheelDeltaX : 0;
		},
		deltaY: function(e) {
			return "deltaY" in e ? e.deltaY : "wheelDeltaY" in e ? -e.wheelDeltaY : "wheelDelta" in e ? -e.wheelDelta : 0;
		},
		deltaZ: 0,
		deltaMode: 0
	})), nr = [
		9,
		13,
		27,
		32
	], rr = c && "CompositionEvent" in window, ir = null;
	c && "documentMode" in document && (ir = document.documentMode);
	var ar = c && "TextEvent" in window && !ir, or = c && (!rr || ir && 8 < ir && 11 >= ir), sr = " ", cr = !1;
	function lr(e, t) {
		switch (e) {
			case "keyup": return nr.indexOf(t.keyCode) !== -1;
			case "keydown": return t.keyCode !== 229;
			case "keypress":
			case "mousedown":
			case "focusout": return !0;
			default: return !1;
		}
	}
	function ur(e) {
		return e = e.detail, typeof e == "object" && "data" in e ? e.data : null;
	}
	var dr = !1;
	function fr(e, t) {
		switch (e) {
			case "compositionend": return ur(t);
			case "keypress": return t.which === 32 ? (cr = !0, sr) : null;
			case "textInput": return e = t.data, e === sr && cr ? null : e;
			default: return null;
		}
	}
	function pr(e, t) {
		if (dr) return e === "compositionend" || !rr && lr(e, t) ? (e = Dn(), En = Tn = wn = null, dr = !1, e) : null;
		switch (e) {
			case "paste": return null;
			case "keypress":
				if (!(t.ctrlKey || t.altKey || t.metaKey) || t.ctrlKey && t.altKey) {
					if (t.char && 1 < t.char.length) return t.char;
					if (t.which) return String.fromCharCode(t.which);
				}
				return null;
			case "compositionend": return or && t.locale !== "ko" ? null : t.data;
			default: return null;
		}
	}
	var mr = {
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
	function hr(e) {
		var t = e && e.nodeName && e.nodeName.toLowerCase();
		return t === "input" ? !!mr[e.type] : t === "textarea";
	}
	function gr(e, t, n, r) {
		qe(r), t = gi(t, "onChange"), 0 < t.length && (n = new Nn("onChange", "change", null, n, r), e.push({
			event: n,
			listeners: t
		}));
	}
	var _r = null, vr = null;
	function yr(e) {
		li(e, 0);
	}
	function br(e) {
		if (he(Wi(e))) return e;
	}
	function xr(e, t) {
		if (e === "change") return t;
	}
	var Sr = !1;
	if (c) {
		var Cr;
		if (c) {
			var wr = "oninput" in document;
			if (!wr) {
				var Tr = document.createElement("div");
				Tr.setAttribute("oninput", "return;"), wr = typeof Tr.oninput == "function";
			}
			Cr = wr;
		} else Cr = !1;
		Sr = Cr && (!document.documentMode || 9 < document.documentMode);
	}
	function Er() {
		_r && (_r.detachEvent("onpropertychange", Dr), vr = _r = null);
	}
	function Dr(e) {
		if (e.propertyName === "value" && br(vr)) {
			var t = [];
			gr(t, vr, e, He(e)), Qe(yr, t);
		}
	}
	function Or(e, t, n) {
		e === "focusin" ? (Er(), _r = t, vr = n, _r.attachEvent("onpropertychange", Dr)) : e === "focusout" && Er();
	}
	function kr(e) {
		if (e === "selectionchange" || e === "keyup" || e === "keydown") return br(vr);
	}
	function Ar(e, t) {
		if (e === "click") return br(t);
	}
	function jr(e, t) {
		if (e === "input" || e === "change") return br(t);
	}
	function Mr(e, t) {
		return e === t && (e !== 0 || 1 / e == 1 / t) || e !== e && t !== t;
	}
	var Nr = typeof Object.is == "function" ? Object.is : Mr;
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
		for (var e = window, t = ge(); t instanceof e.HTMLIFrameElement;) {
			try {
				var n = typeof t.contentWindow.location.href == "string";
			} catch (e) {
				n = !1;
			}
			if (n) e = t.contentWindow;
			else break;
			t = ge(e.document);
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
		Gr || Hr == null || Hr !== ge(r) || (r = Hr, "selectionStart" in r && zr(r) ? r = {
			start: r.selectionStart,
			end: r.selectionEnd
		} : (r = (r.ownerDocument && r.ownerDocument.defaultView || window).getSelection(), r = {
			anchorNode: r.anchorNode,
			anchorOffset: r.anchorOffset,
			focusNode: r.focusNode,
			focusOffset: r.focusOffset
		}), Wr && Pr(Wr, r) || (Wr = r, r = gi(Ur, "onSelect"), 0 < r.length && (t = new Nn("onSelect", "select", null, t, n), e.push({
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
	function R(e) {
		if (Yr[e]) return Yr[e];
		if (!Jr[e]) return e;
		var t = Jr[e], n;
		for (n in t) if (t.hasOwnProperty(n) && n in Xr) return Yr[e] = t[n];
		return e;
	}
	var Zr = R("animationend"), Qr = R("animationiteration"), $r = R("animationstart"), ei = R("transitionend"), ti = /* @__PURE__ */ new Map(), ni = "abort auxClick cancel canPlay canPlayThrough click close contextMenu copy cut drag dragEnd dragEnter dragExit dragLeave dragOver dragStart drop durationChange emptied encrypted ended error gotPointerCapture input invalid keyDown keyPress keyUp load loadedData loadedMetadata loadStart lostPointerCapture mouseDown mouseMove mouseOut mouseOver mouseUp paste pause play playing pointerCancel pointerDown pointerMove pointerOut pointerOver pointerUp progress rateChange reset resize seeked seeking stalled submit suspend timeUpdate touchCancel touchEnd touchStart volumeChange scroll toggle touchMove waiting wheel".split(" ");
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
		e.currentTarget = n, lt(r, t, void 0, e), e.currentTarget = null;
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
		if (at) throw e = ot, at = !1, ot = null, e;
	}
	function ui(e, t) {
		var n = t[zi];
		n === void 0 && (n = t[zi] = /* @__PURE__ */ new Set());
		var r = e + "__bubble";
		n.has(r) || (z(t, e, 2, !1), n.add(r));
	}
	function di(e, t, n) {
		var r = 0;
		t && (r |= 4), z(n, e, r, t);
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
	function z(e, t, n, r) {
		switch (Cn(t)) {
			case 1:
				var i = vn;
				break;
			case 4:
				i = yn;
				break;
			default: i = bn;
		}
		n = i.bind(null, t, n, e), i = void 0, !et || t !== "touchstart" && t !== "touchmove" && t !== "wheel" || (i = !0), r ? i === void 0 ? e.addEventListener(t, n, !0) : e.addEventListener(t, n, {
			capture: !0,
			passive: i
		}) : i === void 0 ? e.addEventListener(t, n, !1) : e.addEventListener(t, n, { passive: i });
	}
	function mi(e, t, n, r, i) {
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
					if (o = Hi(s), o === null) return;
					if (c = o.tag, c === 5 || c === 6) {
						r = a = o;
						continue a;
					}
					s = s.parentNode;
				}
			}
			r = r.return;
		}
		Qe(function() {
			var r = a, i = He(n), o = [];
			a: {
				var s = ti.get(e);
				if (s !== void 0) {
					var c = Nn, l = e;
					switch (e) {
						case "keypress": if (On(n) === 0) break a;
						case "keydown":
						case "keyup":
							c = Zn;
							break;
						case "focusin":
							l = "focus", c = Hn;
							break;
						case "focusout":
							l = "blur", c = Hn;
							break;
						case "beforeblur":
						case "afterblur":
							c = Hn;
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
							c = Bn;
							break;
						case "drag":
						case "dragend":
						case "dragenter":
						case "dragexit":
						case "dragleave":
						case "dragover":
						case "dragstart":
						case "drop":
							c = Vn;
							break;
						case "touchcancel":
						case "touchend":
						case "touchmove":
						case "touchstart":
							c = $n;
							break;
						case Zr:
						case Qr:
						case $r:
							c = Un;
							break;
						case ei:
							c = er;
							break;
						case "scroll":
							c = Fn;
							break;
						case "wheel":
							c = tr;
							break;
						case "copy":
						case "cut":
						case "paste":
							c = Wn;
							break;
						case "gotpointercapture":
						case "lostpointercapture":
						case "pointercancel":
						case "pointerdown":
						case "pointermove":
						case "pointerout":
						case "pointerover":
						case "pointerup": c = Qn;
					}
					var u = (t & 4) != 0, d = !u && e === "scroll", f = u ? s === null ? null : s + "Capture" : s;
					u = [];
					for (var p = r, m; p !== null;) {
						m = p;
						var h = m.stateNode;
						if (m.tag === 5 && h !== null && (m = h, f !== null && (h = $e(p, f), h != null && u.push(hi(p, h, m)))), d) break;
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
					if (s = e === "mouseover" || e === "pointerover", c = e === "mouseout" || e === "pointerout", s && n !== Ve && (l = n.relatedTarget || n.fromElement) && (Hi(l) || l[Ri])) break a;
					if ((c || s) && (s = i.window === i ? i : (s = i.ownerDocument) ? s.defaultView || s.parentWindow : window, c ? (l = n.relatedTarget || n.toElement, c = r, l = l ? Hi(l) : null, l !== null && (d = ut(l), l !== d || l.tag !== 5 && l.tag !== 6) && (l = null)) : (c = null, l = r), c !== l)) {
						if (u = Bn, h = "onMouseLeave", f = "onMouseEnter", p = "mouse", (e === "pointerout" || e === "pointerover") && (u = Qn, h = "onPointerLeave", f = "onPointerEnter", p = "pointer"), d = c == null ? s : Wi(c), m = l == null ? s : Wi(l), s = new u(h, p + "leave", c, n, i), s.target = d, s.relatedTarget = m, h = null, Hi(i) === r && (u = new u(f, p + "enter", l, n, i), u.target = m, u.relatedTarget = d, h = u), d = h, c && l) b: {
							for (u = c, f = l, p = 0, m = u; m; m = _i(m)) p++;
							for (m = 0, h = f; h; h = _i(h)) m++;
							for (; 0 < p - m;) u = _i(u), p--;
							for (; 0 < m - p;) f = _i(f), m--;
							for (; p--;) {
								if (u === f || f !== null && u === f.alternate) break b;
								u = _i(u), f = _i(f);
							}
							u = null;
						}
						else u = null;
						c !== null && vi(o, s, c, u, !1), l !== null && d !== null && vi(o, d, l, u, !0);
					}
				}
				a: {
					if (s = r ? Wi(r) : window, c = s.nodeName && s.nodeName.toLowerCase(), c === "select" || c === "input" && s.type === "file") var g = xr;
					else if (hr(s)) if (Sr) g = jr;
					else {
						g = kr;
						var _ = Or;
					}
					else (c = s.nodeName) && c.toLowerCase() === "input" && (s.type === "checkbox" || s.type === "radio") && (g = Ar);
					if (g && (g = g(e, r))) {
						gr(o, g, n, i);
						break a;
					}
					_ && _(e, s, r), e === "focusout" && (_ = s._wrapperState) && _.controlled && s.type === "number" && Se(s, "number", s.value);
				}
				switch (_ = r ? Wi(r) : window, e) {
					case "focusin":
						(hr(_) || _.contentEditable === "true") && (Hr = _, Ur = r, Wr = null);
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
				if (rr) b: {
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
				else dr ? lr(e, n) && (y = "onCompositionEnd") : e === "keydown" && n.keyCode === 229 && (y = "onCompositionStart");
				y && (or && n.locale !== "ko" && (dr || y !== "onCompositionStart" ? y === "onCompositionEnd" && dr && (v = Dn()) : (wn = i, Tn = "value" in wn ? wn.value : wn.textContent, dr = !0)), _ = gi(r, y), 0 < _.length && (y = new Gn(y, e, null, n, i), o.push({
					event: y,
					listeners: _
				}), v ? y.data = v : (v = ur(n), v !== null && (y.data = v)))), (v = ar ? fr(e, n) : pr(e, n)) && (r = gi(r, "onBeforeInput"), 0 < r.length && (i = new Gn("onBeforeInput", "beforeinput", null, n, i), o.push({
					event: i,
					listeners: r
				}), i.data = v));
			}
			li(o, t);
		});
	}
	function hi(e, t, n) {
		return {
			instance: e,
			listener: t,
			currentTarget: n
		};
	}
	function gi(e, t) {
		for (var n = t + "Capture", r = []; e !== null;) {
			var i = e, a = i.stateNode;
			i.tag === 5 && a !== null && (i = a, a = $e(e, n), a != null && r.unshift(hi(e, a, i)), a = $e(e, t), a != null && r.push(hi(e, a, i))), e = e.return;
		}
		return r;
	}
	function _i(e) {
		if (e === null) return null;
		do
			e = e.return;
		while (e && e.tag !== 5);
		return e || null;
	}
	function vi(e, t, n, r, i) {
		for (var a = t._reactName, o = []; n !== null && n !== r;) {
			var s = n, c = s.alternate, l = s.stateNode;
			if (c !== null && c === r) break;
			s.tag === 5 && l !== null && (s = l, i ? (c = $e(n, a), c != null && o.unshift(hi(n, c, s))) : i || (c = $e(n, a), c != null && o.push(hi(n, c, s)))), n = n.return;
		}
		o.length !== 0 && e.push({
			event: t,
			listeners: o
		});
	}
	var yi = /\r\n?/g, bi = /\u0000|\uFFFD/g;
	function xi(e) {
		return (typeof e == "string" ? e : "" + e).replace(yi, "\n").replace(bi, "");
	}
	function Si(e, t, n) {
		if (t = xi(t), xi(e) !== t && n) throw Error(r(425));
	}
	function Ci() {}
	var wi = null, Ti = null;
	function Ei(e, t) {
		return e === "textarea" || e === "noscript" || typeof t.children == "string" || typeof t.children == "number" || typeof t.dangerouslySetInnerHTML == "object" && t.dangerouslySetInnerHTML !== null && t.dangerouslySetInnerHTML.__html != null;
	}
	var Di = typeof setTimeout == "function" ? setTimeout : void 0, Oi = typeof clearTimeout == "function" ? clearTimeout : void 0, ki = typeof Promise == "function" ? Promise : void 0, Ai = typeof queueMicrotask == "function" ? queueMicrotask : ki === void 0 ? Di : function(e) {
		return ki.resolve(null).then(e).catch(ji);
	};
	function ji(e) {
		setTimeout(function() {
			throw e;
		});
	}
	function Mi(e, t) {
		var n = t, r = 0;
		do {
			var i = n.nextSibling;
			if (e.removeChild(n), i && i.nodeType === 8) if (n = i.data, n === "/$") {
				if (r === 0) {
					e.removeChild(i), hn(t);
					return;
				}
				r--;
			} else n !== "$" && n !== "$?" && n !== "$!" || r++;
			n = i;
		} while (n);
		hn(t);
	}
	function Ni(e) {
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
	function Pi(e) {
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
	var Fi = Math.random().toString(36).slice(2), Ii = "__reactFiber$" + Fi, Li = "__reactProps$" + Fi, Ri = "__reactContainer$" + Fi, zi = "__reactEvents$" + Fi, Bi = "__reactListeners$" + Fi, Vi = "__reactHandles$" + Fi;
	function Hi(e) {
		var t = e[Ii];
		if (t) return t;
		for (var n = e.parentNode; n;) {
			if (t = n[Ri] || n[Ii]) {
				if (n = t.alternate, t.child !== null || n !== null && n.child !== null) for (e = Pi(e); e !== null;) {
					if (n = e[Ii]) return n;
					e = Pi(e);
				}
				return t;
			}
			e = n, n = e.parentNode;
		}
		return null;
	}
	function Ui(e) {
		return e = e[Ii] || e[Ri], !e || e.tag !== 5 && e.tag !== 6 && e.tag !== 13 && e.tag !== 3 ? null : e;
	}
	function Wi(e) {
		if (e.tag === 5 || e.tag === 6) return e.stateNode;
		throw Error(r(33));
	}
	function Gi(e) {
		return e[Li] || null;
	}
	var Ki = [], qi = -1;
	function Ji(e) {
		return { current: e };
	}
	function B(e) {
		0 > qi || (e.current = Ki[qi], Ki[qi] = null, qi--);
	}
	function V(e, t) {
		qi++, Ki[qi] = e.current, e.current = t;
	}
	var Yi = {}, Xi = Ji(Yi), Zi = Ji(!1), Qi = Yi;
	function $i(e, t) {
		var n = e.type.contextTypes;
		if (!n) return Yi;
		var r = e.stateNode;
		if (r && r.__reactInternalMemoizedUnmaskedChildContext === t) return r.__reactInternalMemoizedMaskedChildContext;
		var i = {}, a;
		for (a in n) i[a] = t[a];
		return r && (e = e.stateNode, e.__reactInternalMemoizedUnmaskedChildContext = t, e.__reactInternalMemoizedMaskedChildContext = i), i;
	}
	function ea(e) {
		return e = e.childContextTypes, e != null;
	}
	function ta() {
		B(Zi), B(Xi);
	}
	function na(e, t, n) {
		if (Xi.current !== Yi) throw Error(r(168));
		V(Xi, t), V(Zi, n);
	}
	function ra(e, t, n) {
		var i = e.stateNode;
		if (t = t.childContextTypes, typeof i.getChildContext != "function") return n;
		for (var a in i = i.getChildContext(), i) if (!(a in t)) throw Error(r(108, ue(e) || "Unknown", a));
		return re({}, n, i);
	}
	function ia(e) {
		return e = (e = e.stateNode) && e.__reactInternalMemoizedMergedChildContext || Yi, Qi = Xi.current, V(Xi, e), V(Zi, Zi.current), !0;
	}
	function aa(e, t, n) {
		var i = e.stateNode;
		if (!i) throw Error(r(169));
		n ? (e = ra(e, t, Qi), i.__reactInternalMemoizedMergedChildContext = e, B(Zi), B(Xi), V(Xi, e)) : B(Zi), V(Zi, n);
	}
	var oa = null, sa = !1, ca = !1;
	function la(e) {
		oa === null ? oa = [e] : oa.push(e);
	}
	function ua(e) {
		sa = !0, la(e);
	}
	function da() {
		if (!ca && oa !== null) {
			ca = !0;
			var e = 0, t = I;
			try {
				var n = oa;
				for (I = 1; e < n.length; e++) {
					var r = n[e];
					do
						r = r(!0);
					while (r !== null);
				}
				oa = null, sa = !1;
			} catch (t) {
				throw oa !== null && (oa = oa.slice(e + 1)), gt(St, da), t;
			} finally {
				I = t, ca = !1;
			}
		}
		return null;
	}
	var fa = [], pa = 0, ma = null, ha = 0, ga = [], _a = 0, va = null, ya = 1, ba = "";
	function xa(e, t) {
		fa[pa++] = ha, fa[pa++] = ma, ma = e, ha = t;
	}
	function Sa(e, t, n) {
		ga[_a++] = ya, ga[_a++] = ba, ga[_a++] = va, va = e;
		var r = ya;
		e = ba;
		var i = 32 - At(r) - 1;
		r &= ~(1 << i), n += 1;
		var a = 32 - At(t) + i;
		if (30 < a) {
			var o = i - i % 5;
			a = (r & (1 << o) - 1).toString(32), r >>= o, i -= o, ya = 1 << 32 - At(t) + i | n << i | r, ba = a + e;
		} else ya = 1 << a | n << i | r, ba = e;
	}
	function Ca(e) {
		e.return !== null && (xa(e, 1), Sa(e, 1, 0));
	}
	function wa(e) {
		for (; e === ma;) ma = fa[--pa], fa[pa] = null, ha = fa[--pa], fa[pa] = null;
		for (; e === va;) va = ga[--_a], ga[_a] = null, ba = ga[--_a], ga[_a] = null, ya = ga[--_a], ga[_a] = null;
	}
	var Ta = null, Ea = null, Da = !1, Oa = null;
	function ka(e, t) {
		var n = $l(5, null, null, 0);
		n.elementType = "DELETED", n.stateNode = t, n.return = e, t = e.deletions, t === null ? (e.deletions = [n], e.flags |= 16) : t.push(n);
	}
	function Aa(e, t) {
		switch (e.tag) {
			case 5:
				var n = e.type;
				return t = t.nodeType !== 1 || n.toLowerCase() !== t.nodeName.toLowerCase() ? null : t, t === null ? !1 : (e.stateNode = t, Ta = e, Ea = Ni(t.firstChild), !0);
			case 6: return t = e.pendingProps === "" || t.nodeType !== 3 ? null : t, t === null ? !1 : (e.stateNode = t, Ta = e, Ea = null, !0);
			case 13: return t = t.nodeType === 8 ? t : null, t === null ? !1 : (n = va === null ? null : {
				id: ya,
				overflow: ba
			}, e.memoizedState = {
				dehydrated: t,
				treeContext: n,
				retryLane: 1073741824
			}, n = $l(18, null, null, 0), n.stateNode = t, n.return = e, e.child = n, Ta = e, Ea = null, !0);
			default: return !1;
		}
	}
	function ja(e) {
		return (e.mode & 1) != 0 && (e.flags & 128) == 0;
	}
	function Ma(e) {
		if (Da) {
			var t = Ea;
			if (t) {
				var n = t;
				if (!Aa(e, t)) {
					if (ja(e)) throw Error(r(418));
					t = Ni(n.nextSibling);
					var i = Ta;
					t && Aa(e, t) ? ka(i, n) : (e.flags = e.flags & -4097 | 2, Da = !1, Ta = e);
				}
			} else {
				if (ja(e)) throw Error(r(418));
				e.flags = e.flags & -4097 | 2, Da = !1, Ta = e;
			}
		}
	}
	function Na(e) {
		for (e = e.return; e !== null && e.tag !== 5 && e.tag !== 3 && e.tag !== 13;) e = e.return;
		Ta = e;
	}
	function Pa(e) {
		if (e !== Ta) return !1;
		if (!Da) return Na(e), Da = !0, !1;
		var t;
		if ((t = e.tag !== 3) && !(t = e.tag !== 5) && (t = e.type, t = t !== "head" && t !== "body" && !Ei(e.type, e.memoizedProps)), t && (t = Ea)) {
			if (ja(e)) throw Fa(), Error(r(418));
			for (; t;) ka(e, t), t = Ni(t.nextSibling);
		}
		if (Na(e), e.tag === 13) {
			if (e = e.memoizedState, e = e === null ? null : e.dehydrated, !e) throw Error(r(317));
			a: {
				for (e = e.nextSibling, t = 0; e;) {
					if (e.nodeType === 8) {
						var n = e.data;
						if (n === "/$") {
							if (t === 0) {
								Ea = Ni(e.nextSibling);
								break a;
							}
							t--;
						} else n !== "$" && n !== "$!" && n !== "$?" || t++;
					}
					e = e.nextSibling;
				}
				Ea = null;
			}
		} else Ea = Ta ? Ni(e.stateNode.nextSibling) : null;
		return !0;
	}
	function Fa() {
		for (var e = Ea; e;) e = Ni(e.nextSibling);
	}
	function Ia() {
		Ea = Ta = null, Da = !1;
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
			return i === E ? d(e, t, n.props.children, r, n.key) : t !== null && (t.elementType === i || typeof i == "object" && i && i.$$typeof === F && Va(i) === t.type) ? (r = a(t, n.props), r.ref = za(e, t, n), r.return = e, r) : (r = ru(n.type, n.key, n.props, null, e.mode, r), r.ref = za(e, t, n), r.return = e, r);
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
					case w: return n = ru(t.type, t.key, t.props, null, e.mode, n), n.ref = za(e, null, t), n.return = e, n;
					case T: return t = su(t, e.mode, n), t.return = e, t;
					case F:
						var r = t._init;
						return f(e, r(t._payload), n);
				}
				if (Ce(t) || ne(t)) return t = iu(t, e.mode, n, null), t.return = e, t;
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
					case F: return i = n._init, p(e, t, i(n._payload), r);
				}
				if (Ce(n) || ne(n)) return i === null ? d(e, t, n, r, null) : null;
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
					case F:
						var a = r._init;
						return m(e, t, n, a(r._payload), i);
				}
				if (Ce(r) || ne(r)) return e = e.get(n) || null, d(t, e, r, i, null);
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
			if (h === s.length) return n(r, d), Da && xa(r, h), l;
			if (d === null) {
				for (; h < s.length; h++) d = f(r, s[h], c), d !== null && (a = o(d, a, h), u === null ? l = d : u.sibling = d, u = d);
				return Da && xa(r, h), l;
			}
			for (d = i(r, d); h < s.length; h++) g = m(d, r, h, s[h], c), g !== null && (e && g.alternate !== null && d.delete(g.key === null ? h : g.key), a = o(g, a, h), u === null ? l = g : u.sibling = g, u = g);
			return e && d.forEach(function(e) {
				return t(r, e);
			}), Da && xa(r, h), l;
		}
		function g(a, s, c, l) {
			var u = ne(c);
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
			if (v.done) return n(a, h), Da && xa(a, g), u;
			if (h === null) {
				for (; !v.done; g++, v = c.next()) v = f(a, v.value, l), v !== null && (s = o(v, s, g), d === null ? u = v : d.sibling = v, d = v);
				return Da && xa(a, g), u;
			}
			for (h = i(a, h); !v.done; g++, v = c.next()) v = m(h, a, g, v.value, l), v !== null && (e && v.alternate !== null && h.delete(v.key === null ? g : v.key), s = o(v, s, g), d === null ? u = v : d.sibling = v, d = v);
			return e && h.forEach(function(e) {
				return t(a, e);
			}), Da && xa(a, g), u;
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
									} else if (l.elementType === c || typeof c == "object" && c && c.$$typeof === F && Va(c) === l.type) {
										n(e, l.sibling), r = a(l, i.props), r.ref = za(e, l, i), r.return = e, e = r;
										break a;
									}
									n(e, l);
									break;
								} else t(e, l);
								l = l.sibling;
							}
							i.type === E ? (r = iu(i.props.children, e.mode, o, i.key), r.return = e, e = r) : (o = ru(i.type, i.key, i.props, null, e.mode, o), o.ref = za(e, r, i), o.return = e, e = o);
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
					case F: return l = i._init, _(e, r, l(i._payload), o);
				}
				if (Ce(i)) return h(e, r, i, o);
				if (ne(i)) return g(e, r, i, o);
				Ba(e, i);
			}
			return typeof i == "string" && i !== "" || typeof i == "number" ? (i = "" + i, r !== null && r.tag === 6 ? (n(e, r.sibling), r = a(r, i), r.return = e, e = r) : (n(e, r), r = ou(i, e.mode, o), r.return = e, e = r), s(e)) : n(e, r);
		}
		return _;
	}
	var Ua = Ha(!0), Wa = Ha(!1), Ga = Ji(null), Ka = null, qa = null, Ja = null;
	function Ya() {
		Ja = qa = Ka = null;
	}
	function Xa(e) {
		var t = Ga.current;
		B(Ga), e._currentValue = t;
	}
	function Za(e, t, n) {
		for (; e !== null;) {
			var r = e.alternate;
			if ((e.childLanes & t) === t ? r !== null && (r.childLanes & t) !== t && (r.childLanes |= t) : (e.childLanes |= t, r !== null && (r.childLanes |= t)), e === n) break;
			e = e.return;
		}
	}
	function Qa(e, t) {
		Ka = e, Ja = qa = null, e = e.dependencies, e !== null && e.firstContext !== null && ((e.lanes & t) !== 0 && (Bs = !0), e.firstContext = null);
	}
	function $a(e) {
		var t = e._currentValue;
		if (Ja !== e) if (e = {
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
	var eo = null;
	function to(e) {
		eo === null ? eo = [e] : eo.push(e);
	}
	function no(e, t, n, r) {
		var i = t.interleaved;
		return i === null ? (n.next = n, to(t)) : (n.next = i.next, i.next = n), t.interleaved = n, ro(e, r);
	}
	function ro(e, t) {
		e.lanes |= t;
		var n = e.alternate;
		for (n !== null && (n.lanes |= t), n = e, e = e.return; e !== null;) e.childLanes |= t, n = e.alternate, n !== null && (n.childLanes |= t), n = e, e = e.return;
		return n.tag === 3 ? n.stateNode : null;
	}
	var io = !1;
	function ao(e) {
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
	function oo(e, t) {
		e = e.updateQueue, t.updateQueue === e && (t.updateQueue = {
			baseState: e.baseState,
			firstBaseUpdate: e.firstBaseUpdate,
			lastBaseUpdate: e.lastBaseUpdate,
			shared: e.shared,
			effects: e.effects
		});
	}
	function so(e, t) {
		return {
			eventTime: e,
			lane: t,
			tag: 0,
			payload: null,
			callback: null,
			next: null
		};
	}
	function co(e, t, n) {
		var r = e.updateQueue;
		if (r === null) return null;
		if (r = r.shared, G & 2) {
			var i = r.pending;
			return i === null ? t.next = t : (t.next = i.next, i.next = t), r.pending = t, ro(e, n);
		}
		return i = r.interleaved, i === null ? (t.next = t, to(r)) : (t.next = i.next, i.next = t), r.interleaved = t, ro(e, n);
	}
	function lo(e, t, n) {
		if (t = t.updateQueue, t !== null && (t = t.shared, n & 4194240)) {
			var r = t.lanes;
			r &= e.pendingLanes, n |= r, t.lanes = n, Gt(e, n);
		}
	}
	function uo(e, t) {
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
	function fo(e, t, n, r) {
		var i = e.updateQueue;
		io = !1;
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
								d = re({}, d, f);
								break a;
							case 2: io = !0;
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
	function po(e, t, n) {
		if (e = t.effects, t.effects = null, e !== null) for (t = 0; t < e.length; t++) {
			var i = e[t], a = i.callback;
			if (a !== null) {
				if (i.callback = null, i = n, typeof a != "function") throw Error(r(191, a));
				a.call(i);
			}
		}
	}
	var H = {}, mo = Ji(H), ho = Ji(H), go = Ji(H);
	function _o(e) {
		if (e === H) throw Error(r(174));
		return e;
	}
	function vo(e, t) {
		switch (V(go, t), V(ho, e), V(mo, H), e = t.nodeType, e) {
			case 9:
			case 11:
				t = (t = t.documentElement) ? t.namespaceURI : Ae(null, "");
				break;
			default: e = e === 8 ? t.parentNode : t, t = e.namespaceURI || null, e = e.tagName, t = Ae(t, e);
		}
		B(mo), V(mo, t);
	}
	function yo() {
		B(mo), B(ho), B(go);
	}
	function bo(e) {
		_o(go.current);
		var t = _o(mo.current), n = Ae(t, e.type);
		t !== n && (V(ho, e), V(mo, n));
	}
	function xo(e) {
		ho.current === e && (B(mo), B(ho));
	}
	var So = Ji(0);
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
		if (Oo = o, ko = t, t.memoizedState = null, t.updateQueue = null, t.lanes = 0, Eo.current = e === null || e.memoizedState === null ? xs : Ss, e = n(i, a), No) {
			o = 0;
			do {
				if (No = !1, Po = 0, 25 <= o) throw Error(r(301));
				o += 1, jo = Ao = null, t.updateQueue = null, Eo.current = Cs, e = n(i, a);
			} while (No);
		}
		if (Eo.current = bs, t = Ao !== null && Ao.next !== null, Oo = 0, jo = Ao = ko = null, Mo = !1, t) throw Error(r(300));
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
					l === null ? (c = l = f, s = i) : l = l.next = f, ko.lanes |= d, nl |= d;
				}
				u = u.next;
			} while (u !== null && u !== o);
			l === null ? s = i : l.next = c, Nr(i, t.memoizedState) || (Bs = !0), t.memoizedState = i, t.baseState = s, t.baseQueue = l, n.lastRenderedState = i;
		}
		if (e = n.interleaved, e !== null) {
			a = e;
			do
				o = a.lane, ko.lanes |= o, nl |= o, a = a.next;
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
			Nr(o, t.memoizedState) || (Bs = !0), t.memoizedState = o, t.baseQueue === null && (t.baseState = o), n.lastRenderedState = o;
		}
		return [o, i];
	}
	function Go() {}
	function Ko(e, t) {
		var n = ko, i = Vo(), a = t(), o = !Nr(i.memoizedState, a);
		if (o && (i.memoizedState = a, Bs = !0), i = i.queue, is(Yo.bind(null, n, i, e), [e]), i.getSnapshot !== t || o || jo !== null && jo.memoizedState.tag & 1) {
			if (n.flags |= 2048, $o(9, Jo.bind(null, n, i, a, t), void 0, null), Yc === null) throw Error(r(349));
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
		var t = ro(e, 1);
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
		return Oo & 21 ? (Nr(n, t) || (n = Vt(), ko.lanes |= n, nl |= n, e.baseState = !0), t) : (e.baseState && (e.baseState = !1, Bs = !0), e.memoizedState = n);
	}
	function ps(e, t) {
		var n = I;
		I = n !== 0 && 4 > n ? n : 4, e(!0);
		var r = Do.transition;
		Do.transition = {};
		try {
			e(!1), t();
		} finally {
			I = n, Do.transition = r;
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
		else if (n = no(e, t, n, r), n !== null) {
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
				if (i.hasEagerState = !0, i.eagerState = s, Nr(s, o)) {
					var c = t.interleaved;
					c === null ? (i.next = i, to(t)) : (i.next = c.next, c.next = i), t.interleaved = i;
					return;
				}
			} catch (e) {}
			n = no(e, t, i, r), n !== null && (i = yl(), xl(n, e, r, i), ys(n, t, r));
		}
	}
	function _s(e) {
		var t = e.alternate;
		return e === ko || t !== null && t === ko;
	}
	function vs(e, t) {
		No = Mo = !0;
		var n = e.pending;
		n === null ? t.next = t : (t.next = n.next, n.next = t), e.pending = t;
	}
	function ys(e, t, n) {
		if (n & 4194240) {
			var r = t.lanes;
			r &= e.pendingLanes, n |= r, t.lanes = n, Gt(e, n);
		}
	}
	var bs = {
		readContext: $a,
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
		readContext: $a,
		useCallback: function(e, t) {
			return Bo().memoizedState = [e, t === void 0 ? null : t], e;
		},
		useContext: $a,
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
			if (Da) {
				if (n === void 0) throw Error(r(407));
				n = n();
			} else {
				if (n = t(), Yc === null) throw Error(r(349));
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
			var e = Bo(), t = Yc.identifierPrefix;
			if (Da) {
				var n = ba, r = ya;
				n = (r & ~(1 << 32 - At(r) - 1)).toString(32) + n, t = ":" + t + "R" + n, n = Po++, 0 < n && (t += "H" + n.toString(32)), t += ":";
			} else n = Fo++, t = ":" + t + "r" + n.toString(32) + ":";
			return e.memoizedState = t;
		},
		unstable_isNewReconciler: !1
	}, Ss = {
		readContext: $a,
		useCallback: us,
		useContext: $a,
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
		readContext: $a,
		useCallback: us,
		useContext: $a,
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
			for (var n in t = re({}, t), e = e.defaultProps, e) t[n] === void 0 && (t[n] = e[n]);
			return t;
		}
		return t;
	}
	function Ts(e, t, n, r) {
		t = e.memoizedState, n = n(r, t), n = n == null ? t : re({}, t, n), e.memoizedState = n, e.lanes === 0 && (e.updateQueue.baseState = n);
	}
	var Es = {
		isMounted: function(e) {
			return (e = e._reactInternals) ? ut(e) === e : !1;
		},
		enqueueSetState: function(e, t, n) {
			e = e._reactInternals;
			var r = yl(), i = bl(e), a = so(r, i);
			a.payload = t, n != null && (a.callback = n), t = co(e, a, i), t !== null && (xl(t, e, i, r), lo(t, e, i));
		},
		enqueueReplaceState: function(e, t, n) {
			e = e._reactInternals;
			var r = yl(), i = bl(e), a = so(r, i);
			a.tag = 1, a.payload = t, n != null && (a.callback = n), t = co(e, a, i), t !== null && (xl(t, e, i, r), lo(t, e, i));
		},
		enqueueForceUpdate: function(e, t) {
			e = e._reactInternals;
			var n = yl(), r = bl(e), i = so(n, r);
			i.tag = 2, t != null && (i.callback = t), t = co(e, i, r), t !== null && (xl(t, e, r, n), lo(t, e, r));
		}
	};
	function Ds(e, t, n, r, i, a, o) {
		return e = e.stateNode, typeof e.shouldComponentUpdate == "function" ? e.shouldComponentUpdate(r, a, o) : t.prototype && t.prototype.isPureReactComponent ? !Pr(n, r) || !Pr(i, a) : !0;
	}
	function Os(e, t, n) {
		var r = !1, i = Yi, a = t.contextType;
		return typeof a == "object" && a ? a = $a(a) : (i = ea(t) ? Qi : Xi.current, r = t.contextTypes, a = (r = r != null) ? $i(e, i) : Yi), t = new t(n, a), e.memoizedState = t.state !== null && t.state !== void 0 ? t.state : null, t.updater = Es, e.stateNode = t, t._reactInternals = e, r && (e = e.stateNode, e.__reactInternalMemoizedUnmaskedChildContext = i, e.__reactInternalMemoizedMaskedChildContext = a), t;
	}
	function ks(e, t, n, r) {
		e = t.state, typeof t.componentWillReceiveProps == "function" && t.componentWillReceiveProps(n, r), typeof t.UNSAFE_componentWillReceiveProps == "function" && t.UNSAFE_componentWillReceiveProps(n, r), t.state !== e && Es.enqueueReplaceState(t, t.state, null);
	}
	function As(e, t, n, r) {
		var i = e.stateNode;
		i.props = n, i.state = e.memoizedState, i.refs = {}, ao(e);
		var a = t.contextType;
		typeof a == "object" && a ? i.context = $a(a) : (a = ea(t) ? Qi : Xi.current, i.context = $i(e, a)), i.state = e.memoizedState, a = t.getDerivedStateFromProps, typeof a == "function" && (Ts(e, t, a, n), i.state = e.memoizedState), typeof t.getDerivedStateFromProps == "function" || typeof i.getSnapshotBeforeUpdate == "function" || typeof i.UNSAFE_componentWillMount != "function" && typeof i.componentWillMount != "function" || (t = i.state, typeof i.componentWillMount == "function" && i.componentWillMount(), typeof i.UNSAFE_componentWillMount == "function" && i.UNSAFE_componentWillMount(), t !== i.state && Es.enqueueReplaceState(i, i.state, null), fo(e, n, i, r), i.state = e.memoizedState), typeof i.componentDidMount == "function" && (e.flags |= 4194308);
	}
	function js(e, t) {
		try {
			var n = "", r = t;
			do
				n += ce(r), r = r.return;
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
	function Ms(e, t, n) {
		return {
			value: e,
			source: null,
			stack: n == null ? null : n,
			digest: t == null ? null : t
		};
	}
	function Ns(e, t) {
		try {
			console.error(t.value);
		} catch (e) {
			setTimeout(function() {
				throw e;
			});
		}
	}
	var Ps = typeof WeakMap == "function" ? WeakMap : Map;
	function Fs(e, t, n) {
		n = so(-1, n), n.tag = 3, n.payload = { element: null };
		var r = t.value;
		return n.callback = function() {
			ul || (ul = !0, dl = r), Ns(e, t);
		}, n;
	}
	function U(e, t, n) {
		n = so(-1, n), n.tag = 3;
		var r = e.type.getDerivedStateFromError;
		if (typeof r == "function") {
			var i = t.value;
			n.payload = function() {
				return r(i);
			}, n.callback = function() {
				Ns(e, t);
			};
		}
		var a = e.stateNode;
		return a !== null && typeof a.componentDidCatch == "function" && (n.callback = function() {
			Ns(e, t), typeof r != "function" && (fl === null ? fl = /* @__PURE__ */ new Set([this]) : fl.add(this));
			var n = t.stack;
			this.componentDidCatch(t.value, { componentStack: n === null ? "" : n });
		}), n;
	}
	function Is(e, t, n) {
		var r = e.pingCache;
		if (r === null) {
			r = e.pingCache = new Ps();
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
		return e.mode & 1 ? (e.flags |= 65536, e.lanes = i, e) : (e === t ? e.flags |= 65536 : (e.flags |= 128, n.flags |= 131072, n.flags &= -52805, n.tag === 1 && (n.alternate === null ? n.tag = 17 : (t = so(-1, 1), t.tag = 2, co(n, t, 1))), n.lanes |= 1), e);
	}
	var zs = C.ReactCurrentOwner, Bs = !1;
	function Vs(e, t, n, r) {
		t.child = e === null ? Wa(t, null, n, r) : Ua(t, e.child, n, r);
	}
	function Hs(e, t, n, r, i) {
		n = n.render;
		var a = t.ref;
		return Qa(t, i), r = Ro(e, t, n, r, a, i), n = zo(), e !== null && !Bs ? (t.updateQueue = e.updateQueue, t.flags &= -2053, e.lanes &= ~i, cc(e, t, i)) : (Da && n && Ca(t), t.flags |= 1, Vs(e, t, r, i), t.child);
	}
	function Us(e, t, n, r, i) {
		if (e === null) {
			var a = n.type;
			return typeof a == "function" && !eu(a) && a.defaultProps === void 0 && n.compare === null && n.defaultProps === void 0 ? (t.tag = 15, t.type = a, Ws(e, t, a, r, i)) : (e = ru(n.type, null, r, t, t.mode, i), e.ref = t.ref, e.return = t, t.child = e);
		}
		if (a = e.child, (e.lanes & i) === 0) {
			var o = a.memoizedProps;
			if (n = n.compare, n = n === null ? Pr : n, n(o, r) && e.ref === t.ref) return cc(e, t, i);
		}
		return t.flags |= 1, e = nu(a, r), e.ref = t.ref, e.return = t, t.child = e;
	}
	function Ws(e, t, n, r, i) {
		if (e !== null) {
			var a = e.memoizedProps;
			if (Pr(a, r) && e.ref === t.ref) if (Bs = !1, t.pendingProps = r = a, (e.lanes & i) !== 0) e.flags & 131072 && (Bs = !0);
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
		}, V($c, Qc), Qc |= n;
		else {
			if (!(n & 1073741824)) return e = a === null ? n : a.baseLanes | n, t.lanes = t.childLanes = 1073741824, t.memoizedState = {
				baseLanes: e,
				cachePool: null,
				transitions: null
			}, t.updateQueue = null, V($c, Qc), Qc |= e, null;
			t.memoizedState = {
				baseLanes: 0,
				cachePool: null,
				transitions: null
			}, r = a === null ? n : a.baseLanes, V($c, Qc), Qc |= r;
		}
		else a === null ? r = n : (r = a.baseLanes | n, t.memoizedState = null), V($c, Qc), Qc |= r;
		return Vs(e, t, i, n), t.child;
	}
	function Ks(e, t) {
		var n = t.ref;
		(e === null && n !== null || e !== null && e.ref !== n) && (t.flags |= 512, t.flags |= 2097152);
	}
	function qs(e, t, n, r, i) {
		var a = ea(n) ? Qi : Xi.current;
		return a = $i(t, a), Qa(t, i), n = Ro(e, t, n, r, a, i), r = zo(), e !== null && !Bs ? (t.updateQueue = e.updateQueue, t.flags &= -2053, e.lanes &= ~i, cc(e, t, i)) : (Da && r && Ca(t), t.flags |= 1, Vs(e, t, n, i), t.child);
	}
	function Js(e, t, n, r, i) {
		if (ea(n)) {
			var a = !0;
			ia(t);
		} else a = !1;
		if (Qa(t, i), t.stateNode === null) sc(e, t), Os(t, n, r), As(t, n, r, i), r = !0;
		else if (e === null) {
			var o = t.stateNode, s = t.memoizedProps;
			o.props = s;
			var c = o.context, l = n.contextType;
			typeof l == "object" && l ? l = $a(l) : (l = ea(n) ? Qi : Xi.current, l = $i(t, l));
			var u = n.getDerivedStateFromProps, d = typeof u == "function" || typeof o.getSnapshotBeforeUpdate == "function";
			d || typeof o.UNSAFE_componentWillReceiveProps != "function" && typeof o.componentWillReceiveProps != "function" || (s !== r || c !== l) && ks(t, o, r, l), io = !1;
			var f = t.memoizedState;
			o.state = f, fo(t, r, o, i), c = t.memoizedState, s !== r || f !== c || Zi.current || io ? (typeof u == "function" && (Ts(t, n, u, r), c = t.memoizedState), (s = io || Ds(t, n, s, r, f, c, l)) ? (d || typeof o.UNSAFE_componentWillMount != "function" && typeof o.componentWillMount != "function" || (typeof o.componentWillMount == "function" && o.componentWillMount(), typeof o.UNSAFE_componentWillMount == "function" && o.UNSAFE_componentWillMount()), typeof o.componentDidMount == "function" && (t.flags |= 4194308)) : (typeof o.componentDidMount == "function" && (t.flags |= 4194308), t.memoizedProps = r, t.memoizedState = c), o.props = r, o.state = c, o.context = l, r = s) : (typeof o.componentDidMount == "function" && (t.flags |= 4194308), r = !1);
		} else {
			o = t.stateNode, oo(e, t), s = t.memoizedProps, l = t.type === t.elementType ? s : ws(t.type, s), o.props = l, d = t.pendingProps, f = o.context, c = n.contextType, typeof c == "object" && c ? c = $a(c) : (c = ea(n) ? Qi : Xi.current, c = $i(t, c));
			var p = n.getDerivedStateFromProps;
			(u = typeof p == "function" || typeof o.getSnapshotBeforeUpdate == "function") || typeof o.UNSAFE_componentWillReceiveProps != "function" && typeof o.componentWillReceiveProps != "function" || (s !== d || f !== c) && ks(t, o, r, c), io = !1, f = t.memoizedState, o.state = f, fo(t, r, o, i);
			var m = t.memoizedState;
			s !== d || f !== m || Zi.current || io ? (typeof p == "function" && (Ts(t, n, p, r), m = t.memoizedState), (l = io || Ds(t, n, l, r, f, m, c) || !1) ? (u || typeof o.UNSAFE_componentWillUpdate != "function" && typeof o.componentWillUpdate != "function" || (typeof o.componentWillUpdate == "function" && o.componentWillUpdate(r, m, c), typeof o.UNSAFE_componentWillUpdate == "function" && o.UNSAFE_componentWillUpdate(r, m, c)), typeof o.componentDidUpdate == "function" && (t.flags |= 4), typeof o.getSnapshotBeforeUpdate == "function" && (t.flags |= 1024)) : (typeof o.componentDidUpdate != "function" || s === e.memoizedProps && f === e.memoizedState || (t.flags |= 4), typeof o.getSnapshotBeforeUpdate != "function" || s === e.memoizedProps && f === e.memoizedState || (t.flags |= 1024), t.memoizedProps = r, t.memoizedState = m), o.props = r, o.state = m, o.context = c, r = l) : (typeof o.componentDidUpdate != "function" || s === e.memoizedProps && f === e.memoizedState || (t.flags |= 4), typeof o.getSnapshotBeforeUpdate != "function" || s === e.memoizedProps && f === e.memoizedState || (t.flags |= 1024), r = !1);
		}
		return Ys(e, t, n, r, a, i);
	}
	function Ys(e, t, n, r, i, a) {
		Ks(e, t);
		var o = (t.flags & 128) != 0;
		if (!r && !o) return i && aa(t, n, !1), cc(e, t, a);
		r = t.stateNode, zs.current = t;
		var s = o && typeof n.getDerivedStateFromError != "function" ? null : r.render();
		return t.flags |= 1, e !== null && o ? (t.child = Ua(t, e.child, null, a), t.child = Ua(t, null, s, a)) : Vs(e, t, s, a), t.memoizedState = r.state, i && aa(t, n, !0), t.child;
	}
	function Xs(e) {
		var t = e.stateNode;
		t.pendingContext ? na(e, t.pendingContext, t.pendingContext !== t.context) : t.context && na(e, t.context, !1), vo(e, t.containerInfo);
	}
	function Zs(e, t, n, r, i) {
		return Ia(), La(i), t.flags |= 256, Vs(e, t, n, r), t.child;
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
		var r = t.pendingProps, i = So.current, a = !1, o = (t.flags & 128) != 0, s;
		if ((s = o) || (s = e !== null && e.memoizedState === null ? !1 : (i & 2) != 0), s ? (a = !0, t.flags &= -129) : (e === null || e.memoizedState !== null) && (i |= 1), V(So, i & 1), e === null) return Ma(t), e = t.memoizedState, e !== null && (e = e.dehydrated, e !== null) ? (t.mode & 1 ? e.data === "$!" ? t.lanes = 8 : t.lanes = 1073741824 : t.lanes = 1, null) : (o = r.children, e = r.fallback, a ? (r = t.mode, a = t.child, o = {
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
		return r !== null && La(r), Ua(t, e.child, null, n), e = tc(t, t.pendingProps.children), e.flags |= 2, t.memoizedState = null, e;
	}
	function rc(e, t, n, i, a, o, s) {
		if (n) return t.flags & 256 ? (t.flags &= -257, i = Ms(Error(r(422))), nc(e, t, s, i)) : t.memoizedState === null ? (o = i.fallback, a = t.mode, i = au({
			mode: "visible",
			children: i.children
		}, a, 0, null), o = iu(o, a, s, null), o.flags |= 2, i.return = t, o.return = t, i.sibling = o, t.child = i, t.mode & 1 && Ua(t, e.child, null, s), t.child.memoizedState = $s(s), t.memoizedState = Qs, o) : (t.child = e.child, t.flags |= 128, null);
		if (!(t.mode & 1)) return nc(e, t, s, null);
		if (a.data === "$!") {
			if (i = a.nextSibling && a.nextSibling.dataset, i) var c = i.dgst;
			return i = c, o = Error(r(419)), i = Ms(o, i, void 0), nc(e, t, s, i);
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
				a = (a & (i.suspendedLanes | s)) === 0 ? a : 0, a !== 0 && a !== o.retryLane && (o.retryLane = a, ro(e, a), xl(i, e, a, -1));
			}
			return Fl(), i = Ms(Error(r(421))), nc(e, t, s, i);
		}
		return a.data === "$?" ? (t.flags |= 128, t.child = e.child, t = Jl.bind(null, e), a._reactRetry = t, null) : (e = o.treeContext, Ea = Ni(a.nextSibling), Ta = t, Da = !0, Oa = null, e !== null && (ga[_a++] = ya, ga[_a++] = ba, ga[_a++] = va, ya = e.id, ba = e.overflow, va = t), t = tc(t, i.children), t.flags |= 4096, t);
	}
	function ic(e, t, n) {
		e.lanes |= t;
		var r = e.alternate;
		r !== null && (r.lanes |= t), Za(e.return, t, n);
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
		if (Vs(e, t, r.children, n), r = So.current, r & 2) r = r & 1 | 2, t.flags |= 128;
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
		if (V(So, r), !(t.mode & 1)) t.memoizedState = null;
		else switch (i) {
			case "forwards":
				for (n = t.child, i = null; n !== null;) e = n.alternate, e !== null && Co(e) === null && (i = n), n = n.sibling;
				n = i, n === null ? (i = t.child, t.child = null) : (i = n.sibling, n.sibling = null), ac(t, !1, i, n, a);
				break;
			case "backwards":
				for (n = null, i = t.child, t.child = null; i !== null;) {
					if (e = i.alternate, e !== null && Co(e) === null) {
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
				Xs(t), Ia();
				break;
			case 5:
				bo(t);
				break;
			case 1:
				ea(t.type) && ia(t);
				break;
			case 4:
				vo(t, t.stateNode.containerInfo);
				break;
			case 10:
				var r = t.type._context, i = t.memoizedProps.value;
				V(Ga, r._currentValue), r._currentValue = i;
				break;
			case 13:
				if (r = t.memoizedState, r !== null) return r.dehydrated === null ? (n & t.child.childLanes) === 0 ? (V(So, So.current & 1), e = cc(e, t, n), e === null ? null : e.sibling) : ec(e, t, n) : (V(So, So.current & 1), t.flags |= 128, null);
				V(So, So.current & 1);
				break;
			case 19:
				if (r = (n & t.childLanes) !== 0, e.flags & 128) {
					if (r) return oc(e, t, n);
					t.flags |= 128;
				}
				if (i = t.memoizedState, i !== null && (i.rendering = null, i.tail = null, i.lastEffect = null), V(So, So.current), r) break;
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
			e = t.stateNode, _o(mo.current);
			var o = null;
			switch (n) {
				case "input":
					i = _e(e, i), r = _e(e, r), o = [];
					break;
				case "select":
					i = re({}, i, { value: void 0 }), r = re({}, r, { value: void 0 }), o = [];
					break;
				case "textarea":
					i = Te(e, i), r = Te(e, r), o = [];
					break;
				default: typeof i.onClick != "function" && typeof r.onClick == "function" && (e.onclick = Ci);
			}
			ze(n, r);
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
		if (!Da) switch (e.tailMode) {
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
		switch (wa(t), t.tag) {
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
			case 1: return ea(t.type) && ta(), mc(t), null;
			case 3: return i = t.stateNode, yo(), B(Zi), B(Xi), To(), i.pendingContext && (i.context = i.pendingContext, i.pendingContext = null), (e === null || e.child === null) && (Pa(t) ? t.flags |= 4 : e === null || e.memoizedState.isDehydrated && !(t.flags & 256) || (t.flags |= 1024, Oa !== null && (Tl(Oa), Oa = null))), mc(t), null;
			case 5:
				xo(t);
				var o = _o(go.current);
				if (n = t.type, e !== null && t.stateNode != null) dc(e, t, n, i, o), e.ref !== t.ref && (t.flags |= 512, t.flags |= 2097152);
				else {
					if (!i) {
						if (t.stateNode === null) throw Error(r(166));
						return mc(t), null;
					}
					if (e = _o(mo.current), Pa(t)) {
						i = t.stateNode, n = t.type;
						var s = t.memoizedProps;
						switch (i[Ii] = t, i[Li] = s, e = (t.mode & 1) != 0, n) {
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
								ve(i, s), ui("invalid", i);
								break;
							case "select":
								i._wrapperState = { wasMultiple: !!s.multiple }, ui("invalid", i);
								break;
							case "textarea": Ee(i, s), ui("invalid", i);
						}
						for (var c in ze(n, s), o = null, s) if (s.hasOwnProperty(c)) {
							var l = s[c];
							c === "children" ? typeof l == "string" ? i.textContent !== l && (!0 !== s.suppressHydrationWarning && Si(i.textContent, l, e), o = ["children", l]) : typeof l == "number" && i.textContent !== "" + l && (!0 !== s.suppressHydrationWarning && Si(i.textContent, l, e), o = ["children", "" + l]) : a.hasOwnProperty(c) && l != null && c === "onScroll" && ui("scroll", i);
						}
						switch (n) {
							case "input":
								me(i), xe(i, s, !0);
								break;
							case "textarea":
								me(i), Oe(i);
								break;
							case "select":
							case "option": break;
							default: typeof s.onClick == "function" && (i.onclick = Ci);
						}
						i = o, t.updateQueue = i, i !== null && (t.flags |= 4);
					} else {
						c = o.nodeType === 9 ? o : o.ownerDocument, e === "http://www.w3.org/1999/xhtml" && (e = ke(n)), e === "http://www.w3.org/1999/xhtml" ? n === "script" ? (e = c.createElement("div"), e.innerHTML = "<script><\/script>", e = e.removeChild(e.firstChild)) : typeof i.is == "string" ? e = c.createElement(n, { is: i.is }) : (e = c.createElement(n), n === "select" && (c = e, i.multiple ? c.multiple = !0 : i.size && (c.size = i.size))) : e = c.createElementNS(e, n), e[Ii] = t, e[Li] = i, uc(e, t, !1, !1), t.stateNode = e;
						a: {
							switch (c = Be(n, i), n) {
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
									ve(e, i), o = _e(e, i), ui("invalid", e);
									break;
								case "option":
									o = i;
									break;
								case "select":
									e._wrapperState = { wasMultiple: !!i.multiple }, o = re({}, i, { value: void 0 }), ui("invalid", e);
									break;
								case "textarea":
									Ee(e, i), o = Te(e, i), ui("invalid", e);
									break;
								default: o = i;
							}
							for (s in ze(n, o), l = o, l) if (l.hasOwnProperty(s)) {
								var u = l[s];
								s === "style" ? Le(e, u) : s === "dangerouslySetInnerHTML" ? (u = u ? u.__html : void 0, u != null && Me(e, u)) : s === "children" ? typeof u == "string" ? (n !== "textarea" || u !== "") && Ne(e, u) : typeof u == "number" && Ne(e, "" + u) : s !== "suppressContentEditableWarning" && s !== "suppressHydrationWarning" && s !== "autoFocus" && (a.hasOwnProperty(s) ? u != null && s === "onScroll" && ui("scroll", e) : u != null && S(e, s, u, c));
							}
							switch (n) {
								case "input":
									me(e), xe(e, i, !1);
									break;
								case "textarea":
									me(e), Oe(e);
									break;
								case "option":
									i.value != null && e.setAttribute("value", "" + de(i.value));
									break;
								case "select":
									e.multiple = !!i.multiple, s = i.value, s == null ? i.defaultValue != null && we(e, !!i.multiple, i.defaultValue, !0) : we(e, !!i.multiple, s, !1);
									break;
								default: typeof o.onClick == "function" && (e.onclick = Ci);
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
					if (n = _o(go.current), _o(mo.current), Pa(t)) {
						if (i = t.stateNode, n = t.memoizedProps, i[Ii] = t, (s = i.nodeValue !== n) && (e = Ta, e !== null)) switch (e.tag) {
							case 3:
								Si(i.nodeValue, n, (e.mode & 1) != 0);
								break;
							case 5: !0 !== e.memoizedProps.suppressHydrationWarning && Si(i.nodeValue, n, (e.mode & 1) != 0);
						}
						s && (t.flags |= 4);
					} else i = (n.nodeType === 9 ? n : n.ownerDocument).createTextNode(i), i[Ii] = t, t.stateNode = i;
				}
				return mc(t), null;
			case 13:
				if (B(So), i = t.memoizedState, e === null || e.memoizedState !== null && e.memoizedState.dehydrated !== null) {
					if (Da && Ea !== null && t.mode & 1 && !(t.flags & 128)) Fa(), Ia(), t.flags |= 98560, s = !1;
					else if (s = Pa(t), i !== null && i.dehydrated !== null) {
						if (e === null) {
							if (!s) throw Error(r(318));
							if (s = t.memoizedState, s = s === null ? null : s.dehydrated, !s) throw Error(r(317));
							s[Ii] = t;
						} else Ia(), !(t.flags & 128) && (t.memoizedState = null), t.flags |= 4;
						mc(t), s = !1;
					} else Oa !== null && (Tl(Oa), Oa = null), s = !0;
					if (!s) return t.flags & 65536 ? t : null;
				}
				return t.flags & 128 ? (t.lanes = n, t) : (i = i !== null, i !== (e !== null && e.memoizedState !== null) && i && (t.child.flags |= 8192, t.mode & 1 && (e === null || So.current & 1 ? el === 0 && (el = 3) : Fl())), t.updateQueue !== null && (t.flags |= 4), mc(t), null);
			case 4: return yo(), e === null && pi(t.stateNode.containerInfo), mc(t), null;
			case 10: return Xa(t.type._context), mc(t), null;
			case 17: return ea(t.type) && ta(), mc(t), null;
			case 19:
				if (B(So), s = t.memoizedState, s === null) return mc(t), null;
				if (i = (t.flags & 128) != 0, c = s.rendering, c === null) if (i) pc(s, !1);
				else {
					if (el !== 0 || e !== null && e.flags & 128) for (e = t.child; e !== null;) {
						if (c = Co(e), c !== null) {
							for (t.flags |= 128, pc(s, !1), i = c.updateQueue, i !== null && (t.updateQueue = i, t.flags |= 4), t.subtreeFlags = 0, i = n, n = t.child; n !== null;) s = n, e = i, s.flags &= 14680066, c = s.alternate, c === null ? (s.childLanes = 0, s.lanes = e, s.child = null, s.subtreeFlags = 0, s.memoizedProps = null, s.memoizedState = null, s.updateQueue = null, s.dependencies = null, s.stateNode = null) : (s.childLanes = c.childLanes, s.lanes = c.lanes, s.child = c.child, s.subtreeFlags = 0, s.deletions = null, s.memoizedProps = c.memoizedProps, s.memoizedState = c.memoizedState, s.updateQueue = c.updateQueue, s.type = c.type, e = c.dependencies, s.dependencies = e === null ? null : {
								lanes: e.lanes,
								firstContext: e.firstContext
							}), n = n.sibling;
							return V(So, So.current & 1 | 2), t.child;
						}
						e = e.sibling;
					}
					s.tail !== null && bt() > cl && (t.flags |= 128, i = !0, pc(s, !1), t.lanes = 4194304);
				}
				else {
					if (!i) if (e = Co(c), e !== null) {
						if (t.flags |= 128, i = !0, n = e.updateQueue, n !== null && (t.updateQueue = n, t.flags |= 4), pc(s, !0), s.tail === null && s.tailMode === "hidden" && !c.alternate && !Da) return mc(t), null;
					} else 2 * bt() - s.renderingStartTime > cl && n !== 1073741824 && (t.flags |= 128, i = !0, pc(s, !1), t.lanes = 4194304);
					s.isBackwards ? (c.sibling = t.child, t.child = c) : (n = s.last, n === null ? t.child = c : n.sibling = c, s.last = c);
				}
				return s.tail === null ? (mc(t), null) : (t = s.tail, s.rendering = t, s.tail = t.sibling, s.renderingStartTime = bt(), t.sibling = null, n = So.current, V(So, i ? n & 1 | 2 : n & 1), t);
			case 22:
			case 23: return jl(), i = t.memoizedState !== null, e !== null && e.memoizedState !== null !== i && (t.flags |= 8192), i && t.mode & 1 ? Qc & 1073741824 && (mc(t), t.subtreeFlags & 6 && (t.flags |= 8192)) : mc(t), null;
			case 24: return null;
			case 25: return null;
		}
		throw Error(r(156, t.tag));
	}
	function gc(e, t) {
		switch (wa(t), t.tag) {
			case 1: return ea(t.type) && ta(), e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
			case 3: return yo(), B(Zi), B(Xi), To(), e = t.flags, e & 65536 && !(e & 128) ? (t.flags = e & -65537 | 128, t) : null;
			case 5: return xo(t), null;
			case 13:
				if (B(So), e = t.memoizedState, e !== null && e.dehydrated !== null) {
					if (t.alternate === null) throw Error(r(340));
					Ia();
				}
				return e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
			case 19: return B(So), null;
			case 4: return yo(), null;
			case 10: return Xa(t.type._context), null;
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
		if (wi = _n, e = Rr(), zr(e)) {
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
		for (Ti = {
			focusedElem: e,
			selectionRange: n
		}, _n = !1, W = t; W !== null;) if (t = W, e = t.child, t.subtreeFlags & 1028 && e !== null) e.return = t, W = e;
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
		t !== null && (e.alternate = null, Dc(t)), e.child = null, e.deletions = null, e.sibling = null, e.tag === 5 && (t = e.stateNode, t !== null && (delete t[Ii], delete t[Li], delete t[zi], delete t[Bi], delete t[Vi])), e.stateNode = null, e.return = null, e.dependencies = null, e.memoizedProps = null, e.memoizedState = null, e.pendingProps = null, e.stateNode = null, e.updateQueue = null;
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
		if (r === 5 || r === 6) e = e.stateNode, t ? n.nodeType === 8 ? n.parentNode.insertBefore(e, t) : n.insertBefore(e, t) : (n.nodeType === 8 ? (t = n.parentNode, t.insertBefore(e, n)) : (t = n, t.appendChild(e)), n = n._reactRootContainer, n != null || t.onclick !== null || (t.onclick = Ci));
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
		if (Ot && typeof Ot.onCommitFiberUnmount == "function") try {
			Ot.onCommitFiberUnmount(Dt, n);
		} catch (e) {}
		switch (n.tag) {
			case 5: vc || bc(n, t);
			case 6:
				var r = Mc, i = Nc;
				Mc = null, Pc(e, t, n), Mc = r, Nc = i, Mc !== null && (Nc ? (e = Mc, n = n.stateNode, e.nodeType === 8 ? e.parentNode.removeChild(n) : e.removeChild(n)) : Mc.removeChild(n.stateNode));
				break;
			case 18:
				Mc !== null && (Nc ? (e = Mc, n = n.stateNode, e.nodeType === 8 ? Mi(e.parentNode, n) : e.nodeType === 1 && Mi(e, n), hn(e)) : Mi(Mc, n.stateNode));
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
						Ne(a, "");
					} catch (t) {
						Gl(e, e.return, t);
					}
				}
				if (i & 4 && (a = e.stateNode, a != null)) {
					var o = e.memoizedProps, s = n === null ? o : n.memoizedProps, c = e.type, l = e.updateQueue;
					if (e.updateQueue = null, l !== null) try {
						c === "input" && o.type === "radio" && o.name != null && ye(a, o), Be(c, s);
						var u = Be(c, o);
						for (s = 0; s < l.length; s += 2) {
							var d = l[s], f = l[s + 1];
							d === "style" ? Le(a, f) : d === "dangerouslySetInnerHTML" ? Me(a, f) : d === "children" ? Ne(a, f) : S(a, d, f, u);
						}
						switch (c) {
							case "input":
								be(a, o);
								break;
							case "textarea":
								De(a, o);
								break;
							case "select":
								var p = a._wrapperState.wasMultiple;
								a._wrapperState.wasMultiple = !!o.multiple;
								var m = o.value;
								m == null ? p !== !!o.multiple && (o.defaultValue == null ? we(a, !!o.multiple, o.multiple ? [] : "", !1) : we(a, !!o.multiple, o.defaultValue, !0)) : we(a, !!o.multiple, m, !1);
						}
						a[Li] = o;
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
					hn(t.containerInfo);
				} catch (t) {
					Gl(e, e.return, t);
				}
				break;
			case 4:
				Lc(t, e), zc(e);
				break;
			case 13:
				Lc(t, e), zc(e), a = e.child, a.flags & 8192 && (o = a.memoizedState !== null, a.stateNode.isHidden = o, !o || a.alternate !== null && a.alternate.memoizedState !== null || (sl = bt())), i & 4 && Ic(e);
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
									a = f.stateNode, u ? (o = a.style, typeof o.setProperty == "function" ? o.setProperty("display", "none", "important") : o.display = "none") : (c = f.stateNode, l = f.memoizedProps.style, s = l != null && l.hasOwnProperty("display") ? l.display : null, c.style.display = Ie("display", s));
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
						i.flags & 32 && (Ne(a, ""), i.flags &= -33), jc(e, kc(e), a);
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
							o !== null && po(t, o, i);
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
								po(t, s, n);
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
										f !== null && hn(f);
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
	var Gc = Math.ceil, Kc = C.ReactCurrentDispatcher, qc = C.ReactCurrentOwner, Jc = C.ReactCurrentBatchConfig, G = 0, Yc = null, Xc = null, Zc = 0, Qc = 0, $c = Ji(0), el = 0, tl = null, nl = 0, rl = 0, il = 0, al = null, ol = null, sl = 0, cl = Infinity, ll = null, ul = !1, dl = null, fl = null, pl = !1, K = null, ml = 0, hl = 0, gl = null, _l = -1, vl = 0;
	function yl() {
		return G & 6 ? bt() : _l === -1 ? _l = bt() : _l;
	}
	function bl(e) {
		return e.mode & 1 ? G & 2 && Zc !== 0 ? Zc & -Zc : Ra.transition === null ? (e = I, e === 0 ? (e = window.event, e = e === void 0 ? 16 : Cn(e.type), e) : e) : (vl === 0 && (vl = Vt()), vl) : 1;
	}
	function xl(e, t, n, i) {
		if (50 < hl) throw hl = 0, gl = null, Error(r(185));
		Ut(e, n, i), (!(G & 2) || e !== Yc) && (e === Yc && (!(G & 2) && (rl |= n), el === 4 && Dl(e, Zc)), Sl(e, i), n === 1 && G === 0 && !(t.mode & 1) && (cl = bt() + 500, sa && da()));
	}
	function Sl(e, t) {
		var n = e.callbackNode;
		zt(e, t);
		var r = Lt(e, e === Yc ? Zc : 0);
		if (r === 0) n !== null && _t(n), e.callbackNode = null, e.callbackPriority = 0;
		else if (t = r & -r, e.callbackPriority !== t) {
			if (n != null && _t(n), t === 1) e.tag === 0 ? ua(Ol.bind(null, e)) : la(Ol.bind(null, e)), Ai(function() {
				!(G & 6) && da();
			}), n = null;
			else {
				switch (Kt(r)) {
					case 1:
						n = St;
						break;
					case 4:
						n = Ct;
						break;
					case 16:
						n = wt;
						break;
					case 536870912:
						n = Et;
						break;
					default: n = wt;
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
		var i = Lt(e, e === Yc ? Zc : 0);
		if (i === 0) return null;
		if (i & 30 || (i & e.expiredLanes) !== 0 || t) t = Il(e, i);
		else {
			t = i;
			var a = G;
			G |= 2;
			var o = Pl();
			(Yc !== e || Zc !== t) && (ll = null, cl = bt() + 500, Ml(e, t));
			do
				try {
					Rl();
					break;
				} catch (t) {
					Nl(e, t);
				}
			while (1);
			Ya(), Kc.current = o, G = a, Xc === null ? (Yc = null, Zc = 0, t = el) : t = 0;
		}
		if (t !== 0) {
			if (t === 2 && (a = Bt(e), a !== 0 && (i = a, t = wl(e, a))), t === 1) throw n = tl, Ml(e, 0), Dl(e, i), Sl(e, bt()), n;
			if (t === 6) Dl(e, i);
			else {
				if (a = e.current.alternate, !(i & 30) && !El(a) && (t = Il(e, i), t === 2 && (o = Bt(e), o !== 0 && (i = o, t = wl(e, o))), t === 1)) throw n = tl, Ml(e, 0), Dl(e, i), Sl(e, bt()), n;
				switch (e.finishedWork = a, e.finishedLanes = i, t) {
					case 0:
					case 1: throw Error(r(345));
					case 2:
						Vl(e, ol, ll);
						break;
					case 3:
						if (Dl(e, i), (i & 130023424) === i && (t = sl + 500 - bt(), 10 < t)) {
							if (Lt(e, 0) !== 0) break;
							if (a = e.suspendedLanes, (a & i) !== i) {
								yl(), e.pingedLanes |= e.suspendedLanes & a;
								break;
							}
							e.timeoutHandle = Di(Vl.bind(null, e, ol, ll), t);
							break;
						}
						Vl(e, ol, ll);
						break;
					case 4:
						if (Dl(e, i), (i & 4194240) === i) break;
						for (t = e.eventTimes, a = -1; 0 < i;) {
							var s = 31 - At(i);
							o = 1 << s, s = t[s], s > a && (a = s), i &= ~o;
						}
						if (i = a, i = bt() - i, i = (120 > i ? 120 : 480 > i ? 480 : 1080 > i ? 1080 : 1920 > i ? 1920 : 3e3 > i ? 3e3 : 4320 > i ? 4320 : 1960 * Gc(i / 1960)) - i, 10 < i) {
							e.timeoutHandle = Di(Vl.bind(null, e, ol, ll), i);
							break;
						}
						Vl(e, ol, ll);
						break;
					case 5:
						Vl(e, ol, ll);
						break;
					default: throw Error(r(329));
				}
			}
		}
		return Sl(e, bt()), e.callbackNode === n ? Cl.bind(null, e) : null;
	}
	function wl(e, t) {
		var n = al;
		return e.current.memoizedState.isDehydrated && (Ml(e, t).flags |= 256), e = Il(e, t), e !== 2 && (t = ol, ol = n, t !== null && Tl(t)), e;
	}
	function Tl(e) {
		ol === null ? ol = e : ol.push.apply(ol, e);
	}
	function El(e) {
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
	function Dl(e, t) {
		for (t &= ~il, t &= ~rl, e.suspendedLanes |= t, e.pingedLanes &= ~t, e = e.expirationTimes; 0 < t;) {
			var n = 31 - At(t), r = 1 << n;
			e[n] = -1, t &= ~r;
		}
	}
	function Ol(e) {
		if (G & 6) throw Error(r(327));
		Ul();
		var t = Lt(e, 0);
		if (!(t & 1)) return Sl(e, bt()), null;
		var n = Il(e, t);
		if (e.tag !== 0 && n === 2) {
			var i = Bt(e);
			i !== 0 && (t = i, n = wl(e, i));
		}
		if (n === 1) throw n = tl, Ml(e, 0), Dl(e, t), Sl(e, bt()), n;
		if (n === 6) throw Error(r(345));
		return e.finishedWork = e.current.alternate, e.finishedLanes = t, Vl(e, ol, ll), Sl(e, bt()), null;
	}
	function kl(e, t) {
		var n = G;
		G |= 1;
		try {
			return e(t);
		} finally {
			G = n, G === 0 && (cl = bt() + 500, sa && da());
		}
	}
	function Al(e) {
		K !== null && K.tag === 0 && !(G & 6) && Ul();
		var t = G;
		G |= 1;
		var n = Jc.transition, r = I;
		try {
			if (Jc.transition = null, I = 1, e) return e();
		} finally {
			I = r, Jc.transition = n, G = t, !(G & 6) && da();
		}
	}
	function jl() {
		Qc = $c.current, B($c);
	}
	function Ml(e, t) {
		e.finishedWork = null, e.finishedLanes = 0;
		var n = e.timeoutHandle;
		if (n !== -1 && (e.timeoutHandle = -1, Oi(n)), Xc !== null) for (n = Xc.return; n !== null;) {
			var r = n;
			switch (wa(r), r.tag) {
				case 1:
					r = r.type.childContextTypes, r != null && ta();
					break;
				case 3:
					yo(), B(Zi), B(Xi), To();
					break;
				case 5:
					xo(r);
					break;
				case 4:
					yo();
					break;
				case 13:
					B(So);
					break;
				case 19:
					B(So);
					break;
				case 10:
					Xa(r.type._context);
					break;
				case 22:
				case 23: jl();
			}
			n = n.return;
		}
		if (Yc = e, Xc = e = nu(e.current, null), Zc = Qc = t, el = 0, tl = null, il = rl = nl = 0, ol = al = null, eo !== null) {
			for (t = 0; t < eo.length; t++) if (n = eo[t], r = n.interleaved, r !== null) {
				n.interleaved = null;
				var i = r.next, a = n.pending;
				if (a !== null) {
					var o = a.next;
					a.next = i, r.next = o;
				}
				n.pending = r;
			}
			eo = null;
		}
		return e;
	}
	function Nl(e, t) {
		do {
			var n = Xc;
			try {
				if (Ya(), Eo.current = bs, Mo) {
					for (var i = ko.memoizedState; i !== null;) {
						var a = i.queue;
						a !== null && (a.pending = null), i = i.next;
					}
					Mo = !1;
				}
				if (Oo = 0, jo = Ao = ko = null, No = !1, Po = 0, qc.current = null, n === null || n.return === null) {
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
					} else if (Da && c.mode & 1) {
						var _ = Ls(s);
						if (_ !== null) {
							!(_.flags & 65536) && (_.flags |= 256), Rs(_, s, c, o, t), La(js(l, c));
							break a;
						}
					}
					o = l = js(l, c), el !== 4 && (el = 2), al === null ? al = [o] : al.push(o), o = s;
					do {
						switch (o.tag) {
							case 3:
								o.flags |= 65536, t &= -t, o.lanes |= t;
								var v = Fs(o, l, t);
								uo(o, v);
								break a;
							case 1:
								c = l;
								var y = o.type, b = o.stateNode;
								if (!(o.flags & 128) && (typeof y.getDerivedStateFromError == "function" || b !== null && typeof b.componentDidCatch == "function" && (fl === null || !fl.has(b)))) {
									o.flags |= 65536, t &= -t, o.lanes |= t;
									var x = U(o, c, t);
									uo(o, x);
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
		(el === 0 || el === 3 || el === 2) && (el = 4), Yc === null || !(nl & 268435455) && !(rl & 268435455) || Dl(Yc, Zc);
	}
	function Il(e, t) {
		var n = G;
		G |= 2;
		var i = Pl();
		(Yc !== e || Zc !== t) && (ll = null, Ml(e, t));
		do
			try {
				Ll();
				break;
			} catch (t) {
				Nl(e, t);
			}
		while (1);
		if (Ya(), G = n, Kc.current = i, Xc !== null) throw Error(r(261));
		return Yc = null, Zc = 0, el;
	}
	function Ll() {
		for (; Xc !== null;) zl(Xc);
	}
	function Rl() {
		for (; Xc !== null && !vt();) zl(Xc);
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
		var r = I, i = Jc.transition;
		try {
			Jc.transition = null, I = 1, Hl(e, t, n, r);
		} finally {
			Jc.transition = i, I = r;
		}
		return null;
	}
	function Hl(e, t, n, i) {
		do
			Ul();
		while (K !== null);
		if (G & 6) throw Error(r(327));
		n = e.finishedWork;
		var a = e.finishedLanes;
		if (n === null) return null;
		if (e.finishedWork = null, e.finishedLanes = 0, n === e.current) throw Error(r(177));
		e.callbackNode = null, e.callbackPriority = 0;
		var o = n.lanes | n.childLanes;
		if (Wt(e, o), e === Yc && (Xc = Yc = null, Zc = 0), !(n.subtreeFlags & 2064) && !(n.flags & 2064) || pl || (pl = !0, Zl(wt, function() {
			return Ul(), null;
		})), o = (n.flags & 15990) != 0, n.subtreeFlags & 15990 || o) {
			o = Jc.transition, Jc.transition = null;
			var s = I;
			I = 1;
			var c = G;
			G |= 4, qc.current = null, Cc(e, n), Rc(n, e), Br(Ti), _n = !!wi, Ti = wi = null, e.current = n, Bc(n, e, a), yt(), G = c, I = s, Jc.transition = o;
		} else e.current = n;
		if (pl && (pl = !1, K = e, ml = a), o = e.pendingLanes, o === 0 && (fl = null), kt(n.stateNode, i), Sl(e, bt()), t !== null) for (i = e.onRecoverableError, n = 0; n < t.length; n++) a = t[n], i(a.value, {
			componentStack: a.stack,
			digest: a.digest
		});
		if (ul) throw ul = !1, e = dl, dl = null, e;
		return ml & 1 && e.tag !== 0 && Ul(), o = e.pendingLanes, o & 1 ? e === gl ? hl++ : (hl = 0, gl = e) : hl = 0, da(), null;
	}
	function Ul() {
		if (K !== null) {
			var e = Kt(ml), t = Jc.transition, n = I;
			try {
				if (Jc.transition = null, I = 16 > e ? 16 : e, K === null) var i = !1;
				else {
					if (e = K, K = null, ml = 0, G & 6) throw Error(r(331));
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
					if (G = a, da(), Ot && typeof Ot.onPostCommitFiberRoot == "function") try {
						Ot.onPostCommitFiberRoot(Dt, e);
					} catch (e) {}
					i = !0;
				}
				return i;
			} finally {
				I = n, Jc.transition = t;
			}
		}
		return !1;
	}
	function Wl(e, t, n) {
		t = js(n, t), t = Fs(e, t, 1), e = co(e, t, 1), t = yl(), e !== null && (Ut(e, 1, t), Sl(e, t));
	}
	function Gl(e, t, n) {
		if (e.tag === 3) Wl(e, e, n);
		else for (; t !== null;) {
			if (t.tag === 3) {
				Wl(t, e, n);
				break;
			} else if (t.tag === 1) {
				var r = t.stateNode;
				if (typeof t.type.getDerivedStateFromError == "function" || typeof r.componentDidCatch == "function" && (fl === null || !fl.has(r))) {
					e = js(n, e), e = U(t, e, 1), t = co(t, e, 1), e = yl(), t !== null && (Ut(t, 1, e), Sl(t, e));
					break;
				}
			}
			t = t.return;
		}
	}
	function Kl(e, t, n) {
		var r = e.pingCache;
		r !== null && r.delete(t), t = yl(), e.pingedLanes |= e.suspendedLanes & n, Yc === e && (Zc & n) === n && (el === 4 || el === 3 && (Zc & 130023424) === Zc && 500 > bt() - sl ? Ml(e, 0) : il |= n), Sl(e, t);
	}
	function ql(e, t) {
		t === 0 && (e.mode & 1 ? (t = Ft, Ft <<= 1, !(Ft & 130023424) && (Ft = 4194304)) : t = 1);
		var n = yl();
		e = ro(e, t), e !== null && (Ut(e, t, n), Sl(e, n));
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
		if (e !== null) if (e.memoizedProps !== t.pendingProps || Zi.current) Bs = !0;
		else {
			if ((e.lanes & n) === 0 && !(t.flags & 128)) return Bs = !1, lc(e, t, n);
			Bs = !!(e.flags & 131072);
		}
		else Bs = !1, Da && t.flags & 1048576 && Sa(t, ha, t.index);
		switch (t.lanes = 0, t.tag) {
			case 2:
				var i = t.type;
				sc(e, t), e = t.pendingProps;
				var a = $i(t, Xi.current);
				Qa(t, n), a = Ro(null, t, i, e, a, n);
				var o = zo();
				return t.flags |= 1, typeof a == "object" && a && typeof a.render == "function" && a.$$typeof === void 0 ? (t.tag = 1, t.memoizedState = null, t.updateQueue = null, ea(i) ? (o = !0, ia(t)) : o = !1, t.memoizedState = a.state !== null && a.state !== void 0 ? a.state : null, ao(t), a.updater = Es, t.stateNode = a, a._reactInternals = t, As(t, i, e, n), t = Ys(null, t, i, !0, o, n)) : (t.tag = 0, Da && o && Ca(t), Vs(null, t, a, n), t = t.child), t;
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
					i = t.pendingProps, o = t.memoizedState, a = o.element, oo(e, t), fo(t, i, null, n);
					var s = t.memoizedState;
					if (i = s.element, o.isDehydrated) if (o = {
						element: i,
						isDehydrated: !1,
						cache: s.cache,
						pendingSuspenseBoundaries: s.pendingSuspenseBoundaries,
						transitions: s.transitions
					}, t.updateQueue.baseState = o, t.memoizedState = o, t.flags & 256) {
						a = js(Error(r(423)), t), t = Zs(e, t, i, n, a);
						break a;
					} else if (i !== a) {
						a = js(Error(r(424)), t), t = Zs(e, t, i, n, a);
						break a;
					} else for (Ea = Ni(t.stateNode.containerInfo.firstChild), Ta = t, Da = !0, Oa = null, n = Wa(t, null, i, n), t.child = n; n;) n.flags = n.flags & -3 | 4096, n = n.sibling;
					else {
						if (Ia(), i === a) {
							t = cc(e, t, n);
							break a;
						}
						Vs(e, t, i, n);
					}
					t = t.child;
				}
				return t;
			case 5: return bo(t), e === null && Ma(t), i = t.type, a = t.pendingProps, o = e === null ? null : e.memoizedProps, s = a.children, Ei(i, a) ? s = null : o !== null && Ei(i, o) && (t.flags |= 32), Ks(e, t), Vs(e, t, s, n), t.child;
			case 6: return e === null && Ma(t), null;
			case 13: return ec(e, t, n);
			case 4: return vo(t, t.stateNode.containerInfo), i = t.pendingProps, e === null ? t.child = Ua(t, null, i, n) : Vs(e, t, i, n), t.child;
			case 11: return i = t.type, a = t.pendingProps, a = t.elementType === i ? a : ws(i, a), Hs(e, t, i, a, n);
			case 7: return Vs(e, t, t.pendingProps, n), t.child;
			case 8: return Vs(e, t, t.pendingProps.children, n), t.child;
			case 12: return Vs(e, t, t.pendingProps.children, n), t.child;
			case 10:
				a: {
					if (i = t.type._context, a = t.pendingProps, o = t.memoizedProps, s = a.value, V(Ga, i._currentValue), i._currentValue = s, o !== null) if (Nr(o.value, s)) {
						if (o.children === a.children && !Zi.current) {
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
										l = so(-1, n & -n), l.tag = 2;
										var u = o.updateQueue;
										if (u !== null) {
											u = u.shared;
											var d = u.pending;
											d === null ? l.next = l : (l.next = d.next, d.next = l), u.pending = l;
										}
									}
									o.lanes |= n, l = o.alternate, l !== null && (l.lanes |= n), Za(o.return, n, t), c.lanes |= n;
									break;
								}
								l = l.next;
							}
						} else if (o.tag === 10) s = o.type === t.type ? null : o.child;
						else if (o.tag === 18) {
							if (s = o.return, s === null) throw Error(r(341));
							s.lanes |= n, c = s.alternate, c !== null && (c.lanes |= n), Za(s, n, t), s = o.sibling;
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
			case 9: return a = t.type, i = t.pendingProps.children, Qa(t, n), a = $a(a), i = i(a), t.flags |= 1, Vs(e, t, i, n), t.child;
			case 14: return i = t.type, a = ws(i, t.pendingProps), a = ws(i.type, a), Us(e, t, i, a, n);
			case 15: return Ws(e, t, t.type, t.pendingProps, n);
			case 17: return i = t.type, a = t.pendingProps, a = t.elementType === i ? a : ws(i, a), sc(e, t), t.tag = 1, ea(i) ? (e = !0, ia(t)) : e = !1, Qa(t, n), Os(t, i, a), As(t, i, a, n), Ys(null, t, i, !0, e, n);
			case 19: return oc(e, t, n);
			case 22: return Gs(e, t, n);
		}
		throw Error(r(156, t.tag));
	};
	function Zl(e, t) {
		return gt(e, t);
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
			case ee: return au(n, a, o, t);
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
					case F:
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
		return e = $l(22, e, r, t), e.elementType = ee, e.lanes = n, e.stateNode = { isHidden: !1 }, e;
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
		this.tag = t, this.containerInfo = e, this.finishedWork = this.pingCache = this.current = this.pendingChildren = null, this.timeoutHandle = -1, this.callbackNode = this.pendingContext = this.context = null, this.callbackPriority = 0, this.eventTimes = Ht(0), this.expirationTimes = Ht(-1), this.entangledLanes = this.finishedLanes = this.mutableReadLanes = this.expiredLanes = this.pingedLanes = this.suspendedLanes = this.pendingLanes = 0, this.entanglements = Ht(0), this.identifierPrefix = r, this.onRecoverableError = i, this.mutableSourceEagerHydrationData = null;
	}
	function lu(e, t, n, r, i, a, o, s, c) {
		return e = new cu(e, t, n, s, c), t === 1 ? (t = 1, !0 === a && (t |= 8)) : t = 0, a = $l(3, null, null, t), e.current = a, a.stateNode = e, a.memoizedState = {
			element: r,
			isDehydrated: n,
			cache: null,
			transitions: null,
			pendingSuspenseBoundaries: null
		}, ao(a), e;
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
		if (!e) return Yi;
		e = e._reactInternals;
		a: {
			if (ut(e) !== e || e.tag !== 1) throw Error(r(170));
			var t = e;
			do {
				switch (t.tag) {
					case 3:
						t = t.stateNode.context;
						break a;
					case 1: if (ea(t.type)) {
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
			if (ea(n)) return ra(e, n, t);
		}
		return t;
	}
	function fu(e, t, n, r, i, a, o, s, c) {
		return e = lu(n, r, !0, e, i, a, o, s, c), e.context = du(null), n = e.current, r = yl(), i = bl(n), a = so(r, i), a.callback = t == null ? null : t, co(n, a, i), e.current.lanes = i, Ut(e, i, r), Sl(e, r), e;
	}
	function pu(e, t, n, r) {
		var i = t.current, a = yl(), o = bl(i);
		return n = du(n), t.context === null ? t.context = n : t.pendingContext = n, t = so(a, o), t.payload = { element: e }, r = r === void 0 ? null : r, r !== null && (t.callback = r), e = co(i, t, o), e !== null && (xl(e, i, o, a), lo(e, i, o)), o;
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
			}), t[Ri] = null;
		}
	};
	function bu(e) {
		this._internalRoot = e;
	}
	bu.prototype.unstable_scheduleHydration = function(e) {
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
			return e._reactRootContainer = o, e[Ri] = o.current, pi(e.nodeType === 8 ? e.parentNode : e), Al(), o;
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
		return e._reactRootContainer = c, e[Ri] = c.current, pi(e.nodeType === 8 ? e.parentNode : e), Al(function() {
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
	qt = function(e) {
		switch (e.tag) {
			case 3:
				var t = e.stateNode;
				if (t.current.memoizedState.isDehydrated) {
					var n = It(t.pendingLanes);
					n !== 0 && (Gt(t, n | 1), Sl(t, bt()), !(G & 6) && (cl = bt() + 500, da()));
				}
				break;
			case 13: Al(function() {
				var t = ro(e, 1);
				t !== null && xl(t, e, 1, yl());
			}), gu(e, 1);
		}
	}, Jt = function(e) {
		if (e.tag === 13) {
			var t = ro(e, 134217728);
			t !== null && xl(t, e, 134217728, yl()), gu(e, 134217728);
		}
	}, Yt = function(e) {
		if (e.tag === 13) {
			var t = bl(e), n = ro(e, t);
			n !== null && xl(n, e, t, yl()), gu(e, t);
		}
	}, Xt = function() {
		return I;
	}, Zt = function(e, t) {
		var n = I;
		try {
			return I = e, t();
		} finally {
			I = n;
		}
	}, Ue = function(e, t, n) {
		switch (t) {
			case "input":
				if (be(e, n), t = n.name, n.type === "radio" && t != null) {
					for (n = e; n.parentNode;) n = n.parentNode;
					for (n = n.querySelectorAll("input[name=" + JSON.stringify("" + t) + "][type=\"radio\"]"), t = 0; t < n.length; t++) {
						var i = n[t];
						if (i !== e && i.form === e.form) {
							var a = Gi(i);
							if (!a) throw Error(r(90));
							he(i), be(i, a);
						}
					}
				}
				break;
			case "textarea":
				De(e, n);
				break;
			case "select": t = n.value, t != null && we(e, !!n.multiple, t, !1);
		}
	}, Ye = kl, Xe = Al;
	var Eu = {
		usingClientEntryPoint: !1,
		Events: [
			Ui,
			Wi,
			Gi,
			qe,
			Je,
			kl
		]
	}, Du = {
		findFiberByHostInstance: Hi,
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
			return e = mt(e), e === null ? null : e.stateNode;
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
			Dt = ku.inject(Ou), Ot = ku;
		} catch (e) {}
	}
	e.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED = Eu, e.createPortal = function(e, t) {
		var n = 2 < arguments.length && arguments[2] !== void 0 ? arguments[2] : null;
		if (!xu(t)) throw Error(r(200));
		return uu(e, t, null, n);
	}, e.createRoot = function(e, t) {
		if (!xu(e)) throw Error(r(299));
		var n = !1, i = "", a = vu;
		return t != null && (!0 === t.unstable_strictMode && (n = !0), t.identifierPrefix !== void 0 && (i = t.identifierPrefix), t.onRecoverableError !== void 0 && (a = t.onRecoverableError)), t = lu(e, 1, !1, null, null, n, !1, i, a), e[Ri] = t.current, pi(e.nodeType === 8 ? e.parentNode : e), new yu(t);
	}, e.findDOMNode = function(e) {
		if (e == null) return null;
		if (e.nodeType === 1) return e;
		var t = e._reactInternals;
		if (t === void 0) throw typeof e.render == "function" ? Error(r(188)) : (e = Object.keys(e).join(","), Error(r(268, e)));
		return e = mt(t), e = e === null ? null : e.stateNode, e;
	}, e.flushSync = function(e) {
		return Al(e);
	}, e.hydrate = function(e, t, n) {
		if (!Su(t)) throw Error(r(200));
		return Tu(null, e, t, !0, n);
	}, e.hydrateRoot = function(e, t, n) {
		if (!xu(e)) throw Error(r(405));
		var i = n != null && n.hydratedSources || null, a = !1, o = "", s = vu;
		if (n != null && (!0 === n.unstable_strictMode && (a = !0), n.identifierPrefix !== void 0 && (o = n.identifierPrefix), n.onRecoverableError !== void 0 && (s = n.onRecoverableError)), t = fu(t, null, e, 1, n == null ? null : n, a, !1, o, s), e[Ri] = t.current, pi(e), i) for (e = 0; e < i.length; e++) n = i[e], a = n._getVersion, a = a(n._source), t.mutableSourceEagerHydrationData == null ? t.mutableSourceEagerHydrationData = [n, a] : t.mutableSourceEagerHydrationData.push(n, a);
		return new bu(t);
	}, e.render = function(e, t, n) {
		if (!Su(t)) throw Error(r(200));
		return Tu(null, e, t, !1, n);
	}, e.unmountComponentAtNode = function(e) {
		if (!Su(e)) throw Error(r(40));
		return e._reactRootContainer ? (Al(function() {
			Tu(null, null, e, !1, function() {
				e._reactRootContainer = null, e[Ri] = null;
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
]), A = D("bot", [
	["path", {
		d: "M12 8V4H8",
		key: "hb8ula"
	}],
	["rect", {
		width: "16",
		height: "12",
		x: "4",
		y: "8",
		rx: "2",
		key: "enze0r"
	}],
	["path", {
		d: "M2 14h2",
		key: "vft8re"
	}],
	["path", {
		d: "M20 14h2",
		key: "4cs60a"
	}],
	["path", {
		d: "M15 13v2",
		key: "1xurst"
	}],
	["path", {
		d: "M9 13v2",
		key: "rq6x2g"
	}]
]), j = D("briefcase-business", [
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
]), M = D("check", [["path", {
	d: "M20 6 9 17l-5-5",
	key: "1gmf2c"
}]]), N = D("chevron-down", [["path", {
	d: "m6 9 6 6 6-6",
	key: "qrunsl"
}]]), P = D("chevron-right", [["path", {
	d: "m9 18 6-6-6-6",
	key: "mthhwq"
}]]), F = D("chevron-up", [["path", {
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
}]]), te = D("circle-x", [
	["circle", {
		cx: "12",
		cy: "12",
		r: "10",
		key: "1mglay"
	}],
	["path", {
		d: "m15 9-6 6",
		key: "1uzhvr"
	}],
	["path", {
		d: "m9 9 6 6",
		key: "z0biqf"
	}]
]), ne = D("circle", [["circle", {
	cx: "12",
	cy: "12",
	r: "10",
	key: "1mglay"
}]]), re = D("clipboard-check", [
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
]), ie = D("clipboard-list", [
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
]), ae = D("clock-3", [["circle", {
	cx: "12",
	cy: "12",
	r: "10",
	key: "1mglay"
}], ["path", {
	d: "M12 6v6h4",
	key: "135r8i"
}]]), oe = D("clock", [["circle", {
	cx: "12",
	cy: "12",
	r: "10",
	key: "1mglay"
}], ["path", {
	d: "M12 6v6l4 2",
	key: "mmk7yg"
}]]), se = D("database", [
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
]), ce = D("external-link", [
	["path", {
		d: "M15 3h6v6",
		key: "1q9fwt"
	}],
	["path", {
		d: "M10 14 21 3",
		key: "gplh6r"
	}],
	["path", {
		d: "M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6",
		key: "a6xqqp"
	}]
]), le = D("file-question-mark", [
	["path", {
		d: "M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z",
		key: "1oefj6"
	}],
	["path", {
		d: "M12 17h.01",
		key: "p32p05"
	}],
	["path", {
		d: "M9.1 9a3 3 0 0 1 5.82 1c0 2-3 3-3 3",
		key: "mhlwft"
	}]
]), ue = D("file-search", [
	["path", {
		d: "M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z",
		key: "1oefj6"
	}],
	["path", {
		d: "M14 2v5a1 1 0 0 0 1 1h5",
		key: "wfsgrz"
	}],
	["circle", {
		cx: "11.5",
		cy: "14.5",
		r: "2.5",
		key: "1bq0ko"
	}],
	["path", {
		d: "M13.3 16.3 15 18",
		key: "2quom7"
	}]
]), de = D("file-text", [
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
]), fe = D("folder-heart", [["path", {
	d: "M10.638 20H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H20a2 2 0 0 1 2 2v3.417",
	key: "10r6g4"
}], ["path", {
	d: "M14.62 18.8A2.25 2.25 0 1 1 18 15.836a2.25 2.25 0 1 1 3.38 2.966l-2.626 2.856a.998.998 0 0 1-1.507 0z",
	key: "15cy7q"
}]]), pe = D("inbox", [["polyline", {
	points: "22 12 16 12 14 15 10 15 8 12 2 12",
	key: "o97t9d"
}], ["path", {
	d: "M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z",
	key: "oot6mr"
}]]), me = D("info", [
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
]), he = D("list-checks", [
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
]), ge = D("messages-square", [["path", {
	d: "M16 10a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 14.286V4a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z",
	key: "1n2ejm"
}], ["path", {
	d: "M20 9a2 2 0 0 1 2 2v10.286a.71.71 0 0 1-1.212.502l-2.202-2.202A2 2 0 0 0 17.172 19H10a2 2 0 0 1-2-2v-1",
	key: "1qfcsi"
}]]), _e = D("minus", [["path", {
	d: "M5 12h14",
	key: "1ays0h"
}]]), ve = D("play", [["path", {
	d: "M5 5a2 2 0 0 1 3.008-1.728l11.997 6.998a2 2 0 0 1 .003 3.458l-12 7A2 2 0 0 1 5 19z",
	key: "10ikf1"
}]]), ye = D("power", [["path", {
	d: "M12 2v10",
	key: "mnfbl"
}], ["path", {
	d: "M18.4 6.6a9 9 0 1 1-12.77.04",
	key: "obofu9"
}]]), be = D("refresh-cw", [
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
]), xe = D("rotate-ccw", [["path", {
	d: "M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8",
	key: "1357e3"
}], ["path", {
	d: "M3 3v5h5",
	key: "1xhq8a"
}]]), Se = D("rows-3", [
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
]), Ce = D("search", [["path", {
	d: "m21 21-4.34-4.34",
	key: "14j7rj"
}], ["circle", {
	cx: "11",
	cy: "11",
	r: "8",
	key: "4ej97u"
}]]), we = D("settings-2", [
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
]), Te = D("shield-check", [["path", {
	d: "M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z",
	key: "oel41y"
}], ["path", {
	d: "m9 12 2 2 4-4",
	key: "dzmm74"
}]]), Ee = D("triangle-alert", [
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
]), De = D("user-round-check", [
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
]), Oe = D("users-round", [
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
]), ke = D("wand-sparkles", [
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
]), Ae = D("workflow", [
	["rect", {
		width: "8",
		height: "8",
		x: "3",
		y: "3",
		rx: "2",
		key: "by2w9f"
	}],
	["path", {
		d: "M7 11v4a2 2 0 0 0 2 2h4",
		key: "xkn7yn"
	}],
	["rect", {
		width: "8",
		height: "8",
		x: "13",
		y: "13",
		rx: "2",
		key: "1cgmvn"
	}]
]), je = D("x", [["path", {
	d: "M18 6 6 18",
	key: "1bl5f8"
}], ["path", {
	d: "m6 6 12 12",
	key: "d8bk6v"
}]]);
//#endregion
//#region node_modules/clsx/dist/clsx.mjs
function Me(e) {
	var t, n, r = "";
	if (typeof e == "string" || typeof e == "number") r += e;
	else if (typeof e == "object") if (Array.isArray(e)) {
		var i = e.length;
		for (t = 0; t < i; t++) e[t] && (n = Me(e[t])) && (r && (r += " "), r += n);
	} else for (n in e) e[n] && (r && (r += " "), r += n);
	return r;
}
function Ne() {
	for (var e, t, n = 0, r = "", i = arguments.length; n < i; n++) (e = arguments[n]) && (t = Me(e)) && (r && (r += " "), r += t);
	return r;
}
//#endregion
//#region node_modules/recharts/es6/util/excludeEventProps.js
var Pe = /* @__PURE__ */ "dangerouslySetInnerHTML.onCopy.onCopyCapture.onCut.onCutCapture.onPaste.onPasteCapture.onCompositionEnd.onCompositionEndCapture.onCompositionStart.onCompositionStartCapture.onCompositionUpdate.onCompositionUpdateCapture.onFocus.onFocusCapture.onBlur.onBlurCapture.onChange.onChangeCapture.onBeforeInput.onBeforeInputCapture.onInput.onInputCapture.onReset.onResetCapture.onSubmit.onSubmitCapture.onInvalid.onInvalidCapture.onLoad.onLoadCapture.onError.onErrorCapture.onKeyDown.onKeyDownCapture.onKeyPress.onKeyPressCapture.onKeyUp.onKeyUpCapture.onAbort.onAbortCapture.onCanPlay.onCanPlayCapture.onCanPlayThrough.onCanPlayThroughCapture.onDurationChange.onDurationChangeCapture.onEmptied.onEmptiedCapture.onEncrypted.onEncryptedCapture.onEnded.onEndedCapture.onLoadedData.onLoadedDataCapture.onLoadedMetadata.onLoadedMetadataCapture.onLoadStart.onLoadStartCapture.onPause.onPauseCapture.onPlay.onPlayCapture.onPlaying.onPlayingCapture.onProgress.onProgressCapture.onRateChange.onRateChangeCapture.onSeeked.onSeekedCapture.onSeeking.onSeekingCapture.onStalled.onStalledCapture.onSuspend.onSuspendCapture.onTimeUpdate.onTimeUpdateCapture.onVolumeChange.onVolumeChangeCapture.onWaiting.onWaitingCapture.onAuxClick.onAuxClickCapture.onClick.onClickCapture.onContextMenu.onContextMenuCapture.onDoubleClick.onDoubleClickCapture.onDrag.onDragCapture.onDragEnd.onDragEndCapture.onDragEnter.onDragEnterCapture.onDragExit.onDragExitCapture.onDragLeave.onDragLeaveCapture.onDragOver.onDragOverCapture.onDragStart.onDragStartCapture.onDrop.onDropCapture.onMouseDown.onMouseDownCapture.onMouseEnter.onMouseLeave.onMouseMove.onMouseMoveCapture.onMouseOut.onMouseOutCapture.onMouseOver.onMouseOverCapture.onMouseUp.onMouseUpCapture.onSelect.onSelectCapture.onTouchCancel.onTouchCancelCapture.onTouchEnd.onTouchEndCapture.onTouchMove.onTouchMoveCapture.onTouchStart.onTouchStartCapture.onPointerDown.onPointerDownCapture.onPointerMove.onPointerMoveCapture.onPointerUp.onPointerUpCapture.onPointerCancel.onPointerCancelCapture.onPointerEnter.onPointerEnterCapture.onPointerLeave.onPointerLeaveCapture.onPointerOver.onPointerOverCapture.onPointerOut.onPointerOutCapture.onGotPointerCapture.onGotPointerCaptureCapture.onLostPointerCapture.onLostPointerCaptureCapture.onScroll.onScrollCapture.onWheel.onWheelCapture.onAnimationStart.onAnimationStartCapture.onAnimationEnd.onAnimationEndCapture.onAnimationIteration.onAnimationIterationCapture.onTransitionEnd.onTransitionEndCapture".split(".");
function Fe(e) {
	return typeof e == "string" && Pe.includes(e);
}
//#endregion
//#region node_modules/recharts/es6/util/svgPropertiesNoEvents.js
var Ie = /* @__PURE__ */ new Set(/* @__PURE__ */ "aria-activedescendant.aria-atomic.aria-autocomplete.aria-busy.aria-checked.aria-colcount.aria-colindex.aria-colspan.aria-controls.aria-current.aria-describedby.aria-details.aria-disabled.aria-errormessage.aria-expanded.aria-flowto.aria-haspopup.aria-hidden.aria-invalid.aria-keyshortcuts.aria-label.aria-labelledby.aria-level.aria-live.aria-modal.aria-multiline.aria-multiselectable.aria-orientation.aria-owns.aria-placeholder.aria-posinset.aria-pressed.aria-readonly.aria-relevant.aria-required.aria-roledescription.aria-rowcount.aria-rowindex.aria-rowspan.aria-selected.aria-setsize.aria-sort.aria-valuemax.aria-valuemin.aria-valuenow.aria-valuetext.className.color.height.id.lang.max.media.method.min.name.style.target.width.role.tabIndex.accentHeight.accumulate.additive.alignmentBaseline.allowReorder.alphabetic.amplitude.arabicForm.ascent.attributeName.attributeType.autoReverse.azimuth.baseFrequency.baselineShift.baseProfile.bbox.begin.bias.by.calcMode.capHeight.clip.clipPath.clipPathUnits.clipRule.colorInterpolation.colorInterpolationFilters.colorProfile.colorRendering.contentScriptType.contentStyleType.cursor.cx.cy.d.decelerate.descent.diffuseConstant.direction.display.divisor.dominantBaseline.dur.dx.dy.edgeMode.elevation.enableBackground.end.exponent.externalResourcesRequired.fill.fillOpacity.fillRule.filter.filterRes.filterUnits.floodColor.floodOpacity.focusable.fontFamily.fontSize.fontSizeAdjust.fontStretch.fontStyle.fontVariant.fontWeight.format.from.fx.fy.g1.g2.glyphName.glyphOrientationHorizontal.glyphOrientationVertical.glyphRef.gradientTransform.gradientUnits.hanging.horizAdvX.horizOriginX.href.ideographic.imageRendering.in2.in.intercept.k1.k2.k3.k4.k.kernelMatrix.kernelUnitLength.kerning.keyPoints.keySplines.keyTimes.lengthAdjust.letterSpacing.lightingColor.limitingConeAngle.local.markerEnd.markerHeight.markerMid.markerStart.markerUnits.markerWidth.mask.maskContentUnits.maskUnits.mathematical.mode.numOctaves.offset.opacity.operator.order.orient.orientation.origin.overflow.overlinePosition.overlineThickness.paintOrder.panose1.pathLength.patternContentUnits.patternTransform.patternUnits.pointerEvents.pointsAtX.pointsAtY.pointsAtZ.preserveAlpha.preserveAspectRatio.primitiveUnits.r.radius.refX.refY.renderingIntent.repeatCount.repeatDur.requiredExtensions.requiredFeatures.restart.result.rotate.rx.ry.seed.shapeRendering.slope.spacing.specularConstant.specularExponent.speed.spreadMethod.startOffset.stdDeviation.stemh.stemv.stitchTiles.stopColor.stopOpacity.strikethroughPosition.strikethroughThickness.string.stroke.strokeDasharray.strokeDashoffset.strokeLinecap.strokeLinejoin.strokeMiterlimit.strokeOpacity.strokeWidth.surfaceScale.systemLanguage.tableValues.targetX.targetY.textAnchor.textDecoration.textLength.textRendering.to.transform.u1.u2.underlinePosition.underlineThickness.unicode.unicodeBidi.unicodeRange.unitsPerEm.vAlphabetic.values.vectorEffect.version.vertAdvY.vertOriginX.vertOriginY.vHanging.vIdeographic.viewTarget.visibility.vMathematical.widths.wordSpacing.writingMode.x1.x2.x.xChannelSelector.xHeight.xlinkActuate.xlinkArcrole.xlinkHref.xlinkRole.xlinkShow.xlinkTitle.xlinkType.xmlBase.xmlLang.xmlns.xmlnsXlink.xmlSpace.y1.y2.y.yChannelSelector.z.zoomAndPan.ref.key.angle".split("."));
function Le(e) {
	return typeof e == "string" && Ie.has(e);
}
function Re(e) {
	return typeof e == "string" && e.startsWith("data-");
}
function ze(e) {
	if (typeof e != "object" || !e) return {};
	var t = {};
	for (var n in e) Object.prototype.hasOwnProperty.call(e, n) && (Le(n) || Re(n)) && (t[n] = e[n]);
	return t;
}
function Be(e) {
	if (e == null) return null;
	if (/*#__PURE__*/ (0, C.isValidElement)(e) && typeof e.props == "object" && e.props !== null) {
		var t = e.props;
		return ze(t);
	}
	return typeof e == "object" && !Array.isArray(e) ? ze(e) : null;
}
//#endregion
//#region node_modules/recharts/es6/util/svgPropertiesAndEvents.js
function Ve(e) {
	var t = {};
	for (var n in e) Object.prototype.hasOwnProperty.call(e, n) && (Le(n) || Re(n) || Fe(n)) && (t[n] = e[n]);
	return t;
}
//#endregion
//#region node_modules/recharts/es6/container/Surface.js
var He = [
	"children",
	"width",
	"height",
	"viewBox",
	"className",
	"style",
	"title",
	"desc"
];
function Ue() {
	return Ue = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, Ue.apply(null, arguments);
}
function We(e, t) {
	if (e == null) return {};
	var n, r, i = Ge(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function Ge(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var Ke = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.children, r = e.width, i = e.height, a = e.viewBox, o = e.className, s = e.style, c = e.title, l = e.desc, u = We(e, He), d = a || {
		width: r,
		height: i,
		x: 0,
		y: 0
	}, f = Ne("recharts-surface", o);
	return /*#__PURE__*/ C.createElement("svg", Ue({}, Ve(u), {
		className: f,
		width: r,
		height: i,
		style: s,
		viewBox: `${d.x} ${d.y} ${d.width} ${d.height}`,
		ref: t
	}), /*#__PURE__*/ C.createElement("title", null, c), /*#__PURE__*/ C.createElement("desc", null, l), n);
}), qe = ["children", "className"];
function Je() {
	return Je = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, Je.apply(null, arguments);
}
function Ye(e, t) {
	if (e == null) return {};
	var n, r, i = Xe(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function Xe(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var Ze = /*#__PURE__*/ C.forwardRef((e, t) => {
	var n = e.children, r = e.className, i = Ye(e, qe), a = Ne("recharts-layer", r);
	return /*#__PURE__*/ C.createElement("g", Je({ className: a }, Ve(i), { ref: t }), n);
}), Qe = /*#__PURE__*/ (0, C.createContext)(null);
//#endregion
//#region node_modules/d3-shape/src/constant.js
function $e(e) {
	return function() {
		return e;
	};
}
//#endregion
//#region node_modules/d3-path/src/path.js
var et = Math.PI, tt = 2 * et, nt = 1e-6, rt = tt - nt;
function it(e) {
	this._ += e[0];
	for (let t = 1, n = e.length; t < n; ++t) this._ += arguments[t] + e[t];
}
function at(e) {
	let t = Math.floor(e);
	if (!(t >= 0)) throw Error(`invalid digits: ${e}`);
	if (t > 15) return it;
	let n = 10 ** t;
	return function(e) {
		this._ += e[0];
		for (let t = 1, r = e.length; t < r; ++t) this._ += Math.round(arguments[t] * n) / n + e[t];
	};
}
var ot = class {
	constructor(e) {
		this._x0 = this._y0 = this._x1 = this._y1 = null, this._ = "", this._append = e == null ? it : at(e);
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
		else if (d > nt) if (!(Math.abs(u * s - c * l) > nt) || !i) this._append`L${this._x1 = e},${this._y1 = t}`;
		else {
			let f = n - a, p = r - o, m = s * s + c * c, h = f * f + p * p, g = Math.sqrt(m), _ = Math.sqrt(d), v = i * Math.tan((et - Math.acos((m + d - h) / (2 * g * _))) / 2), y = v / _, b = v / g;
			Math.abs(y - 1) > nt && this._append`L${e + y * l},${t + y * u}`, this._append`A${i},${i},0,0,${+(u * f > l * p)},${this._x1 = e + b * s},${this._y1 = t + b * c}`;
		}
	}
	arc(e, t, n, r, i, a) {
		if (e = +e, t = +t, n = +n, a = !!a, n < 0) throw Error(`negative radius: ${n}`);
		let o = n * Math.cos(r), s = n * Math.sin(r), c = e + o, l = t + s, u = 1 ^ a, d = a ? r - i : i - r;
		this._x1 === null ? this._append`M${c},${l}` : (Math.abs(this._x1 - c) > nt || Math.abs(this._y1 - l) > nt) && this._append`L${c},${l}`, n && (d < 0 && (d = d % tt + tt), d > rt ? this._append`A${n},${n},0,1,${u},${e - o},${t - s}A${n},${n},0,1,${u},${this._x1 = c},${this._y1 = l}` : d > nt && this._append`A${n},${n},0,${+(d >= et)},${u},${this._x1 = e + n * Math.cos(i)},${this._y1 = t + n * Math.sin(i)}`);
	}
	rect(e, t, n, r) {
		this._append`M${this._x0 = this._x1 = +e},${this._y0 = this._y1 = +t}h${n = +n}v${+r}h${-n}Z`;
	}
	toString() {
		return this._;
	}
};
function st() {
	return new ot();
}
st.prototype = ot.prototype;
//#endregion
//#region node_modules/d3-shape/src/path.js
function ct(e) {
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
	}, () => new ot(t);
}
Array.prototype.slice;
function lt(e) {
	return typeof e == "object" && "length" in e ? e : Array.from(e);
}
//#endregion
//#region node_modules/d3-shape/src/curve/linear.js
function ut(e) {
	this._context = e;
}
ut.prototype = {
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
function dt(e) {
	return new ut(e);
}
//#endregion
//#region node_modules/d3-shape/src/point.js
function ft(e) {
	return e[0];
}
function pt(e) {
	return e[1];
}
//#endregion
//#region node_modules/d3-shape/src/line.js
function mt(e, t) {
	var n = $e(!0), r = null, i = dt, a = null, o = ct(s);
	e = typeof e == "function" ? e : e === void 0 ? ft : $e(e), t = typeof t == "function" ? t : t === void 0 ? pt : $e(t);
	function s(s) {
		var c, l = (s = lt(s)).length, u, d = !1, f;
		for (r == null && (a = i(f = o())), c = 0; c <= l; ++c) !(c < l && n(u = s[c], c, s)) === d && ((d = !d) ? a.lineStart() : a.lineEnd()), d && a.point(+e(u, c, s), +t(u, c, s));
		if (f) return a = null, f + "" || null;
	}
	return s.x = function(t) {
		return arguments.length ? (e = typeof t == "function" ? t : $e(+t), s) : e;
	}, s.y = function(e) {
		return arguments.length ? (t = typeof e == "function" ? e : $e(+e), s) : t;
	}, s.defined = function(e) {
		return arguments.length ? (n = typeof e == "function" ? e : $e(!!e), s) : n;
	}, s.curve = function(e) {
		return arguments.length ? (i = e, r != null && (a = i(r)), s) : i;
	}, s.context = function(e) {
		return arguments.length ? (e == null ? r = a = null : a = i(r = e), s) : r;
	}, s;
}
//#endregion
//#region node_modules/d3-shape/src/area.js
function ht(e, t, n) {
	var r = null, i = $e(!0), a = null, o = dt, s = null, c = ct(l);
	e = typeof e == "function" ? e : e === void 0 ? ft : $e(+e), t = typeof t == "function" ? t : $e(t === void 0 ? 0 : +t), n = typeof n == "function" ? n : n === void 0 ? pt : $e(+n);
	function l(l) {
		var u, d, f, p = (l = lt(l)).length, m, h = !1, g, _ = Array(p), v = Array(p);
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
		return mt().defined(i).curve(o).context(a);
	}
	return l.x = function(t) {
		return arguments.length ? (e = typeof t == "function" ? t : $e(+t), r = null, l) : e;
	}, l.x0 = function(t) {
		return arguments.length ? (e = typeof t == "function" ? t : $e(+t), l) : e;
	}, l.x1 = function(e) {
		return arguments.length ? (r = e == null ? null : typeof e == "function" ? e : $e(+e), l) : r;
	}, l.y = function(e) {
		return arguments.length ? (t = typeof e == "function" ? e : $e(+e), n = null, l) : t;
	}, l.y0 = function(e) {
		return arguments.length ? (t = typeof e == "function" ? e : $e(+e), l) : t;
	}, l.y1 = function(e) {
		return arguments.length ? (n = e == null ? null : typeof e == "function" ? e : $e(+e), l) : n;
	}, l.lineX0 = l.lineY0 = function() {
		return u().x(e).y(t);
	}, l.lineY1 = function() {
		return u().x(e).y(n);
	}, l.lineX1 = function() {
		return u().x(r).y(t);
	}, l.defined = function(e) {
		return arguments.length ? (i = typeof e == "function" ? e : $e(!!e), l) : i;
	}, l.curve = function(e) {
		return arguments.length ? (o = e, a != null && (s = o(a)), l) : o;
	}, l.context = function(e) {
		return arguments.length ? (e == null ? a = s = null : s = o(a = e), l) : a;
	}, l;
}
//#endregion
//#region node_modules/d3-shape/src/curve/bump.js
var gt = class {
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
function _t(e) {
	return new gt(e, !0);
}
function vt(e) {
	return new gt(e, !1);
}
//#endregion
//#region node_modules/d3-shape/src/noop.js
function yt() {}
//#endregion
//#region node_modules/d3-shape/src/curve/basis.js
function bt(e, t, n) {
	e._context.bezierCurveTo((2 * e._x0 + e._x1) / 3, (2 * e._y0 + e._y1) / 3, (e._x0 + 2 * e._x1) / 3, (e._y0 + 2 * e._y1) / 3, (e._x0 + 4 * e._x1 + t) / 6, (e._y0 + 4 * e._y1 + n) / 6);
}
function xt(e) {
	this._context = e;
}
xt.prototype = {
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
			case 3: bt(this, this._x1, this._y1);
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
				bt(this, e, t);
				break;
		}
		this._x0 = this._x1, this._x1 = e, this._y0 = this._y1, this._y1 = t;
	}
};
function St(e) {
	return new xt(e);
}
//#endregion
//#region node_modules/d3-shape/src/curve/basisClosed.js
function Ct(e) {
	this._context = e;
}
Ct.prototype = {
	areaStart: yt,
	areaEnd: yt,
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
				bt(this, e, t);
				break;
		}
		this._x0 = this._x1, this._x1 = e, this._y0 = this._y1, this._y1 = t;
	}
};
function wt(e) {
	return new Ct(e);
}
//#endregion
//#region node_modules/d3-shape/src/curve/basisOpen.js
function Tt(e) {
	this._context = e;
}
Tt.prototype = {
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
				bt(this, e, t);
				break;
		}
		this._x0 = this._x1, this._x1 = e, this._y0 = this._y1, this._y1 = t;
	}
};
function Et(e) {
	return new Tt(e);
}
//#endregion
//#region node_modules/d3-shape/src/curve/linearClosed.js
function Dt(e) {
	this._context = e;
}
Dt.prototype = {
	areaStart: yt,
	areaEnd: yt,
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
function Ot(e) {
	return new Dt(e);
}
//#endregion
//#region node_modules/d3-shape/src/curve/monotone.js
function kt(e) {
	return e < 0 ? -1 : 1;
}
function At(e, t, n) {
	var r = e._x1 - e._x0, i = t - e._x1, a = (e._y1 - e._y0) / (r || i < 0 && -0), o = (n - e._y1) / (i || r < 0 && -0), s = (a * i + o * r) / (r + i);
	return (kt(a) + kt(o)) * Math.min(Math.abs(a), Math.abs(o), .5 * Math.abs(s)) || 0;
}
function jt(e, t) {
	var n = e._x1 - e._x0;
	return n ? (3 * (e._y1 - e._y0) / n - t) / 2 : t;
}
function Mt(e, t, n) {
	var r = e._x0, i = e._y0, a = e._x1, o = e._y1, s = (a - r) / 3;
	e._context.bezierCurveTo(r + s, i + s * t, a - s, o - s * n, a, o);
}
function Nt(e) {
	this._context = e;
}
Nt.prototype = {
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
				Mt(this, this._t0, jt(this, this._t0));
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
					this._point = 3, Mt(this, jt(this, n = At(this, e, t)), n);
					break;
				default:
					Mt(this, this._t0, n = At(this, e, t));
					break;
			}
			this._x0 = this._x1, this._x1 = e, this._y0 = this._y1, this._y1 = t, this._t0 = n;
		}
	}
};
function Pt(e) {
	this._context = new Ft(e);
}
(Pt.prototype = Object.create(Nt.prototype)).point = function(e, t) {
	Nt.prototype.point.call(this, t, e);
};
function Ft(e) {
	this._context = e;
}
Ft.prototype = {
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
function It(e) {
	return new Nt(e);
}
function Lt(e) {
	return new Pt(e);
}
//#endregion
//#region node_modules/d3-shape/src/curve/natural.js
function Rt(e) {
	this._context = e;
}
Rt.prototype = {
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
		else for (var r = zt(e), i = zt(t), a = 0, o = 1; o < n; ++a, ++o) this._context.bezierCurveTo(r[0][a], i[0][a], r[1][a], i[1][a], e[o], t[o]);
		(this._line || this._line !== 0 && n === 1) && this._context.closePath(), this._line = 1 - this._line, this._x = this._y = null;
	},
	point: function(e, t) {
		this._x.push(+e), this._y.push(+t);
	}
};
function zt(e) {
	var t, n = e.length - 1, r, i = Array(n), a = Array(n), o = Array(n);
	for (i[0] = 0, a[0] = 2, o[0] = e[0] + 2 * e[1], t = 1; t < n - 1; ++t) i[t] = 1, a[t] = 4, o[t] = 4 * e[t] + 2 * e[t + 1];
	for (i[n - 1] = 2, a[n - 1] = 7, o[n - 1] = 8 * e[n - 1] + e[n], t = 1; t < n; ++t) r = i[t] / a[t - 1], a[t] -= r, o[t] -= r * o[t - 1];
	for (i[n - 1] = o[n - 1] / a[n - 1], t = n - 2; t >= 0; --t) i[t] = (o[t] - i[t + 1]) / a[t];
	for (a[n - 1] = (e[n] + i[n - 1]) / 2, t = 0; t < n - 1; ++t) a[t] = 2 * e[t + 1] - i[t + 1];
	return [i, a];
}
function Bt(e) {
	return new Rt(e);
}
//#endregion
//#region node_modules/d3-shape/src/curve/step.js
function Vt(e, t) {
	this._context = e, this._t = t;
}
Vt.prototype = {
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
function Ht(e) {
	return new Vt(e, .5);
}
function Ut(e) {
	return new Vt(e, 0);
}
function Wt(e) {
	return new Vt(e, 1);
}
//#endregion
//#region node_modules/d3-shape/src/offset/none.js
function Gt(e, t) {
	if ((o = e.length) > 1) for (var n = 1, r, i, a = e[t[0]], o, s = a.length; n < o; ++n) for (i = a, a = e[t[n]], r = 0; r < s; ++r) a[r][1] += a[r][0] = isNaN(i[r][1]) ? i[r][0] : i[r][1];
}
//#endregion
//#region node_modules/d3-shape/src/order/none.js
function I(e) {
	for (var t = e.length, n = Array(t); --t >= 0;) n[t] = t;
	return n;
}
//#endregion
//#region node_modules/d3-shape/src/stack.js
function Kt(e, t) {
	return e[t];
}
function qt(e) {
	let t = [];
	return t.key = e, t;
}
function Jt() {
	var e = $e([]), t = I, n = Gt, r = Kt;
	function i(i) {
		var a = Array.from(e.apply(this, arguments), qt), o, s = a.length, c = -1, l;
		for (let e of i) for (o = 0, ++c; o < s; ++o) (a[o][c] = [0, +r(e, a[o].key, c, i)]).data = e;
		for (o = 0, l = lt(t(a)); o < s; ++o) a[l[o]].index = o;
		return n(a, l), a;
	}
	return i.keys = function(t) {
		return arguments.length ? (e = typeof t == "function" ? t : $e(Array.from(t)), i) : e;
	}, i.value = function(e) {
		return arguments.length ? (r = typeof e == "function" ? e : $e(+e), i) : r;
	}, i.order = function(e) {
		return arguments.length ? (t = e == null ? I : typeof e == "function" ? e : $e(Array.from(e)), i) : t;
	}, i.offset = function(e) {
		return arguments.length ? (n = e == null ? Gt : e, i) : n;
	}, i;
}
//#endregion
//#region node_modules/d3-shape/src/offset/expand.js
function Yt(e, t) {
	if ((r = e.length) > 0) {
		for (var n, r, i = 0, a = e[0].length, o; i < a; ++i) {
			for (o = n = 0; n < r; ++n) o += e[n][i][1] || 0;
			if (o) for (n = 0; n < r; ++n) e[n][i][1] /= o;
		}
		Gt(e, t);
	}
}
//#endregion
//#region node_modules/d3-shape/src/offset/silhouette.js
function Xt(e, t) {
	if ((i = e.length) > 0) {
		for (var n = 0, r = e[t[0]], i, a = r.length; n < a; ++n) {
			for (var o = 0, s = 0; o < i; ++o) s += e[o][n][1] || 0;
			r[n][1] += r[n][0] = -s / 2;
		}
		Gt(e, t);
	}
}
//#endregion
//#region node_modules/d3-shape/src/offset/wiggle.js
function Zt(e, t) {
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
		i[r - 1][1] += i[r - 1][0] = n, Gt(e, t);
	}
}
//#endregion
//#region node_modules/es-toolkit/dist/_internal/isUnsafeProperty.mjs
function Qt(e) {
	return e === "__proto__";
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/isDeepKey.mjs
function $t(e) {
	switch (typeof e) {
		case "number":
		case "symbol": return !1;
		case "string": return e.includes(".") || e.includes("[") || e.includes("]");
	}
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/toKey.mjs
function en(e) {
	var t;
	return typeof e == "string" || typeof e == "symbol" ? e : Object.is(e == null || (t = e.valueOf) == null ? void 0 : t.call(e), -0) ? "-0" : String(e);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/util/toString.mjs
function tn(e) {
	if (e == null) return "";
	if (typeof e == "string") return e;
	if (Array.isArray(e)) return e.map(tn).join(",");
	let t = String(e);
	return t === "0" && Object.is(Number(e), -0) ? "-0" : t;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/util/toPath.mjs
function nn(e) {
	if (Array.isArray(e)) return e.map(en);
	if (typeof e == "symbol") return [e];
	e = tn(e);
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
function rn(e, t, n) {
	if (e == null) return n;
	switch (typeof t) {
		case "string": {
			if (Qt(t)) return n;
			let r = e[t];
			return r === void 0 ? $t(t) && !Object.hasOwn(e, t) ? rn(e, nn(t), n) : n : r;
		}
		case "number":
		case "symbol": {
			typeof t == "number" && (t = en(t));
			let r = e[t];
			return r === void 0 ? n : r;
		}
		default: {
			if (Array.isArray(t)) return an(e, t, n);
			if (t = Object.is(t == null ? void 0 : t.valueOf(), -0) ? "-0" : String(t), Qt(t)) return n;
			let r = e[t];
			return r === void 0 ? n : r;
		}
	}
}
function an(e, t, n) {
	if (t.length === 0) return n;
	let r = e;
	for (let e = 0; e < t.length; e++) {
		if (r == null || Qt(t[e])) return n;
		r = r[t[e]];
	}
	return r === void 0 ? n : r;
}
//#endregion
//#region node_modules/recharts/es6/util/round.js
var on = 4;
function sn(e) {
	var t = 10 ** (arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : on), n = Math.round(e * t) / t;
	return Object.is(n, -0) ? 0 : n;
}
function cn(e) {
	var t = [...arguments].slice(1);
	return e.reduce((e, n, r) => {
		var i = t[r - 1];
		return typeof i == "string" ? e + i + n : i === void 0 ? e + n : e + sn(i) + n;
	}, "");
}
//#endregion
//#region node_modules/recharts/es6/util/DataUtils.js
var ln = (e) => e === 0 ? 0 : e > 0 ? 1 : -1, un = (e) => typeof e == "number" && e != +e, dn = (e) => typeof e == "string" && e.length > 1 && e.indexOf("%") === e.length - 1, L = (e) => (typeof e == "number" || e instanceof Number) && !un(e), fn = (e) => L(e) || typeof e == "string", pn = 0, mn = (e) => {
	var t = ++pn;
	return `${e || ""}${t}`;
}, hn = function(e, t) {
	var n = arguments.length > 2 && arguments[2] !== void 0 ? arguments[2] : 0, r = arguments.length > 3 && arguments[3] !== void 0 && arguments[3];
	if (!L(e) && typeof e != "string") return n;
	var i;
	if (dn(e)) {
		if (t == null) return n;
		var a = e.indexOf("%");
		i = t * parseFloat(e.slice(0, a)) / 100;
	} else i = +e;
	return un(i) && (i = n), r && t != null && i > t && (i = t), i;
}, gn = (e) => {
	if (!Array.isArray(e)) return !1;
	for (var t = e.length, n = {}, r = 0; r < t; r++) if (!n[String(e[r])]) n[String(e[r])] = !0;
	else return !0;
	return !1;
};
function _n(e, t, n) {
	return L(e) && L(t) ? sn(e + n * (t - e)) : t;
}
function vn(e, t, n) {
	if (!(!e || !e.length)) return e.find((e) => e && (typeof t == "function" ? t(e) : rn(e, t)) === n);
}
var yn = (e) => e == null, bn = (e) => yn(e) ? e : `${e.charAt(0).toUpperCase()}${e.slice(1)}`;
function xn(e) {
	return e != null;
}
function Sn() {}
//#endregion
//#region node_modules/recharts/es6/util/types.js
var Cn = (e) => "radius" in e && "startAngle" in e && "endAngle" in e, wn = (e, t) => {
	if (!e || typeof e == "function" || typeof e == "boolean") return null;
	var n = e;
	if (/*#__PURE__*/ (0, C.isValidElement)(e) && (n = e.props), typeof n != "object" && typeof n != "function") return null;
	var r = {};
	return Object.keys(n).forEach((e) => {
		Fe(e) && typeof n[e] == "function" && (r[e] = t || ((t) => n[e](n, t)));
	}), r;
}, Tn = (e, t, n) => (r) => (e(t, n, r), null), En = (e, t, n) => {
	if (e === null || typeof e != "object" && typeof e != "function") return null;
	var r = null;
	return Object.keys(e).forEach((i) => {
		var a = e[i];
		Fe(i) && typeof a == "function" && (r || (r = {}), r[i] = Tn(a, t, n));
	}), r;
};
//#endregion
//#region node_modules/recharts/es6/util/resolveDefaultProps.js
function Dn(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function On(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Dn(Object(n), !0).forEach(function(t) {
			kn(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Dn(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function kn(e, t, n) {
	return (t = An(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function An(e) {
	var t = jn(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function jn(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function Mn(e, t) {
	var n = On({}, e), r = t;
	return Object.keys(t).reduce((e, t) => (e[t] === void 0 && r[t] !== void 0 && (e[t] = r[t]), e), n);
}
//#endregion
//#region node_modules/es-toolkit/dist/array/uniqBy.mjs
function Nn(e, t) {
	let n = /* @__PURE__ */ new Map();
	for (let r = 0; r < e.length; r++) {
		let i = e[r], a = t(i, r, e);
		n.has(a) || n.set(a, i);
	}
	return Array.from(n.values());
}
//#endregion
//#region node_modules/es-toolkit/dist/function/ary.mjs
function Pn(e, t) {
	return function(...n) {
		return e.apply(this, n.slice(0, t));
	};
}
//#endregion
//#region node_modules/es-toolkit/dist/function/identity.mjs
function Fn(e) {
	return e;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/object/property.mjs
function In(e) {
	return function(t) {
		return rn(t, e);
	};
}
//#endregion
//#region node_modules/es-toolkit/dist/predicate/isPrimitive.mjs
function Ln(e) {
	return e == null || typeof e != "object" && typeof e != "function";
}
//#endregion
//#region node_modules/es-toolkit/dist/predicate/isTypedArray.mjs
function Rn(e) {
	return ArrayBuffer.isView(e) && !(e instanceof DataView);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/getSymbols.mjs
function zn(e) {
	return Object.getOwnPropertySymbols(e).filter((t) => Object.prototype.propertyIsEnumerable.call(e, t));
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/getTag.mjs
function Bn(e) {
	return e == null ? e === void 0 ? "[object Undefined]" : "[object Null]" : Object.prototype.toString.call(e);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/tags.mjs
var Vn = "[object RegExp]", Hn = "[object String]", Un = "[object Number]", Wn = "[object Boolean]", Gn = "[object Arguments]", Kn = "[object Symbol]", qn = "[object Date]", Jn = "[object Map]", Yn = "[object Set]", Xn = "[object Array]", Zn = "[object ArrayBuffer]", Qn = "[object Object]", $n = "[object DataView]", er = "[object Uint8Array]", tr = "[object Uint8ClampedArray]", nr = "[object Uint16Array]", rr = "[object Uint32Array]", ir = "[object Int8Array]", ar = "[object Int16Array]", or = "[object Int32Array]", sr = "[object Float32Array]", cr = "[object Float64Array]", lr = typeof globalThis == "object" && globalThis || typeof window == "object" && window || typeof self == "object" && self || typeof global == "object" && global || (function() {
	return this;
})();
//#endregion
//#region node_modules/es-toolkit/dist/predicate/isBuffer.mjs
function ur(e) {
	return lr.Buffer !== void 0 && lr.Buffer.isBuffer(e);
}
//#endregion
//#region node_modules/es-toolkit/dist/object/cloneDeepWith.mjs
function dr(e, t) {
	return fr(e, void 0, e, /* @__PURE__ */ new Map(), t);
}
function fr(e, t, n, r = /* @__PURE__ */ new Map(), i = void 0) {
	let a = i == null ? void 0 : i(e, t, n, r);
	if (a !== void 0) return a;
	if (Ln(e)) return e;
	if (r.has(e)) return r.get(e);
	if (Array.isArray(e)) {
		let t = Array(e.length);
		r.set(e, t);
		for (let a = 0; a < e.length; a++) t[a] = fr(e[a], a, n, r, i);
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
		for (let [a, o] of e) t.set(a, fr(o, a, n, r, i));
		return t;
	}
	if (e instanceof Set) {
		let t = /* @__PURE__ */ new Set();
		r.set(e, t);
		for (let a of e) t.add(fr(a, void 0, n, r, i));
		return t;
	}
	if (ur(e)) return e.subarray();
	if (Rn(e)) {
		let t = new (Object.getPrototypeOf(e)).constructor(e.length);
		r.set(e, t);
		for (let a = 0; a < e.length; a++) t[a] = fr(e[a], a, n, r, i);
		return t;
	}
	if (e instanceof ArrayBuffer || typeof SharedArrayBuffer < "u" && e instanceof SharedArrayBuffer) return e.slice(0);
	if (e instanceof DataView) {
		let t = new DataView(e.buffer.slice(0), e.byteOffset, e.byteLength);
		return r.set(e, t), pr(t, e, n, r, i), t;
	}
	if (typeof File < "u" && e instanceof File) {
		let t = new File([e], e.name, { type: e.type });
		return r.set(e, t), pr(t, e, n, r, i), t;
	}
	if (typeof Blob < "u" && e instanceof Blob) {
		let t = new Blob([e], { type: e.type });
		return r.set(e, t), pr(t, e, n, r, i), t;
	}
	if (e instanceof Error) {
		let t = structuredClone(e);
		return r.set(e, t), t.message = e.message, t.name = e.name, t.stack = e.stack, t.cause = e.cause, t.constructor = e.constructor, pr(t, e, n, r, i), t;
	}
	if (e instanceof Boolean) {
		let t = new Boolean(e.valueOf());
		return r.set(e, t), pr(t, e, n, r, i), t;
	}
	if (e instanceof Number) {
		let t = new Number(e.valueOf());
		return r.set(e, t), pr(t, e, n, r, i), t;
	}
	if (e instanceof String) {
		let t = new String(e.valueOf());
		return r.set(e, t), pr(t, e, n, r, i), t;
	}
	if (typeof e == "object" && mr(e)) {
		let t = Object.create(Object.getPrototypeOf(e));
		return r.set(e, t), pr(t, e, n, r, i), t;
	}
	return e;
}
function pr(e, t, n = e, r, i) {
	let a = [...Object.keys(t), ...zn(t)];
	for (let o = 0; o < a.length; o++) {
		let s = a[o], c = Object.getOwnPropertyDescriptor(e, s);
		(c == null || c.writable) && (e[s] = fr(t[s], s, n, r, i));
	}
}
function mr(e) {
	switch (Bn(e)) {
		case Gn:
		case Xn:
		case Zn:
		case $n:
		case Wn:
		case qn:
		case sr:
		case cr:
		case ir:
		case ar:
		case or:
		case Jn:
		case Un:
		case Qn:
		case Vn:
		case Yn:
		case Hn:
		case Kn:
		case er:
		case tr:
		case nr:
		case rr: return !0;
		default: return !1;
	}
}
//#endregion
//#region node_modules/es-toolkit/dist/object/cloneDeep.mjs
function hr(e) {
	return fr(e, void 0, e, /* @__PURE__ */ new Map(), void 0);
}
//#endregion
//#region node_modules/es-toolkit/dist/_internal/isEqualsSameValueZero.mjs
function gr(e, t) {
	return e === t || Number.isNaN(e) && Number.isNaN(t);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isObject.mjs
function _r(e) {
	return e !== null && (typeof e == "object" || typeof e == "function");
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isMatchWith.mjs
function vr(e, t, n) {
	return typeof n == "function" ? yr(e, t, function e(t, r, i, a, o, s) {
		let c = n(t, r, i, a, o, s);
		return c === void 0 ? yr(t, r, e, s, !1) : !!c;
	}, /* @__PURE__ */ new Map(), !0) : vr(e, t, () => void 0);
}
function yr(e, t, n, r, i = !1) {
	if (t === e) return !0;
	switch (typeof t) {
		case "object": return br(e, t, n, r);
		case "function": return Object.keys(t).length > 0 ? yr(e, { ...t }, n, r, i) : gr(e, t);
		default: return _r(e) && i ? typeof t != "string" || t === "" : gr(e, t);
	}
}
function br(e, t, n, r) {
	if (t == null) return !0;
	if (Array.isArray(t)) return Sr(e, t, n, r);
	if (t instanceof Map) return xr(e, t, n, r);
	if (t instanceof Set) return Cr(e, t, n, r);
	let i = Object.keys(t);
	if (e == null || Ln(e)) return i.length === 0;
	if (i.length === 0) return !0;
	if (r != null && r.has(t)) return r.get(t) === e;
	r == null || r.set(t, e);
	try {
		for (let a = 0; a < i.length; a++) {
			let o = i[a];
			if (!Ln(e) && !(o in e) || t[o] === void 0 && e[o] !== void 0 || t[o] === null && e[o] !== null || !n(e[o], t[o], o, e, t, r)) return !1;
		}
		return !0;
	} finally {
		r == null || r.delete(t);
	}
}
function xr(e, t, n, r) {
	if (t.size === 0) return !0;
	if (!(e instanceof Map)) return !1;
	for (let [i, a] of t.entries()) if (n(e.get(i), a, i, e, t, r) === !1) return !1;
	return !0;
}
function Sr(e, t, n, r) {
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
function Cr(e, t, n, r) {
	return t.size === 0 || e instanceof Set && Sr([...e], [...t], n, r);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isMatch.mjs
function wr(e, t) {
	return vr(e, t, () => void 0);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/matches.mjs
function Tr(e) {
	return e = hr(e), (t) => wr(t, e);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/object/cloneDeepWith.mjs
function Er(e, t) {
	return dr(e, (n, r, i, a) => {
		let o = t == null ? void 0 : t(n, r, i, a);
		if (o !== void 0) return o;
		if (typeof e == "object") {
			if (Bn(e) === "[object Object]" && typeof e.constructor != "function") {
				let t = {};
				return a.set(e, t), pr(t, e, i, a), t;
			}
			switch (Object.prototype.toString.call(e)) {
				case Un:
				case Hn:
				case Wn: {
					let t = new e.constructor(e == null ? void 0 : e.valueOf());
					return pr(t, e), t;
				}
				case Gn: {
					let t = {};
					return pr(t, e), t.length = e.length, t[Symbol.iterator] = e[Symbol.iterator], t;
				}
				default: return;
			}
		}
	});
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/object/cloneDeep.mjs
function Dr(e) {
	return Er(e);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/isIndex.mjs
var Or = /^(?:0|[1-9]\d*)$/;
function kr(e, t = 2 ** 53 - 1) {
	switch (typeof e) {
		case "number": return Number.isInteger(e) && e >= 0 && e < t;
		case "symbol": return !1;
		case "string": return Or.test(e);
	}
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isArguments.mjs
function Ar(e) {
	return typeof e == "object" && !!e && Bn(e) === "[object Arguments]";
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/object/has.mjs
function jr(e, t) {
	let n;
	if (n = Array.isArray(t) ? t : typeof t == "string" && $t(t) && (e == null ? void 0 : e[t]) == null ? nn(t) : [t], n.length === 0) return !1;
	let r = e;
	for (let e = 0; e < n.length; e++) {
		let t = n[e];
		if ((r == null || !Object.hasOwn(r, t)) && !((Array.isArray(r) || Ar(r)) && kr(t) && t < r.length)) return !1;
		r = r[t];
	}
	return !0;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/matchesProperty.mjs
function Mr(e, t) {
	switch (typeof e) {
		case "object":
			Object.is(e == null ? void 0 : e.valueOf(), -0) && (e = "-0");
			break;
		case "number":
			e = en(e);
			break;
	}
	return t = Dr(t), function(n) {
		let r = rn(n, e);
		return r === void 0 ? jr(n, e) : t === void 0 ? r === void 0 : wr(r, t);
	};
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/util/iteratee.mjs
function Nr(e) {
	if (e == null) return Fn;
	switch (typeof e) {
		case "function": return e;
		case "object": return Array.isArray(e) && e.length === 2 ? Mr(e[0], e[1]) : Tr(e);
		case "string":
		case "symbol":
		case "number": return In(e);
	}
}
//#endregion
//#region node_modules/es-toolkit/dist/predicate/isLength.mjs
function Pr(e) {
	return Number.isSafeInteger(e) && e >= 0;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isArrayLike.mjs
function Fr(e) {
	return e != null && typeof e != "function" && Pr(e.length);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isObjectLike.mjs
function Ir(e) {
	return typeof e == "object" && !!e;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isArrayLikeObject.mjs
function Lr(e) {
	return Ir(e) && Fr(e);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/array/uniqBy.mjs
function Rr(e, t = Fn) {
	return Lr(e) ? Nn(Array.from(e), Pn(Nr(t), 1)) : [];
}
//#endregion
//#region node_modules/recharts/es6/util/payload/getUniqPayload.js
function zr(e, t, n) {
	return t === !0 ? Rr(e, n) : typeof t == "function" ? Rr(e, t) : e;
}
//#endregion
//#region node_modules/use-sync-external-store/cjs/use-sync-external-store-shim.production.js
var Br = /* @__PURE__ */ o(((e) => {
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
})), Vr = /* @__PURE__ */ o(((e, t) => {
	t.exports = Br();
})), Hr = /* @__PURE__ */ o(((e) => {
	var t = d(), n = Vr();
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
})), Ur = /* @__PURE__ */ o(((e, t) => {
	t.exports = Hr();
})), Wr = /*#__PURE__*/ (0, C.createContext)(null), Gr = Ur(), Kr = (e) => e, qr = () => {
	var e = (0, C.useContext)(Wr);
	return e ? e.store.dispatch : Kr;
}, Jr = () => {}, Yr = () => Jr, Xr = (e, t) => e === t;
function R(e) {
	var t = (0, C.useContext)(Wr), n = (0, C.useMemo)(() => t ? (t) => {
		if (t != null) return e(t);
	} : Jr, [t, e]);
	return (0, Gr.useSyncExternalStoreWithSelector)(t ? t.subscription.addNestedSub : Yr, t ? t.store.getState : Jr, t ? t.store.getState : Jr, n, Xr);
}
//#endregion
//#region \0@oxc-project+runtime@0.139.0/helpers/esm/typeof.js
function Zr(e) {
	"@babel/helpers - typeof";
	return Zr = typeof Symbol == "function" && typeof Symbol.iterator == "symbol" ? function(e) {
		return typeof e;
	} : function(e) {
		return e && typeof Symbol == "function" && e.constructor === Symbol && e !== Symbol.prototype ? "symbol" : typeof e;
	}, Zr(e);
}
//#endregion
//#region \0@oxc-project+runtime@0.139.0/helpers/esm/toPrimitive.js
function Qr(e, t) {
	if (Zr(e) != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (Zr(r) != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
//#endregion
//#region \0@oxc-project+runtime@0.139.0/helpers/esm/toPropertyKey.js
function $r(e) {
	var t = Qr(e, "string");
	return Zr(t) == "symbol" ? t : t + "";
}
//#endregion
//#region \0@oxc-project+runtime@0.139.0/helpers/esm/defineProperty.js
function ei(e, t, n) {
	return (t = $r(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
//#endregion
//#region node_modules/reselect/dist/reselect.mjs
function ti(e, t = `expected a function, instead received ${typeof e}`) {
	if (typeof e != "function") throw TypeError(t);
}
function ni(e, t = "expected all items to be functions, instead received the following types: ") {
	if (!e.every((e) => typeof e == "function")) {
		let n = e.map((e) => typeof e == "function" ? `function ${e.name || "unnamed"}()` : typeof e).join(", ");
		throw TypeError(`${t}[${n}]`);
	}
}
var ri = (e) => Array.isArray(e) ? e : [e];
function ii(e) {
	let t = Array.isArray(e[0]) ? e[0] : e;
	return ni(t, "createSelector expects all input-selectors to be functions, but received the following types: "), t;
}
function ai(e, t) {
	let n = [], { length: r } = e;
	for (let i = 0; i < r; i++) n.push(e[i].apply(null, t));
	return n;
}
var oi = class {
	constructor(e) {
		this.value = e;
	}
	deref() {
		return this.value;
	}
}, si = typeof WeakRef > "u" ? oi : WeakRef, ci = 0, li = 1;
function ui() {
	return {
		s: ci,
		v: void 0,
		o: null,
		p: null
	};
}
function di(e) {
	return e instanceof si ? e.deref() : e;
}
function fi(e, t = {}) {
	let n = ui(), { resultEqualityCheck: r } = t, i, a = 0;
	function o() {
		let t = n, { length: o } = arguments;
		for (let e = 0, n = o; e < n; e++) {
			let n = arguments[e];
			if (typeof n == "function" || typeof n == "object" && n) {
				let e = t.o;
				e === null && (t.o = e = /* @__PURE__ */ new WeakMap());
				let r = e.get(n);
				r === void 0 ? (t = ui(), e.set(n, t)) : t = r;
			} else {
				let e = t.p;
				e === null && (t.p = e = /* @__PURE__ */ new Map());
				let r = e.get(n);
				r === void 0 ? (t = ui(), e.set(n, t)) : t = r;
			}
		}
		let s = t, c;
		if (t.s === li) c = t.v;
		else if (c = e.apply(null, arguments), a++, r) {
			let e = di(i);
			e != null && r(e, c) && (c = e, a !== 0 && a--), i = typeof c == "object" && c || typeof c == "function" ? /* @__PURE__ */ new si(c) : c;
		}
		return s.s = li, s.v = c, c;
	}
	return o.clearCache = () => {
		n = ui(), o.resetResultsCount();
	}, o.resultsCount = () => a, o.resetResultsCount = () => {
		a = 0;
	}, o;
}
function pi(e, ...t) {
	let n = typeof e == "function" ? {
		memoize: e,
		memoizeOptions: t
	} : e, r = (...e) => {
		let t = 0, r = 0, i, a = {}, o = e.pop();
		typeof o == "object" && (a = o, o = e.pop()), ti(o, `createSelector expects an output function after the inputs, but received: [${typeof o}]`);
		let { memoize: s, memoizeOptions: c = [], argsMemoize: l = fi, argsMemoizeOptions: u = [] } = {
			...n,
			...a
		}, d = ri(c), f = ri(u), p = ii(e), m = s(function() {
			return t++, o.apply(null, arguments);
		}, ...d), h = l(function() {
			r++;
			let e = ai(p, arguments);
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
var z = /* @__PURE__ */ pi(fi);
//#endregion
//#region node_modules/es-toolkit/dist/array/flatten.mjs
function mi(e, t = 1) {
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
function hi(e, t, n) {
	return _r(n) && (typeof t == "number" && Fr(n) && kr(t) && t < n.length || typeof t == "string" && t in n) ? gr(n[t], e) : !1;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/compareValues.mjs
function gi(e) {
	return typeof e == "symbol" ? 1 : e === null ? 2 : e === void 0 ? 3 : e === e ? 0 : 4;
}
var _i = (e, t, n) => {
	if (e !== t) {
		let r = gi(e), i = gi(t);
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
function vi(e) {
	return typeof e == "symbol" || e instanceof Symbol;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/isKey.mjs
var yi = /\.|\[(?:[^[\]]*|(["'])(?:(?!\1)[^\\]|\\.)*?\1)\]/, bi = /^\w*$/;
function xi(e, t) {
	return Array.isArray(e) ? !1 : typeof e == "number" || typeof e == "boolean" || e == null || vi(e) ? !0 : typeof e == "string" && (bi.test(e) || !yi.test(e)) || t != null && Object.hasOwn(t, e);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/array/orderBy.mjs
function Si(e, t, n, r) {
	if (e == null) return [];
	n = r ? void 0 : n, Array.isArray(e) || (e = Object.values(e)), Array.isArray(t) || (t = t == null ? [null] : [t]), t.length === 0 && (t = [null]), Array.isArray(n) || (n = n == null ? [] : [n]), n = n.map((e) => String(e));
	let i = (e, t) => {
		let n = e;
		for (let e = 0; e < t.length && n != null; ++e) n = n[t[e]];
		return n;
	}, a = (e, t) => t == null || e == null ? t : typeof e == "object" && "key" in e ? Object.hasOwn(t, e.key) ? t[e.key] : i(t, e.path) : typeof e == "function" ? e(t) : Array.isArray(e) ? i(t, e) : typeof t == "object" ? t[e] : t, o = t.map((e) => (Array.isArray(e) && e.length === 1 && (e = e[0]), e == null || typeof e == "function" || Array.isArray(e) || xi(e) ? e : {
		key: e,
		path: nn(e)
	}));
	return e.map((e) => ({
		original: e,
		criteria: o.map((t) => a(t, e))
	})).slice().sort((e, t) => {
		for (let r = 0; r < o.length; r++) {
			let i = _i(e.criteria[r], t.criteria[r], n[r]);
			if (i !== 0) return i;
		}
		return 0;
	}).map((e) => e.original);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/array/sortBy.mjs
function Ci(e, ...t) {
	let n = t.length;
	return n > 1 && hi(e, t[0], t[1]) ? t = [] : n > 2 && hi(t[0], t[1], t[2]) && (t = [t[0]]), Si(e, mi(t), ["asc"]);
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/legendSelectors.js
var wi = (e) => e.legend.settings, Ti = (e) => e.legend.size;
z([(e) => e.legend.payload, wi], (e, t) => {
	var n = t.itemSorter, r = e.flat(1);
	return n ? Ci(r, n) : r;
});
//#endregion
//#region node_modules/recharts/es6/util/useElementOffset.js
function Ei(e, t) {
	return ji(e) || Ai(e, t) || Oi(e, t) || Di();
}
function Di() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function Oi(e, t) {
	if (e) {
		if (typeof e == "string") return ki(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? ki(e, t) : void 0;
	}
}
function ki(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function Ai(e, t) {
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
function ji(e) {
	if (Array.isArray(e)) return e;
}
var Mi = 1;
function Ni(e, t) {
	return Math.abs(e.height - t.height) > Mi || Math.abs(e.left - t.left) > Mi || Math.abs(e.top - t.top) > Mi || Math.abs(e.width - t.width) > Mi;
}
function Pi(e) {
	var t = e.getBoundingClientRect();
	return {
		height: t.height,
		left: t.left,
		top: t.top,
		width: t.width
	};
}
function Fi() {
	var e = arguments.length > 0 && arguments[0] !== void 0 ? arguments[0] : [], t = Ei((0, C.useState)({
		height: 0,
		left: 0,
		top: 0,
		width: 0
	}), 2), n = t[0], r = t[1], i = (0, C.useRef)(null), a = (0, C.useRef)(n);
	a.current = n;
	var o = (0, C.useCallback)((e) => {
		if (i.current != null && (i.current.disconnect(), i.current = null), e != null) {
			var t = Pi(e);
			if (Ni(t, a.current) && r(t), typeof ResizeObserver < "u") {
				var n = new ResizeObserver(() => {
					var t = Pi(e);
					Ni(t, a.current) && r(t);
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
function Ii(e) {
	return `Minified Redux error #${e}; visit https://redux.js.org/Errors?code=${e} for the full message or use the non-minified dev environment for full errors. `;
}
var Li = typeof Symbol == "function" && Symbol.observable || "@@observable", Ri = () => Math.random().toString(36).substring(7).split("").join("."), zi = {
	INIT: `@@redux/INIT${/* @__PURE__ */ Ri()}`,
	REPLACE: `@@redux/REPLACE${/* @__PURE__ */ Ri()}`,
	PROBE_UNKNOWN_ACTION: () => `@@redux/PROBE_UNKNOWN_ACTION${Ri()}`
};
function Bi(e) {
	if (typeof e != "object" || !e) return !1;
	let t = e;
	for (; Object.getPrototypeOf(t) !== null;) t = Object.getPrototypeOf(t);
	return Object.getPrototypeOf(e) === t || Object.getPrototypeOf(e) === null;
}
function Vi(e, t, n) {
	if (typeof e != "function") throw Error(Ii(2));
	if (typeof t == "function" && typeof n == "function" || typeof n == "function" && typeof arguments[3] == "function") throw Error(Ii(0));
	if (typeof t == "function" && n === void 0 && (n = t, t = void 0), n !== void 0) {
		if (typeof n != "function") throw Error(Ii(1));
		return n(Vi)(e, t);
	}
	let r = e, i = t, a = /* @__PURE__ */ new Map(), o = a, s = 0, c = !1;
	function l() {
		o === a && (o = /* @__PURE__ */ new Map(), a.forEach((e, t) => {
			o.set(t, e);
		}));
	}
	function u() {
		if (c) throw Error(Ii(3));
		return i;
	}
	function d(e) {
		if (typeof e != "function") throw Error(Ii(4));
		if (c) throw Error(Ii(5));
		let t = !0;
		l();
		let n = s++;
		return o.set(n, e), function() {
			if (t) {
				if (c) throw Error(Ii(6));
				t = !1, l(), o.delete(n), a = null;
			}
		};
	}
	function f(e) {
		if (!Bi(e)) throw Error(Ii(7));
		if (e.type === void 0) throw Error(Ii(8));
		if (typeof e.type != "string") throw Error(Ii(17));
		if (c) throw Error(Ii(9));
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
		if (typeof e != "function") throw Error(Ii(10));
		r = e, f({ type: zi.REPLACE });
	}
	function m() {
		let e = d;
		return {
			subscribe(t) {
				if (typeof t != "object" || !t) throw Error(Ii(11));
				function n() {
					let e = t;
					e.next && e.next(u());
				}
				return n(), { unsubscribe: e(n) };
			},
			[Li]() {
				return this;
			}
		};
	}
	return f({ type: zi.INIT }), {
		dispatch: f,
		subscribe: d,
		getState: u,
		replaceReducer: p,
		[Li]: m
	};
}
function Hi(e) {
	Object.keys(e).forEach((t) => {
		let n = e[t];
		if (n(void 0, { type: zi.INIT }) === void 0) throw Error(Ii(12));
		if (n(void 0, { type: zi.PROBE_UNKNOWN_ACTION() }) === void 0) throw Error(Ii(13));
	});
}
function Ui(e) {
	let t = Object.keys(e), n = {};
	for (let r = 0; r < t.length; r++) {
		let i = t[r];
		typeof e[i] == "function" && (n[i] = e[i]);
	}
	let r = Object.keys(n), i;
	try {
		Hi(n);
	} catch (e) {
		i = e;
	}
	return function(e = {}, t) {
		if (i) throw i;
		let a = !1, o = {};
		for (let i = 0; i < r.length; i++) {
			let s = r[i], c = n[s], l = e[s], u = c(l, t);
			if (u === void 0) throw t && t.type, Error(Ii(14));
			o[s] = u, a = a || u !== l;
		}
		return a = a || r.length !== Object.keys(e).length, a ? o : e;
	};
}
function Wi(...e) {
	return e.length === 0 ? (e) => e : e.length === 1 ? e[0] : e.reduce((e, t) => (...n) => e(t(...n)));
}
function Gi(...e) {
	return (t) => (n, r) => {
		let i = t(n, r), a = () => {
			throw Error(Ii(15));
		}, o = {
			getState: i.getState,
			dispatch: (e, ...t) => a(e, ...t)
		};
		return a = Wi(...e.map((e) => e(o)))(i.dispatch), {
			...i,
			dispatch: a
		};
	};
}
function Ki(e) {
	return Bi(e) && "type" in e && typeof e.type == "string";
}
//#endregion
//#region node_modules/immer/dist/immer.mjs
var qi = Symbol.for("immer-nothing"), Ji = Symbol.for("immer-draftable"), B = Symbol.for("immer-state");
function V(e, ...t) {
	throw Error(`[Immer] minified error nr: ${e}. Full error at: https://bit.ly/3cXEKWf`);
}
var Yi = Object, Xi = Yi.getPrototypeOf, Zi = "constructor", Qi = "prototype", $i = "configurable", ea = "enumerable", ta = "writable", na = "value", ra = (e) => !!e && !!e[B];
function ia(e) {
	var t;
	return e ? sa(e) || ma(e) || !!e[Ji] || !!((t = e[Zi]) != null && t[Ji]) || ha(e) || ga(e) : !1;
}
var aa = Yi[Qi][Zi].toString(), oa = /* @__PURE__ */ new WeakMap();
function sa(e) {
	if (!e || !_a(e)) return !1;
	let t = Xi(e);
	if (t === null || t === Yi[Qi]) return !0;
	let n = Yi.hasOwnProperty.call(t, Zi) && t[Zi];
	if (n === Object) return !0;
	if (!va(n)) return !1;
	let r = oa.get(n);
	return r === void 0 && (r = Function.toString.call(n), oa.set(n, r)), r === aa;
}
function ca(e, t, n = !0) {
	la(e) === 0 ? (n ? Reflect.ownKeys(e) : Yi.keys(e)).forEach((n) => {
		t(n, e[n], e);
	}) : e.forEach((n, r) => t(r, n, e));
}
function la(e) {
	let t = e[B];
	return t ? t.type_ : ma(e) ? 1 : ha(e) ? 2 : ga(e) ? 3 : 0;
}
var ua = (e, t, n = la(e)) => n === 2 ? e.has(t) : Yi[Qi].hasOwnProperty.call(e, t), da = (e, t, n = la(e)) => n === 2 ? e.get(t) : e[t], fa = (e, t, n, r = la(e)) => {
	r === 2 ? e.set(t, n) : r === 3 ? e.add(n) : e[t] = n;
};
function pa(e, t) {
	return e === t ? e !== 0 || 1 / e == 1 / t : e !== e && t !== t;
}
var ma = Array.isArray, ha = (e) => e instanceof Map, ga = (e) => e instanceof Set, _a = (e) => typeof e == "object", va = (e) => typeof e == "function", ya = (e) => typeof e == "boolean";
function ba(e) {
	let t = +e;
	return Number.isInteger(t) && String(t) === e;
}
var xa = (e) => e.copy_ || e.base_, Sa = (e) => e.modified_ ? e.copy_ : e.base_;
function Ca(e, t) {
	if (ha(e)) return new Map(e);
	if (ga(e)) return new Set(e);
	if (ma(e)) return Array[Qi].slice.call(e);
	let n = sa(e);
	if (t === !0 || t === "class_only" && !n) {
		let t = Yi.getOwnPropertyDescriptors(e);
		delete t[B];
		let n = Reflect.ownKeys(t);
		for (let r = 0; r < n.length; r++) {
			let i = n[r], a = t[i];
			a[ta] === !1 && (a[ta] = !0, a[$i] = !0), (a.get || a.set) && (t[i] = {
				[$i]: !0,
				[ta]: !0,
				[ea]: a[ea],
				[na]: e[i]
			});
		}
		return Yi.create(Xi(e), t);
	} else {
		let t = Xi(e);
		if (t !== null && n) return { ...e };
		let r = Yi.create(t);
		return Yi.assign(r, e);
	}
}
function wa(e, t = !1) {
	return Da(e) || ra(e) || !ia(e) ? e : (la(e) > 1 && Yi.defineProperties(e, {
		set: Ea,
		add: Ea,
		clear: Ea,
		delete: Ea
	}), Yi.freeze(e), t && ca(e, (e, t) => {
		wa(t, !0);
	}, !1), e);
}
function Ta() {
	V(2);
}
var Ea = { [na]: Ta };
function Da(e) {
	return e === null || !_a(e) || Yi.isFrozen(e);
}
var Oa = "MapSet", ka = "Patches", Aa = "ArrayMethods", ja = {};
function Ma(e) {
	let t = ja[e];
	return t || V(0, e), t;
}
var Na = (e) => !!ja[e], Pa, Fa = () => Pa, Ia = (e, t) => ({
	drafts_: [],
	parent_: e,
	immer_: t,
	canAutoFreeze_: !0,
	unfinalizedDrafts_: 0,
	handledSet_: /* @__PURE__ */ new Set(),
	processedForPatches_: /* @__PURE__ */ new Set(),
	mapSetPlugin_: Na(Oa) ? Ma(Oa) : void 0,
	arrayMethodsPlugin_: Na(Aa) ? Ma(Aa) : void 0
});
function La(e, t) {
	t && (e.patchPlugin_ = Ma(ka), e.patches_ = [], e.inversePatches_ = [], e.patchListener_ = t);
}
function Ra(e) {
	za(e), e.drafts_.forEach(Va), e.drafts_ = null;
}
function za(e) {
	e === Pa && (Pa = e.parent_);
}
var Ba = (e) => Pa = Ia(Pa, e);
function Va(e) {
	let t = e[B];
	t.type_ === 0 || t.type_ === 1 ? t.revoke_() : t.revoked_ = !0;
}
function Ha(e, t) {
	t.unfinalizedDrafts_ = t.drafts_.length;
	let n = t.drafts_[0];
	if (e !== void 0 && e !== n) {
		n[B].modified_ && (Ra(t), V(4)), ia(e) && (e = Ua(t, e));
		let { patchPlugin_: r } = t;
		r && r.generateReplacementPatches_(n[B].base_, e, t);
	} else e = Ua(t, n);
	return Wa(t, e, !0), Ra(t), t.patches_ && t.patchListener_(t.patches_, t.inversePatches_), e === qi ? void 0 : e;
}
function Ua(e, t) {
	if (Da(t)) return t;
	let n = t[B];
	if (!n) return Qa(t, e.handledSet_, e);
	if (!Ka(n, e)) return t;
	if (!n.modified_) return n.base_;
	if (!n.finalized_) {
		let { callbacks_: t } = n;
		if (t) for (; t.length > 0;) t.pop()(e);
		Xa(n, e);
	}
	return n.copy_;
}
function Wa(e, t, n = !1) {
	!e.parent_ && e.immer_.autoFreeze_ && e.canAutoFreeze_ && wa(t, n);
}
function Ga(e) {
	e.finalized_ = !0, e.scope_.unfinalizedDrafts_--;
}
var Ka = (e, t) => e.scope_ === t, qa = [];
function Ja(e, t, n, r) {
	var i;
	let a = xa(e), o = e.type_;
	if (r !== void 0 && da(a, r, o) === t) {
		fa(a, r, n, o);
		return;
	}
	if (!e.draftLocations_) {
		let t = e.draftLocations_ = /* @__PURE__ */ new Map();
		ca(a, (e, n) => {
			if (ra(n)) {
				let r = t.get(n) || [];
				r.push(e), t.set(n, r);
			}
		});
	}
	let s = (i = e.draftLocations_.get(t)) == null ? qa : i;
	for (let e of s) fa(a, e, n, o);
}
function Ya(e, t, n) {
	e.callbacks_.push(function(r) {
		var i, a;
		let o = t;
		if (!o || !Ka(o, r)) return;
		(i = r.mapSetPlugin_) == null || i.fixSetContents(o);
		let s = Sa(o);
		Ja(e, (a = o.draft_) == null ? o : a, s, n), Xa(o, r);
	});
}
function Xa(e, t) {
	var n, r;
	if (e.modified_ && !e.finalized_ && (e.type_ === 3 || e.type_ === 1 && e.allIndicesReassigned_ || ((n = (r = e.assigned_) == null ? void 0 : r.size) == null ? 0 : n) > 0)) {
		let { patchPlugin_: n } = t;
		if (n) {
			let r = n.getPath(e);
			r && n.generatePatches_(e, r, t);
		}
		Ga(e);
	}
}
function Za(e, t, n) {
	let { scope_: r } = e;
	if (ra(n)) {
		let i = n[B];
		Ka(i, r) && i.callbacks_.push(function() {
			so(e), Ja(e, n, Sa(i), t);
		});
	} else ia(n) && e.callbacks_.push(function() {
		let i = xa(e);
		if (e.type_ === 3) i.has(n) && Qa(n, r.handledSet_, r);
		else if (da(i, t, e.type_) === n) {
			var a;
			r.drafts_.length > 1 && ((a = e.assigned_.get(t)) != null && a) === !0 && e.copy_ && Qa(da(e.copy_, t, e.type_), r.handledSet_, r);
		}
	});
}
function Qa(e, t, n) {
	return !n.immer_.autoFreeze_ && n.unfinalizedDrafts_ < 1 || ra(e) || t.has(e) || !ia(e) || Da(e) ? e : (t.add(e), ca(e, (r, i) => {
		if (ra(i)) {
			let t = i[B];
			Ka(t, n) && (fa(e, r, Sa(t), e.type_), Ga(t));
		} else ia(i) && Qa(i, t, n);
	}), e);
}
function $a(e, t) {
	let n = ma(e), r = {
		type_: +!!n,
		scope_: t ? t.scope_ : Fa(),
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
	}, i = r, a = eo;
	n && (i = [r], a = to);
	let { revoke: o, proxy: s } = Proxy.revocable(i, a);
	return r.draft_ = s, r.revoke_ = o, [s, r];
}
var eo = {
	get(e, t) {
		if (t === B) return e;
		let n = e.scope_.arrayMethodsPlugin_, r = e.type_ === 1 && typeof t == "string";
		if (r && n != null && n.isArrayOperationMethod(t)) return n.createMethodInterceptor(e, t);
		let i = xa(e);
		if (!ua(i, t, e.type_)) return io(e, i, t);
		let a = i[t];
		if (e.finalized_ || !ia(a) || r && e.operationMethod && n != null && n.isMutatingArrayMethod(e.operationMethod) && ba(t)) return a;
		if (a === no(e.base_, t) || ro(e, t, a)) {
			so(e);
			let n = e.type_ === 1 ? +t : t, r = lo(e.scope_, a, e, n);
			return e.copy_[n] = r;
		}
		return a;
	},
	has(e, t) {
		return t in xa(e);
	},
	ownKeys(e) {
		return Reflect.ownKeys(xa(e));
	},
	set(e, t, n) {
		let r = ao(xa(e), t);
		if (r != null && r.set) return r.set.call(e.draft_, n), !0;
		if (!e.modified_) {
			let r = no(xa(e), t), i = r == null ? void 0 : r[B];
			if (i && i.base_ === n) return e.copy_[t] = n, e.assigned_.set(t, !1), !0;
			if (pa(n, r) && (n !== void 0 || ua(e.base_, t, e.type_))) return !0;
			so(e), oo(e);
		}
		return e.copy_[t] === n && (n !== void 0 || ua(e.copy_, t, e.type_)) || Number.isNaN(n) && Number.isNaN(e.copy_[t]) ? !0 : (e.copy_[t] = n, e.assigned_.set(t, !0), Za(e, t, n), !0);
	},
	deleteProperty(e, t) {
		return so(e), no(e.base_, t) !== void 0 || t in e.base_ ? (e.assigned_.set(t, !1), oo(e)) : e.assigned_.delete(t), e.copy_ && delete e.copy_[t], !0;
	},
	getOwnPropertyDescriptor(e, t) {
		let n = xa(e), r = Reflect.getOwnPropertyDescriptor(n, t);
		return r && {
			[ta]: !0,
			[$i]: e.type_ !== 1 || t !== "length",
			[ea]: r[ea],
			[na]: n[t]
		};
	},
	defineProperty() {
		V(11);
	},
	getPrototypeOf(e) {
		return Xi(e.base_);
	},
	setPrototypeOf() {
		V(12);
	}
}, to = {};
for (let e in eo) {
	let t = eo[e];
	to[e] = function() {
		let e = arguments;
		return e[0] = e[0][0], t.apply(this, e);
	};
}
to.deleteProperty = function(e, t) {
	return to.set.call(this, e, t, void 0);
}, to.set = function(e, t, n) {
	return eo.set.call(this, e[0], t, n, e[0]);
};
function no(e, t) {
	let n = e[B];
	return (n ? xa(n) : e)[t];
}
function ro(e, t, n) {
	var r;
	return e.type_ !== 1 || !e.allIndicesReassigned_ || (r = e.assigned_) != null && r.get(t) || !ia(n) || n[B] ? !1 : e.baseRefs_.has(n);
}
function io(e, t, n) {
	var r;
	let i = ao(t, n);
	return i ? na in i ? i[na] : (r = i.get) == null ? void 0 : r.call(e.draft_) : void 0;
}
function ao(e, t) {
	if (!(t in e)) return;
	let n = Xi(e);
	for (; n;) {
		let e = Object.getOwnPropertyDescriptor(n, t);
		if (e) return e;
		n = Xi(n);
	}
}
function oo(e) {
	e.modified_ || (e.modified_ = !0, e.parent_ && oo(e.parent_));
}
function so(e) {
	e.copy_ || (e.assigned_ = /* @__PURE__ */ new Map(), e.copy_ = Ca(e.base_, e.scope_.immer_.useStrictShallowCopy_));
}
var co = class {
	constructor(e) {
		this.autoFreeze_ = !0, this.useStrictShallowCopy_ = !1, this.useStrictIteration_ = !1, this.produce = (e, t, n) => {
			if (va(e) && !va(t)) {
				let n = t;
				t = e;
				let r = this;
				return function(e = n, ...i) {
					return r.produce(e, (e) => t.call(this, e, ...i));
				};
			}
			va(t) || V(6), n !== void 0 && !va(n) && V(7);
			let r;
			if (ia(e)) {
				let i = Ba(this), a = lo(i, e, void 0), o = !0;
				try {
					r = t(a), o = !1;
				} finally {
					o ? Ra(i) : za(i);
				}
				return La(i, n), Ha(r, i);
			} else if (!e || !_a(e)) {
				if (r = t(e), r === void 0 && (r = e), r === qi && (r = void 0), this.autoFreeze_ && wa(r, !0), n) {
					let t = [], i = [];
					Ma(ka).generateReplacementPatches_(e, r, {
						patches_: t,
						inversePatches_: i
					}), n(t, i);
				}
				return r;
			} else V(1, e);
		}, this.produceWithPatches = (e, t) => {
			if (va(e)) return (t, ...n) => this.produceWithPatches(t, (t) => e(t, ...n));
			let n, r;
			return [
				this.produce(e, t, (e, t) => {
					n = e, r = t;
				}),
				n,
				r
			];
		}, ya(e == null ? void 0 : e.autoFreeze) && this.setAutoFreeze(e.autoFreeze), ya(e == null ? void 0 : e.useStrictShallowCopy) && this.setUseStrictShallowCopy(e.useStrictShallowCopy), ya(e == null ? void 0 : e.useStrictIteration) && this.setUseStrictIteration(e.useStrictIteration);
	}
	createDraft(e) {
		ia(e) || V(8), ra(e) && (e = uo(e));
		let t = Ba(this), n = lo(t, e, void 0);
		return n[B].isManual_ = !0, za(t), n;
	}
	finishDraft(e, t) {
		let n = e && e[B];
		(!n || !n.isManual_) && V(9);
		let { scope_: r } = n;
		return La(r, t), Ha(void 0, r);
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
		let r = Ma(ka).applyPatches_;
		return ra(e) ? r(e, t) : this.produce(e, (e) => r(e, t));
	}
};
function lo(e, t, n, r) {
	var i, a;
	let [o, s] = ha(t) ? Ma(Oa).proxyMap_(t, n) : ga(t) ? Ma(Oa).proxySet_(t, n) : $a(t, n);
	return ((i = n == null ? void 0 : n.scope_) == null ? Fa() : i).drafts_.push(o), s.callbacks_ = (a = n == null ? void 0 : n.callbacks_) == null ? [] : a, s.key_ = r, n && r !== void 0 ? Ya(n, s, r) : s.callbacks_.push(function(e) {
		var t;
		(t = e.mapSetPlugin_) == null || t.fixSetContents(s);
		let { patchPlugin_: n } = e;
		s.modified_ && n && n.generatePatches_(s, [], e);
	}), o;
}
function uo(e) {
	return ra(e) || V(10, e), fo(e);
}
function fo(e) {
	if (!ia(e) || Da(e)) return e;
	let t = e[B], n, r = !0;
	if (t) {
		if (!t.modified_) return t.base_;
		t.finalized_ = !0, n = Ca(e, t.scope_.immer_.useStrictShallowCopy_), r = t.scope_.immer_.shouldUseStrictIteration();
	} else n = Ca(e, !0);
	return ca(n, (e, t) => {
		fa(n, e, fo(t));
	}, r), t && (t.finalized_ = !1), n;
}
var po = new co().produce, H = (e) => e;
//#endregion
//#region node_modules/redux-thunk/dist/redux-thunk.mjs
function mo(e) {
	return ({ dispatch: t, getState: n }) => (r) => (i) => typeof i == "function" ? i(t, n, e) : r(i);
}
var ho = mo(), go = mo, _o = typeof window < "u" && window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ ? window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ : function() {
	if (arguments.length !== 0) return typeof arguments[0] == "object" ? Wi : Wi.apply(null, arguments);
};
typeof window < "u" && window.__REDUX_DEVTOOLS_EXTENSION__ && window.__REDUX_DEVTOOLS_EXTENSION__;
function vo(e, t) {
	function n(...n) {
		if (t) {
			let r = t(...n);
			if (!r) throw Error(Ds(0));
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
	return n.toString = () => `${e}`, n.type = e, n.match = (t) => Ki(t) && t.type === e, n;
}
var yo = class e extends Array {
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
function bo(e) {
	return ia(e) ? po(e, () => {}) : e;
}
function xo(e, t, n) {
	return e.has(t) ? e.get(t) : e.set(t, n(t)).get(t);
}
function So(e) {
	return typeof e == "boolean";
}
var Co = () => function(e) {
	let { thunk: t = !0, immutableCheck: n = !0, serializableCheck: r = !0, actionCreatorCheck: i = !0 } = e == null ? {} : e, a = new yo();
	return t && (So(t) ? a.push(ho) : a.push(go(t.extraArgument))), a;
}, wo = "RTK_autoBatch", To = () => (e) => ({
	payload: e,
	meta: { [wo]: !0 }
}), Eo = (e) => (t) => {
	setTimeout(t, e);
}, Do = (e, t) => (n) => {
	let r = !1, i = () => {
		r || (r = !0, cancelAnimationFrame(a), clearTimeout(o), n());
	}, a = e(i), o = setTimeout(i, t);
}, Oo = (e = { type: "raf" }) => (t) => (...n) => {
	let r = t(...n), i = !0, a = !1, o = !1, s = /* @__PURE__ */ new Set(), c = e.type === "tick" ? queueMicrotask : e.type === "raf" ? typeof window < "u" && window.requestAnimationFrame ? Do(window.requestAnimationFrame, 100) : Eo(10) : e.type === "callback" ? e.queueNotification : Eo(e.timeout), l = () => {
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
				return i = !(!(e == null || (t = e.meta) == null) && t[wo]), a = !i, a && (o || (o = !0, c(l))), r.dispatch(e);
			} finally {
				i = !0;
			}
		}
	});
}, ko = (e) => function(t) {
	let { autoBatch: n = !0 } = t == null ? {} : t, r = new yo(e);
	return n && r.push(Oo(typeof n == "object" ? n : void 0)), r;
};
function Ao(e) {
	let t = Co(), { reducer: n = void 0, middleware: r, devTools: i = !0, duplicateMiddlewareCheck: a = !0, preloadedState: o = void 0, enhancers: s = void 0 } = e || {}, c;
	if (typeof n == "function") c = n;
	else if (Bi(n)) c = Ui(n);
	else throw Error(Ds(1));
	let l;
	l = typeof r == "function" ? r(t) : t();
	let u = Wi;
	i && (u = _o({
		trace: !1,
		...typeof i == "object" && i
	}));
	let d = ko(Gi(...l)), f = typeof s == "function" ? s(d) : d(), p = u(...f);
	return Vi(c, o, p);
}
function jo(e) {
	let t = {}, n = [], r, i = {
		addCase(e, n) {
			let r = typeof e == "string" ? e : e.type;
			if (!r) throw Error(Ds(28));
			if (r in t) throw Error(Ds(29));
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
function Mo(e) {
	return typeof e == "function";
}
function No(e, t) {
	let [n, r, i] = jo(t), a;
	if (Mo(e)) a = () => bo(e());
	else {
		let t = bo(e);
		a = () => t;
	}
	function o(e = a(), t) {
		let o = [n[t.type], ...r.filter(({ matcher: e }) => e(t)).map(({ reducer: e }) => e)];
		return o.filter((e) => !!e).length === 0 && (o = [i]), o.reduce((e, n) => {
			if (n) if (ra(e)) {
				let r = n(e, t);
				return r === void 0 ? e : r;
			} else if (ia(e)) return po(e, (e) => n(e, t));
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
var Po = "ModuleSymbhasOwnPr-0123456789ABCDEFGHNRVfgctiUvz_KqYTJkLxpZXIjQW", Fo = (e = 21) => {
	let t = "", n = e;
	for (; n--;) t += Po[Math.random() * 64 | 0];
	return t;
}, Io = /* @__PURE__ */ Symbol.for("rtk-slice-createasyncthunk");
function Lo(e, t) {
	return `${e}/${t}`;
}
function Ro({ creators: e } = {}) {
	var t;
	let n = e == null || (t = e.asyncThunk) == null ? void 0 : t[Io];
	return function(e) {
		let { name: t, reducerPath: r = t } = e;
		if (!t) throw Error(Ds(11));
		let i = (typeof e.reducers == "function" ? e.reducers(Vo()) : e.reducers) || {}, a = Object.keys(i), o = {
			sliceCaseReducersByName: {},
			sliceCaseReducersByType: {},
			actionCreators: {},
			sliceMatchers: []
		}, s = {
			addCase(e, t) {
				let n = typeof e == "string" ? e : e.type;
				if (!n) throw Error(Ds(12));
				if (n in o.sliceCaseReducersByType) throw Error(Ds(13));
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
				type: Lo(t, r),
				createNotation: typeof e.reducers == "function"
			};
			Uo(a) ? Go(o, a, s, n) : Ho(o, a, s);
		});
		function c() {
			let [t = {}, n = [], r = void 0] = typeof e.extraReducers == "function" ? jo(e.extraReducers) : [e.extraReducers], i = {
				...t,
				...o.sliceCaseReducersByType
			};
			return No(e.initialState, (e) => {
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
				return i === void 0 && n && (i = xo(d, r, m)), i;
			}
			function i(t = l) {
				return xo(xo(u, n, () => /* @__PURE__ */ new WeakMap()), t, () => {
					var r;
					let i = {};
					for (let [a, o] of Object.entries((r = e.selectors) == null ? {} : r)) i[a] = zo(o, t, () => xo(d, t, m), n);
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
function zo(e, t, n, r) {
	function i(i, ...a) {
		let o = t(i);
		return o === void 0 && r && (o = n()), e(o, ...a);
	}
	return i.unwrapped = e, i;
}
var Bo = /* @__PURE__ */ Ro();
function Vo() {
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
function Ho({ type: e, reducerName: t, createNotation: n }, r, i) {
	let a, o;
	if ("reducer" in r) {
		if (n && !Wo(r)) throw Error(Ds(17));
		a = r.reducer, o = r.prepare;
	} else a = r;
	i.addCase(e, a).exposeCaseReducer(t, a).exposeAction(t, o ? vo(e, o) : vo(e));
}
function Uo(e) {
	return e._reducerDefinitionType === "asyncThunk";
}
function Wo(e) {
	return e._reducerDefinitionType === "reducerWithPrepare";
}
function Go({ type: e, reducerName: t }, n, r, i) {
	if (!i) throw Error(Ds(18));
	let { payloadCreator: a, fulfilled: o, pending: s, rejected: c, settled: l, options: u } = n, d = i(e, a, u);
	r.exposeAction(t, d), o && r.addCase(d.fulfilled, o), s && r.addCase(d.pending, s), c && r.addCase(d.rejected, c), l && r.addMatcher(d.settled, l), r.exposeCaseReducer(t, {
		fulfilled: o || Ko,
		pending: s || Ko,
		rejected: c || Ko,
		settled: l || Ko
	});
}
function Ko() {}
var qo = "task", Jo = "listener", Yo = "completed", Xo = "cancelled", Zo = `task-${Xo}`, Qo = `task-${Yo}`, $o = `${Jo}-${Xo}`, es = `${Jo}-${Yo}`, ts = class {
	constructor(e) {
		ei(this, "code", void 0), ei(this, "name", "TaskAbortError"), ei(this, "message", void 0), this.code = e, this.message = `${qo} ${Xo} (reason: ${e})`;
	}
}, ns = (e, t) => {
	if (typeof e != "function") throw TypeError(Ds(32));
}, rs = () => {}, is = (e, t = rs) => (e.catch(t), e), as = (e, t) => (e.addEventListener("abort", t, { once: !0 }), () => e.removeEventListener("abort", t)), os = (e) => {
	if (e.aborted) throw new ts(e.reason);
};
function ss(e, t) {
	let n = rs;
	return new Promise((r, i) => {
		let a = () => i(new ts(e.reason));
		if (e.aborted) {
			a();
			return;
		}
		n = as(e, a), t.finally(() => n()).then(r, i);
	}).finally(() => {
		n = rs;
	});
}
var cs = async (e, t) => {
	try {
		return await Promise.resolve(), {
			status: "ok",
			value: await e()
		};
	} catch (e) {
		return {
			status: e instanceof ts ? "cancelled" : "rejected",
			error: e
		};
	} finally {
		t == null || t();
	}
}, ls = (e) => (t) => is(ss(e, t).then((t) => (os(e), t))), us = (e) => {
	let t = ls(e);
	return (e) => t(new Promise((t) => setTimeout(t, e)));
}, { assign: ds } = Object, fs = {}, ps = "listenerMiddleware", ms = (e, t) => {
	let n = (t) => as(e, () => t.abort(e.reason));
	return (r, i) => {
		ns(r, "taskExecutor");
		let a = new AbortController();
		n(a);
		let o = cs(async () => {
			os(e), os(a.signal);
			let t = await r({
				pause: ls(a.signal),
				delay: us(a.signal),
				signal: a.signal
			});
			return os(a.signal), t;
		}, () => a.abort(Qo));
		return i != null && i.autoJoin && t.push(o.catch(rs)), {
			result: ls(e)(o),
			cancel() {
				a.abort(Zo);
			}
		};
	};
}, hs = (e, t) => {
	let n = async (n, r) => {
		os(t);
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
			let e = await ss(t, Promise.race(a));
			return os(t), e;
		} finally {
			i();
		}
	};
	return ((e, t) => is(n(e, t)));
}, gs = (e) => {
	let { type: t, actionCreator: n, matcher: r, predicate: i, effect: a } = e;
	if (t) i = vo(t).match;
	else if (n) t = n.type, i = n.match;
	else if (r) i = r;
	else if (!i) throw Error(Ds(21));
	return ns(a, "options.listener"), {
		predicate: i,
		type: t,
		effect: a
	};
}, _s = /* @__PURE__ */ ds((e) => {
	let { type: t, predicate: n, effect: r } = gs(e);
	return {
		id: Fo(),
		effect: r,
		type: t,
		predicate: n,
		pending: /* @__PURE__ */ new Set(),
		unsubscribe: () => {
			throw Error(Ds(22));
		}
	};
}, { withTypes: () => _s }), vs = (e, t) => {
	let { type: n, effect: r, predicate: i } = gs(t);
	return Array.from(e.values()).find((e) => (typeof n == "string" ? e.type === n : e.predicate === i) && e.effect === r);
}, ys = (e) => {
	e.pending.forEach((e) => {
		e.abort($o);
	});
}, bs = (e, t) => () => {
	for (let e of t.keys()) ys(e);
	e.clear();
}, xs = (e, t, n) => {
	try {
		e(t, n);
	} catch (e) {
		setTimeout(() => {
			throw e;
		}, 0);
	}
}, Ss = /* @__PURE__ */ ds(/* @__PURE__ */ vo(`${ps}/add`), { withTypes: () => Ss }), Cs = /* @__PURE__ */ vo(`${ps}/removeAll`), ws = /* @__PURE__ */ ds(/* @__PURE__ */ vo(`${ps}/remove`), { withTypes: () => ws }), Ts = (...e) => {
	console.error(`${ps}/error`, ...e);
}, Es = (e = {}) => {
	let t = /* @__PURE__ */ new Map(), n = /* @__PURE__ */ new Map(), r = (e) => {
		var t;
		let r = (t = n.get(e)) == null ? 0 : t;
		n.set(e, r + 1);
	}, i = (e) => {
		var t;
		let r = (t = n.get(e)) == null ? 1 : t;
		r === 1 ? n.delete(e) : n.set(e, r - 1);
	}, { extra: a, onError: o = Ts } = e;
	ns(o, "onError");
	let s = (e) => (e.unsubscribe = () => t.delete(e.id), t.set(e.id, e), (t) => {
		e.unsubscribe(), t != null && t.cancelActive && ys(e);
	}), c = ((e) => {
		var n;
		let r = (n = vs(t, e)) == null ? _s(e) : n;
		return s(r);
	});
	ds(c, { withTypes: () => c });
	let l = (e) => {
		let n = vs(t, e);
		return n && (n.unsubscribe(), e.cancelActive && ys(n)), !!n;
	};
	ds(l, { withTypes: () => l });
	let u = async (e, n, s, l) => {
		let u = new AbortController(), d = hs(c, u.signal), f = [];
		try {
			e.pending.add(u), r(e), await Promise.resolve(e.effect(n, ds({}, s, {
				getOriginalState: l,
				condition: (e, t) => d(e, t).then(Boolean),
				take: d,
				delay: us(u.signal),
				pause: ls(u.signal),
				extra: a,
				signal: u.signal,
				fork: ms(u.signal, f),
				unsubscribe: e.unsubscribe,
				subscribe: () => {
					t.set(e.id, e);
				},
				cancelActiveListeners: () => {
					e.pending.forEach((e, t, n) => {
						e !== u && (e.abort($o), n.delete(e));
					});
				},
				cancel: () => {
					u.abort($o), e.pending.delete(u);
				},
				throwIfCancelled: () => {
					os(u.signal);
				}
			})));
		} catch (e) {
			e instanceof ts || xs(o, e, { raisedBy: "effect" });
		} finally {
			await Promise.all(f), u.abort(es), i(e), e.pending.delete(u);
		}
	}, d = bs(t, n);
	return {
		middleware: (e) => (n) => (r) => {
			if (!Ki(r)) return n(r);
			if (Ss.match(r)) return c(r.payload);
			if (Cs.match(r)) {
				d();
				return;
			}
			if (ws.match(r)) return l(r.payload);
			let i = e.getState(), a = () => {
				if (i === fs) throw Error(Ds(23));
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
							s = !1, xs(o, e, { raisedBy: "predicate" });
						}
						s && u(t, r, e, a);
					}
				}
			} finally {
				i = fs;
			}
			return s;
		},
		startListening: c,
		stopListening: l,
		clearListeners: d
	};
};
function Ds(e) {
	return `Minified Redux Toolkit error #${e}; visit https://redux-toolkit.js.org/Errors?code=${e} for the full message or use the non-minified dev environment for full errors. `;
}
//#endregion
//#region node_modules/recharts/es6/state/layoutSlice.js
var Os = Bo({
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
}), ks = Os.actions, As = ks.setMargin, js = ks.setLayout, Ms = ks.setChartSize, Ns = ks.setScale, Ps = Os.reducer;
//#endregion
//#region node_modules/recharts/es6/util/getSliced.js
function Fs(e, t, n) {
	return Array.isArray(e) && e && t + n !== 0 ? e.slice(t, n + 1) : e;
}
//#endregion
//#region node_modules/recharts/es6/util/isWellBehavedNumber.js
function U(e) {
	return Number.isFinite(e);
}
function Is(e) {
	return typeof e == "number" && e > 0 && Number.isFinite(e);
}
//#endregion
//#region node_modules/recharts/es6/util/ChartUtils.js
function Ls(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Rs(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Ls(Object(n), !0).forEach(function(t) {
			zs(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Ls(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function zs(e, t, n) {
	return (t = Bs(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function Bs(e) {
	var t = Vs(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Vs(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function Hs(e, t, n) {
	return yn(e) || yn(t) ? n : fn(t) ? rn(e, t, n) : typeof t == "function" ? t(e) : n;
}
var Us = (e, t, n) => {
	if (t && n) {
		var r = n.width, i = n.height, a = t.align, o = t.verticalAlign, s = t.layout;
		if ((s === "vertical" || s === "horizontal" && o === "middle") && a !== "center" && L(e[a])) return Rs(Rs({}, e), {}, { [a]: e[a] + (r || 0) });
		if ((s === "horizontal" || s === "vertical" && a === "center") && o !== "middle" && L(e[o])) return Rs(Rs({}, e), {}, { [o]: e[o] + (i || 0) });
	}
	return e;
}, Ws = (e, t) => e === "horizontal" && t === "xAxis" || e === "vertical" && t === "yAxis" || e === "centric" && t === "angleAxis" || e === "radial" && t === "radiusAxis", Gs = (e, t) => {
	if (!t || t.length !== 2 || !L(t[0]) || !L(t[1])) return e;
	var n = Math.min(t[0], t[1]), r = Math.max(t[0], t[1]), i = [e[0], e[1]];
	return (!L(e[0]) || e[0] < n) && (i[0] = n), (!L(e[1]) || e[1] > r) && (i[1] = r), i[0] > r && (i[0] = r), i[1] < n && (i[1] = n), i;
}, Ks = {
	sign: (e) => {
		var t, n = e.length;
		if (!(n <= 0)) {
			var r = (t = e[0]) == null ? void 0 : t.length;
			if (!(r == null || r <= 0)) for (var i = 0; i < r; ++i) for (var a = 0, o = 0, s = 0; s < n; ++s) {
				var c = e[s], l = c == null ? void 0 : c[i];
				if (l != null) {
					var u = l[1], d = l[0], f = un(u) ? d : u;
					f >= 0 ? (l[0] = a, a += f, l[1] = a) : (l[0] = o, o += f, l[1] = o);
				}
			}
		}
	},
	expand: Yt,
	none: Gt,
	silhouette: Xt,
	wiggle: Zt,
	positive: (e) => {
		var t, n = e.length;
		if (!(n <= 0)) {
			var r = (t = e[0]) == null ? void 0 : t.length;
			if (!(r == null || r <= 0)) for (var i = 0; i < r; ++i) for (var a = 0, o = 0; o < n; ++o) {
				var s = e[o], c = s == null ? void 0 : s[i];
				if (c != null) {
					var l = un(c[1]) ? c[0] : c[1];
					l >= 0 ? (c[0] = a, a += l, c[1] = a) : (c[0] = 0, c[1] = 0);
				}
			}
		}
	}
}, qs = (e, t, n) => {
	var r, i = (r = Ks[n]) == null ? Gt : r, a = Jt().keys(t).value((e, t) => Number(Hs(e, t, 0))).order(I).offset(i)(e);
	return a.forEach((n, r) => {
		n.forEach((n, i) => {
			var a = Hs(e[i], t[r], 0);
			Array.isArray(a) && a.length === 2 && L(a[0]) && L(a[1]) && (n[0] = a[0], n[1] = a[1]);
		});
	}), a;
};
function Js(e) {
	return e == null ? void 0 : String(e);
}
var Ys = (e) => {
	var t = e.axis, n = e.ticks, r = e.offset, i = e.bandSize, a = e.entry, o = e.index;
	if (t.type === "category") return n[o] ? n[o].coordinate + r : null;
	var s = Hs(a, t.dataKey, t.scale.domain()[o]);
	if (yn(s)) return null;
	var c = t.scale.map(s);
	return L(c) ? c - i / 2 + r : null;
}, Xs = (e) => {
	var t = e.numericAxis, n = t.scale.domain();
	if (t.type === "number") {
		var r = Math.min(n[0], n[1]), i = Math.max(n[0], n[1]);
		return r <= 0 && i >= 0 ? 0 : i < 0 ? i : r;
	}
	return n[0];
}, Zs = (e) => {
	var t = e.flat(2).filter(L);
	return [Math.min(...t), Math.max(...t)];
}, Qs = (e) => [e[0] === Infinity ? 0 : e[0], e[1] === -Infinity ? 0 : e[1]], $s = (e, t, n) => {
	if (!(e == null || Object.keys(e).length === 0)) return Qs(Object.keys(e).reduce((r, i) => {
		var a = e[i];
		if (!a) return r;
		var o = a.stackedData.reduce((e, r) => {
			var i = Zs(Fs(r, t, n));
			return !U(i[0]) || !U(i[1]) ? e : [Math.min(e[0], i[0]), Math.max(e[1], i[1])];
		}, [Infinity, -Infinity]);
		return [Math.min(o[0], r[0]), Math.max(o[1], r[1])];
	}, [Infinity, -Infinity]));
}, ec = /^dataMin[\s]*-[\s]*([0-9]+([.]{1}[0-9]+){0,1})$/, tc = /^dataMax[\s]*\+[\s]*([0-9]+([.]{1}[0-9]+){0,1})$/, nc = (e, t, n) => {
	if (e && e.scale && e.scale.bandwidth) {
		var r = e.scale.bandwidth();
		if (!n || r > 0) return r;
	}
	if (e && t && t.length >= 2) {
		for (var i = Ci(t, (e) => e.coordinate), a = Infinity, o = 1, s = i.length; o < s; o++) {
			var c = i[o], l = i[o - 1];
			a = Math.min(((c == null ? void 0 : c.coordinate) || 0) - ((l == null ? void 0 : l.coordinate) || 0), a);
		}
		return a === Infinity ? 0 : a;
	}
	return n ? void 0 : 0;
};
function rc(e) {
	var t = e.tooltipEntrySettings, n = e.dataKey, r = e.payload, i = e.value, a = e.name;
	return Rs(Rs({}, t), {}, {
		dataKey: n,
		payload: r,
		value: i,
		name: a
	});
}
function ic(e, t) {
	if (e != null) return String(e);
	if (typeof t == "string") return t;
}
var ac = (e, t) => {
	if (t === "horizontal") return e.relativeX;
	if (t === "vertical") return e.relativeY;
}, oc = (e, t) => t === "centric" ? e.angle : e.radius, sc = (e) => e.layout.width, cc = (e) => e.layout.height, lc = (e) => e.layout.scale, uc = (e) => e.layout.margin, dc = z((e) => e.cartesianAxis.xAxis, (e) => Object.values(e)), fc = z((e) => e.cartesianAxis.yAxis, (e) => Object.values(e)), pc = "data-recharts-item-index";
//#endregion
//#region node_modules/recharts/es6/state/selectors/selectChartOffsetInternal.js
function mc(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function hc(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? mc(Object(n), !0).forEach(function(t) {
			gc(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : mc(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function gc(e, t, n) {
	return (t = _c(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function _c(e) {
	var t = vc(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function vc(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var yc = (e) => e.brush.height;
function W(e) {
	return fc(e).reduce((e, t) => t.orientation === "left" && !t.mirror && !t.hide ? e + (typeof t.width == "number" ? t.width : 60) : e, 0);
}
function bc(e) {
	return fc(e).reduce((e, t) => t.orientation === "right" && !t.mirror && !t.hide ? e + (typeof t.width == "number" ? t.width : 60) : e, 0);
}
function xc(e) {
	return dc(e).reduce((e, t) => t.orientation === "top" && !t.mirror && !t.hide ? e + t.height : e, 0);
}
function Sc(e) {
	return dc(e).reduce((e, t) => t.orientation === "bottom" && !t.mirror && !t.hide ? e + t.height : e, 0);
}
var Cc = z([
	sc,
	cc,
	uc,
	yc,
	W,
	bc,
	xc,
	Sc,
	wi,
	Ti
], (e, t, n, r, i, a, o, s, c, l) => {
	var u = {
		left: (n.left || 0) + i,
		right: (n.right || 0) + a
	}, d = hc(hc({}, {
		top: (n.top || 0) + o,
		bottom: (n.bottom || 0) + s
	}), u), f = d.bottom;
	d.bottom += r, d = Us(d, c, l);
	var p = e - d.left - d.right, m = t - d.top - d.bottom;
	return hc(hc({ brushBottom: f }, d), {}, {
		width: Math.max(p, 0),
		height: Math.max(m, 0)
	});
}), wc = z(Cc, (e) => ({
	x: e.left,
	y: e.top,
	width: e.width,
	height: e.height
})), Tc = z(sc, cc, (e, t) => ({
	x: 0,
	y: 0,
	width: e,
	height: t
})), Ec = /*#__PURE__*/ (0, C.createContext)(null), Dc = () => (0, C.useContext)(Ec) != null, Oc = (e) => e.brush, kc = z([
	Oc,
	Cc,
	uc
], (e, t, n) => ({
	height: e.height,
	x: L(e.x) ? e.x : t.left,
	y: L(e.y) ? e.y : t.top + t.height + t.brushBottom - ((n == null ? void 0 : n.bottom) || 0),
	width: L(e.width) ? e.width : t.width
}));
//#endregion
//#region node_modules/es-toolkit/dist/function/debounce.mjs
function Ac(e, t, { signal: n, edges: r } = {}) {
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
function jc(e, t = 0, n = {}) {
	typeof n != "object" && (n = {});
	let { leading: r = !1, trailing: i = !0, maxWait: a } = n, o = [, ,];
	r && (o[0] = "leading"), i && (o[1] = "trailing");
	let s, c = null, l = Ac(function(...t) {
		s = e.apply(this, t), c = null;
	}, t, { edges: o }), u = function(...t) {
		return a != null && (c === null && (c = Date.now()), Date.now() - c >= a) ? (s = e.apply(this, t), c = Date.now(), l.cancel(), l.schedule(), s) : (l.apply(this, t), s);
	};
	return u.cancel = l.cancel, u.flush = () => (l.flush(), s), u;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/function/throttle.mjs
function Mc(e, t = 0, n = {}) {
	let { leading: r = !0, trailing: i = !0 } = n;
	return jc(e, t, {
		leading: r,
		maxWait: t,
		trailing: i
	});
}
//#endregion
//#region node_modules/recharts/es6/util/LogUtils.js
var Nc = function(e, t) {
	var n = [...arguments].slice(2);
	if (typeof console < "u" && console.warn && (t === void 0 && console.warn("LogUtils requires an error message argument"), !e)) if (t === void 0) console.warn("Minified exception occurred; use the non-minified dev environment for the full error message and additional helpful warnings.");
	else {
		var r = 0;
		console.warn(t.replace(/%s/g, () => n[r++]));
	}
}, Pc = {
	width: "100%",
	height: "100%",
	debounce: 0,
	minWidth: 0,
	initialDimension: {
		width: -1,
		height: -1
	}
}, Fc = (e, t, n) => {
	var r = n.width, i = r === void 0 ? Pc.width : r, a = n.height, o = a === void 0 ? Pc.height : a, s = n.aspect, c = n.maxHeight, l = dn(i) ? e : Number(i), u = dn(o) ? t : Number(o);
	return s && s > 0 && (l ? u = l / s : u && (l = u * s), c && u != null && u > c && (u = c)), {
		calculatedWidth: l,
		calculatedHeight: u
	};
}, Ic = {
	width: 0,
	height: 0,
	overflow: "visible"
}, Lc = {
	width: 0,
	overflowX: "visible"
}, Rc = {
	height: 0,
	overflowY: "visible"
}, zc = {}, Bc = (e) => {
	var t = e.width, n = e.height, r = dn(t), i = dn(n);
	return r && i ? Ic : r ? Lc : i ? Rc : zc;
};
function Vc(e) {
	var t = e.width, n = e.height, r = e.aspect, i = t, a = n;
	return i === void 0 && a === void 0 ? (i = Pc.width, a = Pc.height) : i === void 0 ? i = r && r > 0 ? void 0 : Pc.width : a === void 0 && (a = r && r > 0 ? void 0 : Pc.height), {
		width: i,
		height: a
	};
}
//#endregion
//#region node_modules/recharts/es6/component/ResponsiveContainer.js
var Hc = [
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
function Uc() {
	return Uc = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, Uc.apply(null, arguments);
}
function Wc(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Gc(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Wc(Object(n), !0).forEach(function(t) {
			Kc(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Wc(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Kc(e, t, n) {
	return (t = qc(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function qc(e) {
	var t = Jc(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Jc(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function G(e, t) {
	return $c(e) || Qc(e, t) || Xc(e, t) || Yc();
}
function Yc() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function Xc(e, t) {
	if (e) {
		if (typeof e == "string") return Zc(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? Zc(e, t) : void 0;
	}
}
function Zc(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function Qc(e, t) {
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
function $c(e) {
	if (Array.isArray(e)) return e;
}
function el(e, t) {
	if (e == null) return {};
	var n, r, i = tl(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function tl(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var nl = /*#__PURE__*/ (0, C.createContext)(Pc.initialDimension);
function rl(e) {
	return Is(e.width) && Is(e.height);
}
function il(e) {
	var t = e.children, n = e.width, r = e.height, i = (0, C.useMemo)(() => ({
		width: n,
		height: r
	}), [n, r]);
	return rl(i) ? /*#__PURE__*/ C.createElement(nl.Provider, { value: i }, t) : null;
}
var al = () => (0, C.useContext)(nl), ol = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.aspect, r = e.initialDimension, i = r === void 0 ? Pc.initialDimension : r, a = e.width, o = e.height, s = e.minWidth, c = s === void 0 ? Pc.minWidth : s, l = e.minHeight, u = e.maxHeight, d = e.children, f = e.debounce, p = f === void 0 ? Pc.debounce : f, m = e.id, h = e.className, g = e.onResize, _ = e.style, v = _ === void 0 ? {} : _, y = el(e, Hc), b = (0, C.useRef)(null), x = (0, C.useRef)();
	x.current = g, (0, C.useImperativeHandle)(t, () => b.current);
	var S = G((0, C.useState)({
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
		if (b.current == null || typeof ResizeObserver > "u") return Sn;
		var e = (e) => {
			var t, n = e[0];
			if (n != null) {
				var r = n.contentRect, i = r.width, a = r.height;
				E(i, a), (t = x.current) == null || t.call(x, i, a);
			}
		};
		p > 0 && (e = Mc(e, p, {
			trailing: !0,
			leading: !1
		}));
		var t = new ResizeObserver(e), n = b.current.getBoundingClientRect(), r = n.width, i = n.height;
		return E(r, i), t.observe(b.current), () => {
			t.disconnect();
		};
	}, [E, p]);
	var D = w.containerWidth, O = w.containerHeight;
	Nc(!n || n > 0, "The aspect(%s) must be greater than zero.", n);
	var k = Fc(D, O, {
		width: a,
		height: o,
		aspect: n,
		maxHeight: u
	}), A = k.calculatedWidth, j = k.calculatedHeight;
	return Nc(D < 0 || O < 0 || A != null && A > 0 || j != null && j > 0, "The width(%s) and height(%s) of chart should be greater than 0,\n       please check the style of container, or the props width(%s) and height(%s),\n       or add a minWidth(%s) or minHeight(%s) or use aspect(%s) to control the\n       height and width.", A, j, a, o, c, l, n), /*#__PURE__*/ C.createElement("div", Uc({
		id: m ? `${m}` : void 0,
		className: Ne("recharts-responsive-container", h),
		style: Gc(Gc({}, v), {}, {
			width: a,
			height: o,
			minWidth: c,
			minHeight: l,
			maxHeight: u
		}),
		ref: b
	}, y), /*#__PURE__*/ C.createElement("div", { style: Bc({
		width: a,
		height: o
	}) }, /*#__PURE__*/ C.createElement(il, {
		width: A,
		height: j
	}, d)));
}), sl = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = al();
	if (Is(n.width) && Is(n.height)) return e.children;
	var r = Vc({
		width: e.width,
		height: e.height,
		aspect: e.aspect
	}), i = r.width, a = r.height, o = Fc(void 0, void 0, {
		width: i,
		height: a,
		aspect: e.aspect,
		maxHeight: e.maxHeight
	}), s = o.calculatedWidth, c = o.calculatedHeight;
	return L(s) && L(c) ? /*#__PURE__*/ C.createElement(il, {
		width: s,
		height: c
	}, e.children) : /*#__PURE__*/ C.createElement(ol, Uc({}, e, {
		width: i,
		height: a,
		ref: t
	}));
});
//#endregion
//#region node_modules/recharts/es6/context/chartLayoutContext.js
function cl(e) {
	if (e) return {
		x: e.x,
		y: e.y,
		upperWidth: "upperWidth" in e ? e.upperWidth : e.width,
		lowerWidth: "lowerWidth" in e ? e.lowerWidth : e.width,
		width: e.width,
		height: e.height
	};
}
var ll = () => {
	var e, t = Dc(), n = R(wc), r = R(kc), i = (e = R(Oc)) == null ? void 0 : e.padding;
	return !t || !r || !i ? n : {
		width: r.width - i.left - i.right,
		height: r.height - i.top - i.bottom,
		x: i.left,
		y: i.top
	};
}, ul = {
	top: 0,
	bottom: 0,
	left: 0,
	right: 0,
	width: 0,
	height: 0,
	brushBottom: 0
}, dl = () => {
	var e;
	return (e = R(Cc)) == null ? ul : e;
}, fl = () => R(sc), pl = () => R(cc), K = (e) => e.layout.layoutType, ml = () => R(K), hl = () => {
	var e = ml();
	if (e === "horizontal" || e === "vertical") return e;
}, gl = (e) => {
	var t = e.layout.layoutType;
	if (t === "centric" || t === "radial") return t;
}, _l = () => ml() !== void 0, vl = (e) => {
	var t = qr(), n = Dc(), r = e.width, i = e.height, a = al(), o = r, s = i;
	return a && (o = a.width > 0 ? a.width : r, s = a.height > 0 ? a.height : i), (0, C.useEffect)(() => {
		!n && Is(o) && Is(s) && t(Ms({
			width: o,
			height: s
		}));
	}, [
		t,
		n,
		o,
		s
	]), null;
}, yl = Bo({
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
			prepare: To()
		},
		replaceLegendPayload: {
			reducer(e, t) {
				var n = t.payload, r = n.prev, i = n.next, a = uo(e).payload.indexOf(H(r));
				a > -1 && (e.payload[a] = H(i));
			},
			prepare: To()
		},
		removeLegendPayload: {
			reducer(e, t) {
				var n = uo(e).payload.indexOf(H(t.payload));
				n > -1 && e.payload.splice(n, 1);
			},
			prepare: To()
		}
	}
}), bl = yl.actions;
bl.setLegendSize, bl.setLegendSettings;
var xl = bl.addLegendPayload, Sl = bl.replaceLegendPayload, Cl = bl.removeLegendPayload, wl = yl.reducer, Tl = /* @__PURE__ */ o(((e) => {
	var t = d();
	t.useSyncExternalStore, t.useRef, t.useEffect, t.useMemo, t.useDebugValue;
}));
(/* @__PURE__ */ o(((e, t) => {
	t.exports = Tl();
})))();
function El(e) {
	e();
}
function Dl() {
	let e = null, t = null;
	return {
		clear() {
			e = null, t = null;
		},
		notify() {
			El(() => {
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
var Ol = {
	notify() {},
	get: () => []
};
function kl(e, t) {
	let n, r = Ol, i = 0, a = !1;
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
		i++, n || (n = t ? t.addNestedSub(c) : e.subscribe(c), r = Dl());
	}
	function d() {
		i--, n && i === 0 && (n(), n = void 0, r.clear(), r = Ol);
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
var Al = typeof window < "u" && window.document !== void 0 && window.document.createElement !== void 0, jl = typeof navigator < "u" && navigator.product === "ReactNative", Ml = Al || jl ? C.useLayoutEffect : C.useEffect;
function Nl(e, t) {
	return e === t ? e !== 0 || t !== 0 || 1 / e == 1 / t : e !== e && t !== t;
}
function Pl(e, t) {
	if (Nl(e, t)) return !0;
	if (typeof e != "object" || !e || typeof t != "object" || !t) return !1;
	let n = Object.keys(e), r = Object.keys(t);
	if (n.length !== r.length) return !1;
	for (let r = 0; r < n.length; r++) if (!Object.prototype.hasOwnProperty.call(t, n[r]) || !Nl(e[n[r]], t[n[r]])) return !1;
	return !0;
}
var Fl = /* @__PURE__ */ Symbol.for("react-redux-context"), Il = typeof globalThis < "u" ? globalThis : {};
function Ll() {
	var e;
	if (!C.createContext) return {};
	let t = (e = Il[Fl]) == null ? Il[Fl] = /* @__PURE__ */ new Map() : e, n = t.get(C.createContext);
	return n || (n = C.createContext(null), t.set(C.createContext, n)), n;
}
var Rl = /* @__PURE__ */ Ll();
function zl(e) {
	let { children: t, context: n, serverState: r, store: i } = e, a = C.useMemo(() => {
		let e = kl(i);
		return {
			store: i,
			subscription: e,
			getServerState: r ? () => r : void 0
		};
	}, [i, r]), o = C.useMemo(() => i.getState(), [i]);
	Ml(() => {
		let { subscription: e } = a;
		return e.onStateChange = e.notifyNestedSubs, e.trySubscribe(), o !== i.getState() && e.notifyNestedSubs(), () => {
			e.tryUnsubscribe(), e.onStateChange = void 0;
		};
	}, [a, o]);
	let s = n || Rl;
	return /* @__PURE__ */ C.createElement(s.Provider, { value: a }, t);
}
var Bl = zl, Vl = /* @__PURE__ */ new Set([
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
function Hl(e, t) {
	return e == null && t == null ? !0 : typeof e == "number" && typeof t == "number" ? e === t || e !== e && t !== t : e === t;
}
function Ul(e, t) {
	for (var n of /* @__PURE__ */ new Set([...Object.keys(e), ...Object.keys(t)])) if (Vl.has(n)) {
		if (e[n] == null && t[n] == null) continue;
		if (!Pl(e[n], t[n])) return !1;
	} else if (!Hl(e[n], t[n])) return !1;
	return !0;
}
//#endregion
//#region node_modules/recharts/es6/component/DefaultTooltipContent.js
function Wl() {
	return Wl = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, Wl.apply(null, arguments);
}
function Gl(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Kl(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Gl(Object(n), !0).forEach(function(t) {
			ql(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Gl(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function ql(e, t, n) {
	return (t = Jl(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function Jl(e) {
	var t = Yl(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Yl(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function Xl(e, t) {
	return tu(e) || eu(e, t) || Ql(e, t) || Zl();
}
function Zl() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function Ql(e, t) {
	if (e) {
		if (typeof e == "string") return $l(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? $l(e, t) : void 0;
	}
}
function $l(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function eu(e, t) {
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
function tu(e) {
	if (Array.isArray(e)) return e;
}
function nu(e) {
	return Array.isArray(e) && fn(e[0]) && fn(e[1]) ? e.join(" ~ ") : e;
}
var ru = {
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
function iu(e, t) {
	return t == null ? e : Ci(e, t);
}
var au = (e) => {
	var t = e.separator, n = t === void 0 ? ru.separator : t, r = e.contentStyle, i = e.itemStyle, a = e.labelStyle, o = a === void 0 ? ru.labelStyle : a, s = e.payload, c = e.formatter, l = e.itemSorter, u = e.wrapperClassName, d = e.labelClassName, f = e.label, p = e.labelFormatter, m = e.accessibilityLayer, h = m === void 0 ? ru.accessibilityLayer : m, g = () => {
		if (s && s.length) {
			var e = {
				padding: 0,
				margin: 0
			}, t = iu(s, l).map((e, t) => {
				if (!e || e.type === "none") return null;
				var r = e.formatter || c || nu, a = e.value, o = e.name, l = a, u = o;
				if (r) {
					var d = r(a, o, e, t, s);
					if (Array.isArray(d)) {
						var f = Xl(d, 2);
						l = f[0], u = f[1];
					} else if (d != null) l = d;
					else return null;
				}
				var p = Kl(Kl({}, ru.itemStyle), {}, { color: e.color || ru.itemStyle.color }, i);
				return /*#__PURE__*/ C.createElement("li", {
					className: "recharts-tooltip-item",
					key: `tooltip-item-${t}`,
					style: p
				}, fn(u) ? /*#__PURE__*/ C.createElement("span", { className: "recharts-tooltip-item-name" }, u) : null, fn(u) ? /*#__PURE__*/ C.createElement("span", { className: "recharts-tooltip-item-separator" }, n) : null, /*#__PURE__*/ C.createElement("span", { className: "recharts-tooltip-item-value" }, l), /*#__PURE__*/ C.createElement("span", { className: "recharts-tooltip-item-unit" }, e.unit || ""));
			});
			return /*#__PURE__*/ C.createElement("ul", {
				className: "recharts-tooltip-item-list",
				style: e
			}, t);
		}
		return null;
	}, _ = Kl(Kl({}, ru.contentStyle), r), v = Kl({ margin: 0 }, o), y = !yn(f), b = y ? f : "", x = Ne("recharts-default-tooltip", u), S = Ne("recharts-tooltip-label", d);
	y && p && s != null && (b = p(f, s));
	var w = h ? {
		role: "status",
		"aria-live": "assertive"
	} : {};
	return /*#__PURE__*/ C.createElement("div", Wl({
		className: x,
		style: _
	}, w), /*#__PURE__*/ C.createElement("p", {
		className: S,
		style: v
	}, /*#__PURE__*/ C.isValidElement(b) ? b : `${b}`), g());
}, ou = "recharts-tooltip-wrapper", su = { visibility: "hidden" };
function cu(e) {
	var t = e.coordinate, n = e.translateX, r = e.translateY;
	return Ne(ou, {
		[`${ou}-right`]: L(n) && t && L(t.x) && n >= t.x,
		[`${ou}-left`]: L(n) && t && L(t.x) && n < t.x,
		[`${ou}-bottom`]: L(r) && t && L(t.y) && r >= t.y,
		[`${ou}-top`]: L(r) && t && L(t.y) && r < t.y
	});
}
function lu(e) {
	var t = e.allowEscapeViewBox, n = e.coordinate, r = e.key, i = e.offset, a = e.position, o = e.reverseDirection, s = e.tooltipDimension, c = e.viewBox, l = e.viewBoxDimension;
	if (a && L(a[r])) return a[r];
	var u = n[r] - s - (i > 0 ? i : 0), d = n[r] + i;
	if (t[r]) return o[r] ? u : d;
	var f = c[r];
	return f == null ? 0 : o[r] ? Math.max(u < f ? d : u, f) : l == null ? 0 : d + s > f + l ? Math.max(u, f) : Math.max(d, f);
}
function uu(e) {
	var t = e.translateX, n = e.translateY;
	return { transform: e.useTranslate3d ? `translate3d(${t}px, ${n}px, 0)` : `translate(${t}px, ${n}px)` };
}
function du(e) {
	var t = e.allowEscapeViewBox, n = e.coordinate, r = e.offsetTop, i = e.offsetLeft, a = e.position, o = e.reverseDirection, s = e.tooltipBox, c = e.useTranslate3d, l = e.viewBox, u, d, f;
	return s.height > 0 && s.width > 0 && n ? (d = lu({
		allowEscapeViewBox: t,
		coordinate: n,
		key: "x",
		offset: i,
		position: a,
		reverseDirection: o,
		tooltipDimension: s.width,
		viewBox: l,
		viewBoxDimension: l.width
	}), f = lu({
		allowEscapeViewBox: t,
		coordinate: n,
		key: "y",
		offset: r,
		position: a,
		reverseDirection: o,
		tooltipDimension: s.height,
		viewBox: l,
		viewBoxDimension: l.height
	}), u = uu({
		translateX: d,
		translateY: f,
		useTranslate3d: c
	})) : u = su, {
		cssProperties: u,
		cssClasses: cu({
			translateX: d,
			translateY: f,
			coordinate: n
		})
	};
}
var fu = {
	devToolsEnabled: !0,
	isSsr: !(typeof window < "u" && window.document && window.document.createElement && window.setTimeout)
};
//#endregion
//#region node_modules/recharts/es6/util/usePrefersReducedMotion.js
function pu(e, t) {
	return vu(e) || _u(e, t) || hu(e, t) || mu();
}
function mu() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function hu(e, t) {
	if (e) {
		if (typeof e == "string") return gu(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? gu(e, t) : void 0;
	}
}
function gu(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function _u(e, t) {
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
function vu(e) {
	if (Array.isArray(e)) return e;
}
function yu() {
	var e = pu((0, C.useState)(() => fu.isSsr || !window.matchMedia ? !1 : window.matchMedia("(prefers-reduced-motion: reduce)").matches), 2), t = e[0], n = e[1];
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
function bu(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function xu(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? bu(Object(n), !0).forEach(function(t) {
			Su(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : bu(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Su(e, t, n) {
	return (t = Cu(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function Cu(e) {
	var t = wu(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function wu(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function Tu(e, t) {
	return Au(e) || ku(e, t) || Du(e, t) || Eu();
}
function Eu() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function Du(e, t) {
	if (e) {
		if (typeof e == "string") return Ou(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? Ou(e, t) : void 0;
	}
}
function Ou(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function ku(e, t) {
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
function Au(e) {
	if (Array.isArray(e)) return e;
}
function ju(e) {
	if (!(e.prefersReducedMotion && e.isAnimationActive === "auto") && e.isAnimationActive && e.active) {
		var t = typeof e.animationEasing == "string" ? e.animationEasing : "ease";
		return `transform ${e.animationDuration}ms ${t}`;
	}
}
function Mu(e) {
	var t, n, r, i, a, o, s = yu(), c = Tu(C.useState(() => ({
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
	}, [(t = e.coordinate) == null ? void 0 : t.x, (n = e.coordinate) == null ? void 0 : n.y]), l.dismissed && (((r = (i = e.coordinate) == null ? void 0 : i.x) == null ? 0 : r) !== l.dismissedAtCoordinate.x || ((a = (o = e.coordinate) == null ? void 0 : o.y) == null ? 0 : a) !== l.dismissedAtCoordinate.y) && u(xu(xu({}, l), {}, { dismissed: !1 }));
	var d = du({
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
	}), f = d.cssClasses, p = d.cssProperties, m = xu(xu({}, e.hasPortalFromProps ? {} : xu(xu({ transition: ju({
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
var Nu = /*#__PURE__*/ C.memo(Mu), Pu = () => {
	var e;
	return (e = R((e) => e.rootProps.accessibilityLayer)) == null || e;
};
//#endregion
//#region node_modules/recharts/es6/shape/Curve.js
function Fu() {
	return Fu = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, Fu.apply(null, arguments);
}
function Iu(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Lu(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Iu(Object(n), !0).forEach(function(t) {
			Ru(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Iu(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Ru(e, t, n) {
	return (t = zu(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function zu(e) {
	var t = Bu(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Bu(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var Vu = {
	curveBasisClosed: wt,
	curveBasisOpen: Et,
	curveBasis: St,
	curveBumpX: _t,
	curveBumpY: vt,
	curveLinearClosed: Ot,
	curveLinear: dt,
	curveMonotoneX: It,
	curveMonotoneY: Lt,
	curveNatural: Bt,
	curveStep: Ht,
	curveStepAfter: Wt,
	curveStepBefore: Ut
}, Hu = (e) => U(e.x) && U(e.y), Uu = (e) => e.base != null && Hu(e.base) && Hu(e), Wu = (e) => e.x, Gu = (e) => e.y, Ku = (e, t) => {
	if (typeof e == "function") return e;
	var n = `curve${bn(e)}`;
	if ((n === "curveMonotone" || n === "curveBump") && t) {
		var r = Vu[`${n}${t === "vertical" ? "Y" : "X"}`];
		if (r) return r;
	}
	return Vu[n] || dt;
}, qu = {
	connectNulls: !1,
	type: "linear"
}, Ju = (e) => {
	var t = e.type, n = t === void 0 ? qu.type : t, r = e.points, i = r === void 0 ? [] : r, a = e.baseLine, o = e.layout, s = e.connectNulls, c = s === void 0 ? qu.connectNulls : s, l = Ku(n, o), u = c ? i.filter(Hu) : i;
	if (Array.isArray(a)) {
		var d, f = i.map((e, t) => Lu(Lu({}, e), {}, { base: a[t] }));
		return d = o === "vertical" ? ht().y(Gu).x1(Wu).x0((e) => e.base.x) : ht().x(Wu).y1(Gu).y0((e) => e.base.y), d.defined(Uu).curve(l)(c ? f.filter(Uu) : f);
	}
	return (o === "vertical" && L(a) ? ht().y(Gu).x1(Wu).x0(a) : L(a) ? ht().x(Wu).y1(Gu).y0(a) : mt().x(Wu).y(Gu)).defined(Hu).curve(l)(u);
}, Yu = (e) => {
	var t = e.className, n = e.points, r = e.path, i = e.pathRef, a = ml();
	if ((!n || !n.length) && !r) return null;
	var o = {
		type: e.type,
		points: e.points,
		baseLine: e.baseLine,
		layout: e.layout || a,
		connectNulls: e.connectNulls
	}, s = n && n.length ? Ju(o) : r;
	return /*#__PURE__*/ C.createElement("path", Fu({}, ze(e), wn(e), {
		className: Ne("recharts-curve", t),
		d: s === null ? void 0 : s,
		ref: i
	}));
}, Xu = [
	"x",
	"y",
	"top",
	"left",
	"width",
	"height",
	"className"
];
function Zu() {
	return Zu = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, Zu.apply(null, arguments);
}
function Qu(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function $u(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Qu(Object(n), !0).forEach(function(t) {
			ed(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Qu(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
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
function rd(e, t) {
	if (e == null) return {};
	var n, r, i = id(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function id(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var ad = (e, t, n, r, i, a) => `M${e},${i}v${r}M${a},${t}h${n}`, od = (e) => {
	var t = e.x, n = t === void 0 ? 0 : t, r = e.y, i = r === void 0 ? 0 : r, a = e.top, o = a === void 0 ? 0 : a, s = e.left, c = s === void 0 ? 0 : s, l = e.width, u = l === void 0 ? 0 : l, d = e.height, f = d === void 0 ? 0 : d, p = e.className, m = rd(e, Xu), h = $u({
		x: n,
		y: i,
		top: o,
		left: c,
		width: u,
		height: f
	}, m);
	return !L(n) || !L(i) || !L(u) || !L(f) || !L(o) || !L(c) ? null : /*#__PURE__*/ C.createElement("path", Zu({}, Ve(h), {
		className: Ne("recharts-cross", p),
		d: ad(n, i, u, f, o, c)
	}));
};
//#endregion
//#region node_modules/recharts/es6/util/cursor/getCursorRectangle.js
function sd(e, t, n, r) {
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
var cd = (e, t) => [
	0,
	3 * e,
	3 * t - 6 * e,
	3 * e - 3 * t + 1
], ld = (e, t) => e.map((e, n) => e * t ** n).reduce((e, t) => e + t), ud = (e, t) => (n) => ld(cd(e, t), n), dd = (e, t) => (n) => ld([...cd(e, t).map((e, t) => e * t).slice(1), 0], n), fd = (e) => {
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
}, pd = function() {
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
			var t = fd(e[0]);
			if (t) return t;
	}
	return e.length === 4 ? e : [
		0,
		0,
		1,
		1
	];
}, md = (e, t, n, r) => {
	var i = ud(e, n), a = ud(t, r), o = dd(e, n), s = (e) => e > 1 ? 1 : e < 0 ? 0 : e, c = (e) => {
		for (var t = e > 1 ? 1 : e, n = t, r = 0; r < 8; ++r) {
			var c = i(n) - t, l = o(n);
			if (Math.abs(c - t) < 1e-4 || l < 1e-4) return a(n);
			n = s(n - c / l);
		}
		return a(n);
	};
	return c.isStepper = !1, c;
}, hd = function() {
	return md(...pd(...arguments));
}, gd = function() {
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
}, _d = (e) => {
	if (typeof e == "string") switch (e) {
		case "ease":
		case "ease-in-out":
		case "ease-out":
		case "ease-in":
		case "linear": return hd(e);
		case "spring": return gd();
		default: if (e.split("(")[0] === "cubic-bezier") return hd(e);
	}
	return typeof e == "function" ? e : null;
}, vd = /*#__PURE__*/ (0, C.createContext)((e, t, n) => {
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
vd.Provider;
function yd(e) {
	var t = (0, C.useContext)(vd);
	return (0, C.useMemo)(() => e == null ? t : e, [e, t]);
}
//#endregion
//#region node_modules/recharts/es6/animation/AnimationHandle.js
function bd(e, t, n) {
	return (t = xd(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function xd(e) {
	var t = Sd(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Sd(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var Cd = "init", wd = "pending", Td = "active", Ed = "completed";
function Dd(e) {
	return Math.max(0, e);
}
var Od = class {
	getAnimationStartedTime() {
		return this.animationStartedTime;
	}
	getBeginStartedTime() {
		return this.beginStartedTime;
	}
	constructor(e) {
		var t;
		bd(this, "state", Cd), this.animationId = e.animationId, this.onAnimationEnd = e.onAnimationEnd, this.animationDuration = Dd(e.animationDuration), this.animationBegin = Dd(e.animationBegin), this.progress = 0, this.from = e.from, this.to = e.to, this.easing = e.easing, (t = e.onAnimationStart) == null || t.call(e);
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
		if (this.getState() === Cd) return this.state = wd, this.beginStartedTime = e, this.animationBegin;
		if (this.getState() === wd) {
			if (this.beginStartedTime == null) throw Error();
			var t = e - this.beginStartedTime;
			return t >= this.animationBegin ? (this.state = Td, this.animationStartedTime = e, this.nextAnimationUpdate(0)) : Dd(this.animationBegin - t);
		}
		if (this.getState() === Td) {
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
		this.state = Ed;
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
}, kd = class extends Od {
	nextAnimationUpdate() {
		return 0;
	}
	getInterpolated() {
		return this.easing(_n(this.getFrom(), this.getTo(), this.getProgress()));
	}
}, Ad = class {
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
function jd(e, t) {
	return Id(e) || Fd(e, t) || Nd(e, t) || Md();
}
function Md() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function Nd(e, t) {
	if (e) {
		if (typeof e == "string") return Pd(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? Pd(e, t) : void 0;
	}
}
function Pd(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function Fd(e, t) {
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
function Id(e) {
	if (Array.isArray(e)) return e;
}
var Ld = {
	begin: 0,
	duration: 1e3,
	easing: "ease",
	isActive: !0,
	canBegin: !0,
	onAnimationEnd: () => {},
	onAnimationStart: () => {}
}, Rd = 0, zd = 1;
function Bd(e) {
	var t = Mn(e, Ld), n = t.animationId, r = t.isActive, i = t.canBegin, a = t.duration, o = t.easing, s = t.begin, c = t.onAnimationEnd, l = t.onAnimationStart, u = t.children, d = yu(), f = r === "auto" ? !fu.isSsr && !d : r, p = yd(t.animationController), m = jd((0, C.useState)(f ? Rd : zd), 2), h = m[0], g = m[1];
	return (0, C.useEffect)(() => {
		f || g(zd);
	}, [f]), (0, C.useEffect)(() => {
		var e = _d(o);
		return !f || !i || e == null ? Sn : p(new Ad(), new kd({
			animationId: n,
			easing: e,
			animationDuration: a,
			animationBegin: s,
			onAnimationStart: l,
			onAnimationEnd: c,
			from: Rd,
			to: zd
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
function Vd(e) {
	var t = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : "animation-", n = (0, C.useRef)(mn(t)), r = (0, C.useRef)(e);
	return r.current !== e && (n.current = mn(t), r.current = e), n.current;
}
//#endregion
//#region node_modules/recharts/es6/animation/util.js
var Hd = (e) => e.replace(/([A-Z])/g, (e) => `-${e.toLowerCase()}`), Ud = (e, t, n) => e.map((e) => `${Hd(e)} ${t}ms ${n}`).join(","), Wd = ["radius"], Gd = ["radius"], Kd, qd, Jd, Yd, Xd, Zd, Qd, $d, ef, tf;
function nf(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function rf(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? nf(Object(n), !0).forEach(function(t) {
			af(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : nf(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function af(e, t, n) {
	return (t = of(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function of(e) {
	var t = sf(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function sf(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function cf() {
	return cf = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, cf.apply(null, arguments);
}
function lf(e, t) {
	if (e == null) return {};
	var n, r, i = uf(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function uf(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function df(e, t) {
	return gf(e) || hf(e, t) || pf(e, t) || ff();
}
function ff() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function pf(e, t) {
	if (e) {
		if (typeof e == "string") return mf(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? mf(e, t) : void 0;
	}
}
function mf(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function hf(e, t) {
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
function gf(e) {
	if (Array.isArray(e)) return e;
}
function _f(e, t) {
	return t || (t = e.slice(0)), Object.freeze(Object.defineProperties(e, { raw: { value: Object.freeze(t) } }));
}
var vf = (e, t, n, r, i) => {
	var a = sn(n), o = sn(r), s = Math.min(Math.abs(a) / 2, Math.abs(o) / 2), c = o >= 0 ? 1 : -1, l = a >= 0 ? 1 : -1, u = +(o >= 0 && a >= 0 || o < 0 && a < 0), d;
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
		d = cn(Kd || (Kd = _f([
			"M",
			",",
			""
		])), e, t + c * f[0]), f[0] > 0 && (d += cn(qd || (qd = _f([
			"A ",
			",",
			",0,0,",
			",",
			",",
			""
		])), f[0], f[0], u, e + l * f[0], t)), d += cn(Jd || (Jd = _f([
			"L ",
			",",
			""
		])), e + n - l * f[1], t), f[1] > 0 && (d += cn(Yd || (Yd = _f([
			"A ",
			",",
			",0,0,",
			",\n        ",
			",",
			""
		])), f[1], f[1], u, e + n, t + c * f[1])), d += cn(Xd || (Xd = _f([
			"L ",
			",",
			""
		])), e + n, t + r - c * f[2]), f[2] > 0 && (d += cn(Zd || (Zd = _f([
			"A ",
			",",
			",0,0,",
			",\n        ",
			",",
			""
		])), f[2], f[2], u, e + n - l * f[2], t + r)), d += cn(Qd || (Qd = _f([
			"L ",
			",",
			""
		])), e + l * f[3], t + r), f[3] > 0 && (d += cn($d || ($d = _f([
			"A ",
			",",
			",0,0,",
			",\n        ",
			",",
			""
		])), f[3], f[3], u, e, t + r - c * f[3])), d += "Z";
	} else if (s > 0 && i === +i && i > 0) {
		var _ = Math.min(s, i);
		d = cn(ef || (ef = _f(/* @__PURE__ */ "M .,.\n            A .,.,0,0,.,.,.\n            L .,.\n            A .,.,0,0,.,.,.\n            L .,.\n            A .,.,0,0,.,.,.\n            L .,.\n            A .,.,0,0,.,.,. Z".split("."))), e, t + c * _, _, _, u, e + l * _, t, e + n - l * _, t, _, _, u, e + n, t + c * _, e + n, t + r - c * _, _, _, u, e + n - l * _, t + r, e + l * _, t + r, _, _, u, e, t + r - c * _);
	} else d = cn(tf || (tf = _f([
		"M ",
		",",
		" h ",
		" v ",
		" h ",
		" Z"
	])), e, t, n, r, -n);
	return d;
}, yf = {
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
}, bf = (e) => {
	var t = Mn(e, yf), n = (0, C.useRef)(null), r = df((0, C.useState)(-1), 2), i = r[0], a = r[1];
	(0, C.useEffect)(() => {
		if (n.current && n.current.getTotalLength) try {
			var e = n.current.getTotalLength();
			e && a(e);
		} catch (e) {}
	}, []);
	var o = t.x, s = t.y, c = t.width, l = t.height, u = t.radius, d = t.className, f = t.animationEasing, p = t.animationDuration, m = t.animationBegin, h = t.isAnimationActive, g = t.isUpdateAnimationActive, _ = (0, C.useRef)(c), v = (0, C.useRef)(l), y = (0, C.useRef)(o), b = (0, C.useRef)(s), x = Vd((0, C.useMemo)(() => ({
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
	var S = Ne("recharts-rectangle", d);
	if (!g) {
		var w = Ve(t);
		w.radius;
		var T = lf(w, Wd);
		return /*#__PURE__*/ C.createElement("path", cf({}, T, {
			x: sn(o),
			y: sn(s),
			width: sn(c),
			height: sn(l),
			radius: typeof u == "number" ? u : void 0,
			className: S,
			d: vf(o, s, c, l, u)
		}));
	}
	var E = _.current, D = v.current, O = y.current, k = b.current, A = `0px ${i === -1 ? 1 : i}px`, j = `${i}px ${i}px`, M = Ud(["strokeDasharray"], p, typeof f == "string" ? f : yf.animationEasing);
	return /*#__PURE__*/ C.createElement(Bd, {
		animationId: x,
		key: x,
		canBegin: i > 0,
		duration: p,
		easing: f,
		isActive: g,
		begin: m
	}, (e) => {
		var r = _n(E, c, e), i = _n(D, l, e), a = _n(O, o, e), d = _n(k, s, e);
		n.current && (_.current = r, v.current = i, y.current = a, b.current = d);
		var f = h ? e > 0 ? {
			transition: M,
			strokeDasharray: j
		} : { strokeDasharray: A } : { strokeDasharray: j }, p = Ve(t);
		p.radius;
		var m = lf(p, Gd);
		return /*#__PURE__*/ C.createElement("path", cf({}, m, {
			radius: typeof u == "number" ? u : void 0,
			className: S,
			d: vf(a, d, r, i, u),
			ref: n,
			style: rf(rf({}, f), t.style)
		}));
	});
};
//#endregion
//#region node_modules/recharts/es6/util/PolarUtils.js
function xf(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Sf(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? xf(Object(n), !0).forEach(function(t) {
			Cf(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : xf(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Cf(e, t, n) {
	return (t = wf(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function wf(e) {
	var t = Tf(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Tf(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var Ef = Math.PI / 180, Df = (e) => e * 180 / Math.PI, Of = (e, t, n, r) => ({
	x: e + Math.cos(-Ef * r) * n,
	y: t + Math.sin(-Ef * r) * n
}), kf = function(e, t) {
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
}, Af = (e, t) => {
	var n = e.x, r = e.y, i = t.x, a = t.y;
	return Math.sqrt((n - i) ** 2 + (r - a) ** 2);
}, jf = (e, t) => {
	var n = e.x, r = e.y, i = t.cx, a = t.cy, o = Af({
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
		angle: Df(c),
		angleInRadian: c
	};
}, Mf = (e) => {
	var t = e.startAngle, n = e.endAngle, r = Math.floor(t / 360), i = Math.floor(n / 360), a = Math.min(r, i);
	return {
		startAngle: t - a * 360,
		endAngle: n - a * 360
	};
}, Nf = (e, t) => {
	var n = t.startAngle, r = t.endAngle, i = Math.floor(n / 360), a = Math.floor(r / 360);
	return e + Math.min(i, a) * 360;
}, Pf = (e, t) => {
	var n = e.relativeX, r = e.relativeY, i = jf({
		x: n,
		y: r
	}, t), a = i.radius, o = i.angle, s = t.innerRadius, c = t.outerRadius;
	if (a < s || a > c || a === 0) return null;
	var l = Mf(t), u = l.startAngle, d = l.endAngle, f = o, p;
	if (u <= d) {
		for (; f > d;) f -= 360;
		for (; f < u;) f += 360;
		p = f >= u && f <= d;
	} else {
		for (; f > u;) f -= 360;
		for (; f < d;) f += 360;
		p = f >= d && f <= u;
	}
	return p ? Sf(Sf({}, t), {}, {
		radius: a,
		angle: Nf(f, t)
	}) : null;
};
//#endregion
//#region node_modules/recharts/es6/util/cursor/getRadialCursorPoints.js
function Ff(e) {
	var t = e.cx, n = e.cy, r = e.radius, i = e.startAngle, a = e.endAngle;
	return {
		points: [Of(t, n, r, i), Of(t, n, r, a)],
		cx: t,
		cy: n,
		radius: r,
		startAngle: i,
		endAngle: a
	};
}
//#endregion
//#region node_modules/recharts/es6/shape/Sector.js
var If, Lf, Rf, zf, Bf, Vf, Hf;
function Uf() {
	return Uf = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, Uf.apply(null, arguments);
}
function Wf(e, t) {
	return t || (t = e.slice(0)), Object.freeze(Object.defineProperties(e, { raw: { value: Object.freeze(t) } }));
}
var Gf = (e, t) => ln(t - e) * Math.min(Math.abs(t - e), 359.999), Kf = (e) => {
	var t = e.cx, n = e.cy, r = e.radius, i = e.angle, a = e.sign, o = e.isExternal, s = e.cornerRadius, c = e.cornerIsExternal, l = s * (o ? 1 : -1) + r, u = Math.asin(s / l) / Ef, d = c ? i : i + a * u, f = Of(t, n, l, d), p = Of(t, n, r, d), m = c ? i - a * u : i;
	return {
		center: f,
		circleTangency: p,
		lineTangency: Of(t, n, l * Math.cos(u * Ef), m),
		theta: u
	};
}, qf = (e) => {
	var t = e.cx, n = e.cy, r = e.innerRadius, i = e.outerRadius, a = e.startAngle, o = e.endAngle, s = Gf(a, o), c = a + s, l = Of(t, n, i, a), u = Of(t, n, i, c), d = cn(If || (If = Wf([
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
		var f = Of(t, n, r, a), p = Of(t, n, r, c);
		d += cn(Lf || (Lf = Wf([
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
	} else d += cn(Rf || (Rf = Wf([
		"L ",
		",",
		" Z"
	])), t, n);
	return d;
}, Jf = (e) => {
	var t = e.cx, n = e.cy, r = e.innerRadius, i = e.outerRadius, a = e.cornerRadius, o = e.forceCornerRadius, s = e.cornerIsExternal, c = e.startAngle, l = e.endAngle, u = ln(l - c), d = Kf({
		cx: t,
		cy: n,
		radius: i,
		angle: c,
		sign: u,
		cornerRadius: a,
		cornerIsExternal: s
	}), f = d.circleTangency, p = d.lineTangency, m = d.theta, h = Kf({
		cx: t,
		cy: n,
		radius: i,
		angle: l,
		sign: -u,
		cornerRadius: a,
		cornerIsExternal: s
	}), g = h.circleTangency, _ = h.lineTangency, v = h.theta, y = s ? Math.abs(c - l) : Math.abs(c - l) - m - v;
	if (y < 0) return o ? cn(zf || (zf = Wf([
		"M ",
		",",
		"\n        a",
		",",
		",0,0,1,",
		",0\n        a",
		",",
		",0,0,1,",
		",0\n      "
	])), p.x, p.y, a, a, a * 2, a, a, -a * 2) : qf({
		cx: t,
		cy: n,
		innerRadius: r,
		outerRadius: i,
		startAngle: c,
		endAngle: l
	});
	var b = cn(Bf || (Bf = Wf([
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
		var x = Kf({
			cx: t,
			cy: n,
			radius: r,
			angle: c,
			sign: u,
			isExternal: !0,
			cornerRadius: a,
			cornerIsExternal: s
		}), S = x.circleTangency, C = x.lineTangency, w = x.theta, T = Kf({
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
		b += cn(Vf || (Vf = Wf([
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
	} else b += cn(Hf || (Hf = Wf([
		"L",
		",",
		"Z"
	])), t, n);
	return b;
}, Yf = {
	cx: 0,
	cy: 0,
	innerRadius: 0,
	outerRadius: 0,
	startAngle: 0,
	endAngle: 0,
	cornerRadius: 0,
	forceCornerRadius: !1,
	cornerIsExternal: !1
}, Xf = (e) => {
	var t = Mn(e, Yf), n = t.cx, r = t.cy, i = t.innerRadius, a = t.outerRadius, o = t.cornerRadius, s = t.forceCornerRadius, c = t.cornerIsExternal, l = t.startAngle, u = t.endAngle, d = t.className;
	if (a < i || l === u) return null;
	var f = Ne("recharts-sector", d), p = a - i, m = hn(o, p, 0, !0), h = m > 0 && Math.abs(l - u) < 360 ? Jf({
		cx: n,
		cy: r,
		innerRadius: i,
		outerRadius: a,
		cornerRadius: Math.min(m, p / 2),
		forceCornerRadius: s,
		cornerIsExternal: c,
		startAngle: l,
		endAngle: u
	}) : qf({
		cx: n,
		cy: r,
		innerRadius: i,
		outerRadius: a,
		startAngle: l,
		endAngle: u
	});
	return /*#__PURE__*/ C.createElement("path", Uf({}, Ve(t), {
		className: f,
		d: h
	}));
};
//#endregion
//#region node_modules/recharts/es6/util/cursor/getCursorPoints.js
function Zf(e, t, n) {
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
	if (Cn(t)) {
		if (e === "centric") {
			var r = t.cx, i = t.cy, a = t.innerRadius, o = t.outerRadius, s = t.angle, c = Of(r, i, a, s), l = Of(r, i, o, s);
			return [{
				x: c.x,
				y: c.y
			}, {
				x: l.x,
				y: l.y
			}];
		}
		return Ff(t);
	}
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/util/toNumber.mjs
function Qf(e) {
	return vi(e) ? NaN : Number(e);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/util/toFinite.mjs
function $f(e) {
	return e ? (e = Qf(e), e === Infinity || e === -Infinity ? (e < 0 ? -1 : 1) * Number.MAX_VALUE : e === e ? e : 0) : e === 0 ? e : 0;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/math/range.mjs
function ep(e, t, n) {
	n && typeof n != "number" && hi(e, t, n) && (t = n = void 0), e = $f(e), t === void 0 ? (t = e, e = 0) : t = $f(t), n = n === void 0 ? e < t ? 1 : -1 : $f(n);
	let r = Math.max(Math.ceil((t - e) / (n || 1)), 0), i = Array(r);
	for (let t = 0; t < r; t++) i[t] = e, e += n;
	return i;
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/dataSelectors.js
var tp = (e) => e.chartData, np = z([tp], (e) => {
	var t = e.chartData == null ? 0 : e.chartData.length - 1;
	return {
		chartData: e.chartData,
		computedData: e.computedData,
		dataEndIndex: t,
		dataStartIndex: 0
	};
}), rp = (e, t, n, r) => r ? np(e) : tp(e), ip = (e, t, n) => n ? np(e) : tp(e), ap = z([rp], (e) => {
	var t = e.chartData, n = e.dataStartIndex, r = e.dataEndIndex;
	return t == null ? [] : t.slice(n, r + 1);
});
z([np], (e) => {
	var t = e.chartData, n = e.dataStartIndex, r = e.dataEndIndex;
	return t == null ? [] : t.slice(n, r + 1);
});
var op = z([tp], (e) => {
	var t = e.chartData, n = e.dataStartIndex, r = e.dataEndIndex;
	return t == null ? [] : t.slice(n, r + 1);
});
//#endregion
//#region node_modules/recharts/es6/util/isDomainSpecifiedByUser.js
function sp(e, t) {
	return fp(e) || dp(e, t) || lp(e, t) || cp();
}
function cp() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function lp(e, t) {
	if (e) {
		if (typeof e == "string") return up(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? up(e, t) : void 0;
	}
}
function up(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function dp(e, t) {
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
function fp(e) {
	if (Array.isArray(e)) return e;
}
function pp(e) {
	if (Array.isArray(e) && e.length === 2) {
		var t = sp(e, 2), n = t[0], r = t[1];
		if (U(n) && U(r)) return !0;
	}
	return !1;
}
function mp(e, t, n) {
	return n ? e : [Math.min(e[0], t[0]), Math.max(e[1], t[1])];
}
function hp(e, t) {
	if (t && typeof e != "function" && Array.isArray(e) && e.length === 2) {
		var n = sp(e, 2), r = n[0], i = n[1], a, o;
		if (U(r)) a = r;
		else if (typeof r == "function") return;
		if (U(i)) o = i;
		else if (typeof i == "function") return;
		var s = [a, o];
		if (pp(s)) return s;
	}
}
function gp(e, t, n) {
	if (!(!n && t == null)) {
		if (typeof e == "function" && t != null) try {
			var r = e(t, n);
			if (pp(r)) return mp(r, t, n);
		} catch (e) {}
		if (Array.isArray(e) && e.length === 2) {
			var i = sp(e, 2), a = i[0], o = i[1], s, c;
			if (a === "auto") t != null && (s = Math.min(...t));
			else if (L(a)) s = a;
			else if (typeof a == "function") try {
				t != null && (s = a(t == null ? void 0 : t[0]));
			} catch (e) {}
			else if (typeof a == "string" && ec.test(a)) {
				var l = ec.exec(a);
				if (l == null || l[1] == null || t == null) s = void 0;
				else {
					var u = +l[1];
					s = t[0] - u;
				}
			} else s = t == null ? void 0 : t[0];
			if (o === "auto") t != null && (c = Math.max(...t));
			else if (L(o)) c = o;
			else if (typeof o == "function") try {
				t != null && (c = o(t == null ? void 0 : t[1]));
			} catch (e) {}
			else if (typeof o == "string" && tc.test(o)) {
				var d = tc.exec(o);
				if (d == null || d[1] == null || t == null) c = void 0;
				else {
					var f = +d[1];
					c = t[1] + f;
				}
			} else c = t == null ? void 0 : t[1];
			var p = [s, c];
			if (pp(p)) return t == null ? p : mp(p, t, n);
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
function _p(e) {
	return e === 0 ? 1 : Math.floor(new q.default(e).abs().log(10).toNumber()) + 1;
}
function vp(e, t, n) {
	for (var r = new q.default(e), i = 0, a = []; r.lt(t) && i < 1e5;) a.push(r.toNumber()), r = r.add(n), i++;
	return a;
}
//#endregion
//#region node_modules/recharts/es6/util/scale/getNiceTickValues.js
function yp(e, t) {
	return wp(e) || Cp(e, t) || xp(e, t) || bp();
}
function bp() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function xp(e, t) {
	if (e) {
		if (typeof e == "string") return Sp(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? Sp(e, t) : void 0;
	}
}
function Sp(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function Cp(e, t) {
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
function wp(e) {
	if (Array.isArray(e)) return e;
}
var Tp = (e) => {
	var t = yp(e, 2), n = t[0], r = t[1], i = n, a = r;
	return n > r && (i = r, a = n), [i, a];
}, Ep = (e, t, n) => {
	if (e.lte(0)) return new q.default(0);
	var r = _p(e.toNumber()), i = new q.default(10).pow(r), a = e.div(i), o = r === 1 ? .1 : .05, s = new q.default(Math.ceil(a.div(o).toNumber())).add(n).mul(o).mul(i);
	return t ? new q.default(s.toNumber()) : new q.default(Math.ceil(s.toNumber()));
}, Dp = (e, t, n) => {
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
}, Op = (e, t, n) => {
	var r = new q.default(1), i = new q.default(e);
	if (!i.isint() && n) {
		var a = Math.abs(e);
		a < 1 ? (r = new q.default(10).pow(_p(e) - 1), i = new q.default(Math.floor(i.div(r).toNumber())).mul(r)) : a > 1 && (i = new q.default(Math.floor(e)));
	} else e === 0 ? i = new q.default(Math.floor((t - 1) / 2)) : n || (i = new q.default(Math.floor(e)));
	for (var o = Math.floor((t - 1) / 2), s = [], c = 0; c < t; c++) s.push(i.add(new q.default(c - o).mul(r)).toNumber());
	return s;
}, kp = function(e, t, n, r) {
	var i = arguments.length > 4 && arguments[4] !== void 0 ? arguments[4] : 0, a = arguments.length > 5 && arguments[5] !== void 0 ? arguments[5] : Ep;
	if (!Number.isFinite((t - e) / (n - 1))) return {
		step: new q.default(0),
		tickMin: new q.default(0),
		tickMax: new q.default(0)
	};
	var o = a(new q.default(t).sub(e).div(n - 1), r, i), s;
	e <= 0 && t >= 0 ? s = new q.default(0) : (s = new q.default(e).add(t).div(2), s = s.sub(new q.default(s).mod(o)));
	var c = Math.ceil(s.sub(e).div(o).toNumber()), l = Math.ceil(new q.default(t).sub(s).div(o).toNumber()), u = c + l + 1;
	return u > n ? kp(e, t, n, r, i + 1, a) : (u < n && (l = t > 0 ? l + (n - u) : l, c = t > 0 ? c : c + (n - u)), {
		step: o,
		tickMin: s.sub(new q.default(c).mul(o)),
		tickMax: s.add(new q.default(l).mul(o))
	});
}, Ap = function(e) {
	var t = yp(e, 2), n = t[0], r = t[1], i = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : 6, a = arguments.length > 2 && arguments[2] !== void 0 ? arguments[2] : !0, o = arguments.length > 3 && arguments[3] !== void 0 ? arguments[3] : "auto", s = Math.max(i, 2), c = yp(Tp([n, r]), 2), l = c[0], u = c[1];
	if (l === -Infinity || u === Infinity) {
		var d = u === Infinity ? [l, ...Array(i - 1).fill(Infinity)] : [...Array(i - 1).fill(-Infinity), u];
		return n > r ? d.reverse() : d;
	}
	if (l === u) return Op(l, i, a);
	var f = kp(l, u, s, a, 0, o === "snap125" ? Dp : Ep), p = f.step, m = f.tickMin, h = f.tickMax, g = vp(m, h.add(new q.default(.1).mul(p)), p);
	return n > r ? g.reverse() : g;
}, jp = function(e, t) {
	var n = yp(e, 2), r = n[0], i = n[1], a = arguments.length > 2 && arguments[2] !== void 0 ? arguments[2] : !0, o = arguments.length > 3 && arguments[3] !== void 0 ? arguments[3] : "auto", s = yp(Tp([r, i]), 2), c = s[0], l = s[1];
	if (c === -Infinity || l === Infinity) return [r, i];
	if (c === l) return [c];
	var u = o === "snap125" ? Dp : Ep, d = Math.max(t, 2), f = u(new q.default(l).sub(c).div(d - 1), a, 0), p = [...vp(new q.default(c), new q.default(l), f), l];
	if (a === !1) {
		p = p.map((e) => Math.round(e));
		var m = p.length - 1;
		m > 0 && p[m] === p[m - 1] && (p = p.slice(0, m));
	}
	return r > i ? p.reverse() : p;
}, Mp = (e) => e.rootProps.maxBarSize, Np = (e) => e.rootProps.barGap, Pp = (e) => e.rootProps.barCategoryGap, Fp = (e) => e.rootProps.barSize, Ip = (e) => e.rootProps.stackOffset, Lp = (e) => e.rootProps.reverseStackOrder, Rp = (e) => e.options.chartName, zp = (e) => e.rootProps.syncId, Bp = (e) => e.rootProps.syncMethod, Vp = (e) => e.options.eventEmitter, Hp = {
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
}, Up = {
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
	zIndex: Hp.axis
}, Wp = {
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
	zIndex: Hp.axis
}, Gp = (e, t) => {
	if (!(!e || !t)) return e != null && e.reversed ? [t[1], t[0]] : t;
};
//#endregion
//#region node_modules/recharts/es6/util/getAxisTypeBasedOnLayout.js
function Kp(e, t, n) {
	if (n !== "auto") return n;
	if (e != null) return Ws(e, t) ? "category" : "number";
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/polarAxisSelectors.js
function qp(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Jp(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? qp(Object(n), !0).forEach(function(t) {
			Yp(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : qp(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Yp(e, t, n) {
	return (t = Xp(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function Xp(e) {
	var t = Zp(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Zp(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var Qp = {
	allowDataOverflow: Up.allowDataOverflow,
	allowDecimals: Up.allowDecimals,
	allowDuplicatedCategory: !1,
	dataKey: void 0,
	domain: void 0,
	id: Up.angleAxisId,
	includeHidden: !1,
	name: void 0,
	reversed: Up.reversed,
	scale: Up.scale,
	tick: Up.tick,
	tickCount: void 0,
	ticks: void 0,
	type: Up.type,
	unit: void 0,
	niceTicks: "auto"
}, $p = {
	allowDataOverflow: Wp.allowDataOverflow,
	allowDecimals: Wp.allowDecimals,
	allowDuplicatedCategory: Wp.allowDuplicatedCategory,
	dataKey: void 0,
	domain: void 0,
	id: Wp.radiusAxisId,
	includeHidden: Wp.includeHidden,
	name: void 0,
	reversed: Wp.reversed,
	scale: Wp.scale,
	tick: Wp.tick,
	tickCount: Wp.tickCount,
	ticks: void 0,
	type: Wp.type,
	unit: void 0,
	niceTicks: "auto"
}, em = z([(e, t) => {
	if (t != null) return e.polarAxis.angleAxis[t];
}, gl], (e, t) => {
	var n;
	if (e != null) return e;
	var r = (n = Kp(t, "angleAxis", Qp.type)) == null ? "category" : n;
	return Jp(Jp({}, Qp), {}, { type: r });
}), tm = z([(e, t) => e.polarAxis.radiusAxis[t], gl], (e, t) => {
	var n;
	if (e != null) return e;
	var r = (n = Kp(t, "radiusAxis", $p.type)) == null ? "category" : n;
	return Jp(Jp({}, $p), {}, { type: r });
}), nm = (e) => e.polarOptions, rm = z([
	sc,
	cc,
	Cc
], kf), im = z([nm, rm], (e, t) => {
	if (e != null) return hn(e.innerRadius, t, 0);
}), am = z([nm, rm], (e, t) => {
	if (e != null) return hn(e.outerRadius, t, t * .8);
}), om = z([nm], (e) => e == null ? [0, 0] : [e.startAngle, e.endAngle]);
z([em, om], Gp);
var sm = z([
	rm,
	im,
	am
], (e, t, n) => {
	if (!(e == null || t == null || n == null)) return [t, n];
});
z([tm, sm], Gp);
var cm = z([
	K,
	nm,
	im,
	am,
	sc,
	cc
], (e, t, n, r, i, a) => {
	if (!(e !== "centric" && e !== "radial" || t == null || n == null || r == null)) {
		var o = t.cx, s = t.cy, c = t.startAngle, l = t.endAngle;
		return {
			cx: hn(o, i, i / 2),
			cy: hn(s, a, a / 2),
			innerRadius: n,
			outerRadius: r,
			startAngle: c,
			endAngle: l,
			clockWise: !1
		};
	}
}), lm = (e, t) => t, um = (e, t, n) => n;
//#endregion
//#region node_modules/recharts/es6/util/stacks/getStackSeriesIdentifier.js
function dm(e) {
	return e == null ? void 0 : e.id;
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineDisplayedStackedData.js
function fm(e, t, n) {
	var r = t.chartData, i = r === void 0 ? [] : r, a = n.allowDuplicatedCategory, o = n.dataKey, s = /* @__PURE__ */ new Map();
	return e.forEach((e) => {
		var t, n = (t = e.data) == null ? i : t;
		if (!(n == null || n.length === 0)) {
			var r = dm(e);
			n.forEach((t, n) => {
				var i = o == null || a ? n : String(Hs(t, o, null)), c = Hs(t, e.dataKey, 0), l = s.has(i) ? s.get(i) : {};
				Object.assign(l, { [r]: c }), s.set(i, l);
			});
		}
	}), Array.from(s.values());
}
//#endregion
//#region node_modules/recharts/es6/state/types/StackedGraphicalItem.js
function pm(e) {
	return "stackId" in e && e.stackId != null && e.dataKey != null;
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/numberDomainEqualityCheck.js
var mm = (e, t) => e === t ? !0 : e == null || t == null ? !1 : e[0] === t[0] && e[1] === t[1];
//#endregion
//#region node_modules/recharts/es6/state/selectors/arrayEqualityCheck.js
function hm(e, t) {
	return Array.isArray(e) && Array.isArray(t) && e.length === 0 && t.length === 0 ? !0 : e === t;
}
function gm(e, t) {
	if (e.length === t.length) {
		for (var n = 0; n < e.length; n++) if (e[n] !== t[n]) return !1;
		return !0;
	}
	return !1;
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/selectTooltipAxisType.js
var _m = (e) => {
	var t = K(e);
	return t === "horizontal" ? "xAxis" : t === "vertical" ? "yAxis" : t === "centric" ? "angleAxis" : "radiusAxis";
}, vm = (e) => e.tooltip.settings.axisId;
//#endregion
//#region node_modules/recharts/es6/util/scale/RechartsScale.js
function ym(e) {
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
var bm = (e, t) => {
	if (t != null) switch (e) {
		case "linear":
			if (!pp(t)) {
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
function xm(e, t) {
	return e == null || t == null ? NaN : e < t ? -1 : e > t ? 1 : e >= t ? 0 : NaN;
}
//#endregion
//#region node_modules/d3-array/src/descending.js
function Sm(e, t) {
	return e == null || t == null ? NaN : t < e ? -1 : t > e ? 1 : t >= e ? 0 : NaN;
}
//#endregion
//#region node_modules/d3-array/src/bisector.js
function Cm(e) {
	let t, n, r;
	e.length === 2 ? (t = e === xm || e === Sm ? e : wm, n = e, r = e) : (t = xm, n = (t, n) => xm(e(t), n), r = (t, n) => e(t) - n);
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
function wm() {
	return 0;
}
//#endregion
//#region node_modules/d3-array/src/number.js
function Tm(e) {
	return e === null ? NaN : +e;
}
function* Em(e, t) {
	if (t === void 0) for (let t of e) t != null && (t = +t) >= t && (yield t);
	else {
		let n = -1;
		for (let r of e) (r = t(r, ++n, e)) != null && (r = +r) >= r && (yield r);
	}
}
//#endregion
//#region node_modules/d3-array/src/bisect.js
var Dm = Cm(xm), Om = Dm.right;
Dm.left, Cm(Tm).center;
//#endregion
//#region node_modules/internmap/src/index.js
var km = class extends Map {
	constructor(e, t = Nm) {
		if (super(), Object.defineProperties(this, {
			_intern: { value: /* @__PURE__ */ new Map() },
			_key: { value: t }
		}), e != null) for (let [t, n] of e) this.set(t, n);
	}
	get(e) {
		return super.get(Am(this, e));
	}
	has(e) {
		return super.has(Am(this, e));
	}
	set(e, t) {
		return super.set(jm(this, e), t);
	}
	delete(e) {
		return super.delete(Mm(this, e));
	}
};
function Am({ _intern: e, _key: t }, n) {
	let r = t(n);
	return e.has(r) ? e.get(r) : n;
}
function jm({ _intern: e, _key: t }, n) {
	let r = t(n);
	return e.has(r) ? e.get(r) : (e.set(r, n), n);
}
function Mm({ _intern: e, _key: t }, n) {
	let r = t(n);
	return e.has(r) && (n = e.get(r), e.delete(r)), n;
}
function Nm(e) {
	return typeof e == "object" && e ? e.valueOf() : e;
}
//#endregion
//#region node_modules/d3-array/src/sort.js
function Pm(e = xm) {
	if (e === xm) return Fm;
	if (typeof e != "function") throw TypeError("compare is not a function");
	return (t, n) => {
		let r = e(t, n);
		return r || r === 0 ? r : (e(n, n) === 0) - (e(t, t) === 0);
	};
}
function Fm(e, t) {
	return (e == null || !(e >= e)) - (t == null || !(t >= t)) || (e < t ? -1 : +(e > t));
}
//#endregion
//#region node_modules/d3-array/src/ticks.js
var Im = Math.sqrt(50), Lm = Math.sqrt(10), Rm = Math.sqrt(2);
function zm(e, t, n) {
	let r = (t - e) / Math.max(0, n), i = Math.floor(Math.log10(r)), a = r / 10 ** i, o = a >= Im ? 10 : a >= Lm ? 5 : a >= Rm ? 2 : 1, s, c, l;
	return i < 0 ? (l = 10 ** -i / o, s = Math.round(e * l), c = Math.round(t * l), s / l < e && ++s, c / l > t && --c, l = -l) : (l = 10 ** i * o, s = Math.round(e / l), c = Math.round(t / l), s * l < e && ++s, c * l > t && --c), c < s && .5 <= n && n < 2 ? zm(e, t, n * 2) : [
		s,
		c,
		l
	];
}
function Bm(e, t, n) {
	if (t = +t, e = +e, n = +n, !(n > 0)) return [];
	if (e === t) return [e];
	let r = t < e, [i, a, o] = r ? zm(t, e, n) : zm(e, t, n);
	if (!(a >= i)) return [];
	let s = a - i + 1, c = Array(s);
	if (r) if (o < 0) for (let e = 0; e < s; ++e) c[e] = (a - e) / -o;
	else for (let e = 0; e < s; ++e) c[e] = (a - e) * o;
	else if (o < 0) for (let e = 0; e < s; ++e) c[e] = (i + e) / -o;
	else for (let e = 0; e < s; ++e) c[e] = (i + e) * o;
	return c;
}
function Vm(e, t, n) {
	return t = +t, e = +e, n = +n, zm(e, t, n)[2];
}
function Hm(e, t, n) {
	t = +t, e = +e, n = +n;
	let r = t < e, i = r ? Vm(t, e, n) : Vm(e, t, n);
	return (r ? -1 : 1) * (i < 0 ? 1 / -i : i);
}
//#endregion
//#region node_modules/d3-array/src/max.js
function Um(e, t) {
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
function Wm(e, t) {
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
function Gm(e, t, n = 0, r = Infinity, i) {
	if (t = Math.floor(t), n = Math.floor(Math.max(0, n)), r = Math.floor(Math.min(e.length - 1, r)), !(n <= t && t <= r)) return e;
	for (i = i === void 0 ? Fm : Pm(i); r > n;) {
		if (r - n > 600) {
			let a = r - n + 1, o = t - n + 1, s = Math.log(a), c = .5 * Math.exp(2 * s / 3), l = .5 * Math.sqrt(s * c * (a - c) / a) * (o - a / 2 < 0 ? -1 : 1), u = Math.max(n, Math.floor(t - o * c / a + l)), d = Math.min(r, Math.floor(t + (a - o) * c / a + l));
			Gm(e, t, u, d, i);
		}
		let a = e[t], o = n, s = r;
		for (Km(e, n, t), i(e[r], a) > 0 && Km(e, n, r); o < s;) {
			for (Km(e, o, s), ++o, --s; i(e[o], a) < 0;) ++o;
			for (; i(e[s], a) > 0;) --s;
		}
		i(e[n], a) === 0 ? Km(e, n, s) : (++s, Km(e, s, r)), s <= t && (n = s + 1), t <= s && (r = s - 1);
	}
	return e;
}
function Km(e, t, n) {
	let r = e[t];
	e[t] = e[n], e[n] = r;
}
//#endregion
//#region node_modules/d3-array/src/quantile.js
function qm(e, t, n) {
	if (e = Float64Array.from(Em(e, n)), !(!(r = e.length) || isNaN(t = +t))) {
		if (t <= 0 || r < 2) return Wm(e);
		if (t >= 1) return Um(e);
		var r, i = (r - 1) * t, a = Math.floor(i), o = Um(Gm(e, a).subarray(0, a + 1));
		return o + (Wm(e.subarray(a + 1)) - o) * (i - a);
	}
}
function Jm(e, t, n = Tm) {
	if (!(!(r = e.length) || isNaN(t = +t))) {
		if (t <= 0 || r < 2) return +n(e[0], 0, e);
		if (t >= 1) return +n(e[r - 1], r - 1, e);
		var r, i = (r - 1) * t, a = Math.floor(i), o = +n(e[a], a, e);
		return o + (+n(e[a + 1], a + 1, e) - o) * (i - a);
	}
}
//#endregion
//#region node_modules/d3-array/src/range.js
function Ym(e, t, n) {
	e = +e, t = +t, n = (i = arguments.length) < 2 ? (t = e, e = 0, 1) : i < 3 ? 1 : +n;
	for (var r = -1, i = Math.max(0, Math.ceil((t - e) / n)) | 0, a = Array(i); ++r < i;) a[r] = e + r * n;
	return a;
}
//#endregion
//#region node_modules/d3-scale/src/init.js
function Xm(e, t) {
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
function Zm(e, t) {
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
var Qm = Symbol("implicit");
function $m() {
	var e = new km(), t = [], n = [], r = Qm;
	function i(i) {
		let a = e.get(i);
		if (a === void 0) {
			if (r !== Qm) return r;
			e.set(i, a = t.push(i) - 1);
		}
		return n[a % n.length];
	}
	return i.domain = function(n) {
		if (!arguments.length) return t.slice();
		t = [], e = new km();
		for (let r of n) e.has(r) || e.set(r, t.push(r) - 1);
		return i;
	}, i.range = function(e) {
		return arguments.length ? (n = Array.from(e), i) : n.slice();
	}, i.unknown = function(e) {
		return arguments.length ? (r = e, i) : r;
	}, i.copy = function() {
		return $m(t, n).unknown(r);
	}, Xm.apply(i, arguments), i;
}
//#endregion
//#region node_modules/d3-scale/src/band.js
function eh() {
	var e = $m().unknown(void 0), t = e.domain, n = e.range, r = 0, i = 1, a, o, s = !1, c = 0, l = 0, u = .5;
	delete e.unknown;
	function d() {
		var e = t().length, d = i < r, f = d ? i : r, p = d ? r : i;
		a = (p - f) / Math.max(1, e - c + l * 2), s && (a = Math.floor(a)), f += (p - f - a * (e - c)) * u, o = a * (1 - c), s && (f = Math.round(f), o = Math.round(o));
		var m = Ym(e).map(function(e) {
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
		return eh(t(), [r, i]).round(s).paddingInner(c).paddingOuter(l).align(u);
	}, Xm.apply(d(), arguments);
}
function th(e) {
	var t = e.copy;
	return e.padding = e.paddingOuter, delete e.paddingInner, delete e.paddingOuter, e.copy = function() {
		return th(t());
	}, e;
}
function nh() {
	return th(eh.apply(null, arguments).paddingInner(1));
}
//#endregion
//#region node_modules/d3-color/src/define.js
function rh(e, t, n) {
	e.prototype = t.prototype = n, n.constructor = e;
}
function ih(e, t) {
	var n = Object.create(e.prototype);
	for (var r in t) n[r] = t[r];
	return n;
}
//#endregion
//#region node_modules/d3-color/src/color.js
function ah() {}
var oh = .7, sh = 1 / oh, ch = "\\s*([+-]?\\d+)\\s*", lh = "\\s*([+-]?(?:\\d*\\.)?\\d+(?:[eE][+-]?\\d+)?)\\s*", uh = "\\s*([+-]?(?:\\d*\\.)?\\d+(?:[eE][+-]?\\d+)?)%\\s*", dh = /^#([0-9a-f]{3,8})$/, fh = RegExp(`^rgb\\(${ch},${ch},${ch}\\)$`), ph = RegExp(`^rgb\\(${uh},${uh},${uh}\\)$`), mh = RegExp(`^rgba\\(${ch},${ch},${ch},${lh}\\)$`), hh = RegExp(`^rgba\\(${uh},${uh},${uh},${lh}\\)$`), gh = RegExp(`^hsl\\(${lh},${uh},${uh}\\)$`), _h = RegExp(`^hsla\\(${lh},${uh},${uh},${lh}\\)$`), vh = {
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
rh(ah, Ch, {
	copy(e) {
		return Object.assign(new this.constructor(), this, e);
	},
	displayable() {
		return this.rgb().displayable();
	},
	hex: yh,
	formatHex: yh,
	formatHex8: bh,
	formatHsl: xh,
	formatRgb: Sh,
	toString: Sh
});
function yh() {
	return this.rgb().formatHex();
}
function bh() {
	return this.rgb().formatHex8();
}
function xh() {
	return Ih(this).formatHsl();
}
function Sh() {
	return this.rgb().formatRgb();
}
function Ch(e) {
	var t, n;
	return e = (e + "").trim().toLowerCase(), (t = dh.exec(e)) ? (n = t[1].length, t = parseInt(t[1], 16), n === 6 ? wh(t) : n === 3 ? new Oh(t >> 8 & 15 | t >> 4 & 240, t >> 4 & 15 | t & 240, (t & 15) << 4 | t & 15, 1) : n === 8 ? Th(t >> 24 & 255, t >> 16 & 255, t >> 8 & 255, (t & 255) / 255) : n === 4 ? Th(t >> 12 & 15 | t >> 8 & 240, t >> 8 & 15 | t >> 4 & 240, t >> 4 & 15 | t & 240, ((t & 15) << 4 | t & 15) / 255) : null) : (t = fh.exec(e)) ? new Oh(t[1], t[2], t[3], 1) : (t = ph.exec(e)) ? new Oh(t[1] * 255 / 100, t[2] * 255 / 100, t[3] * 255 / 100, 1) : (t = mh.exec(e)) ? Th(t[1], t[2], t[3], t[4]) : (t = hh.exec(e)) ? Th(t[1] * 255 / 100, t[2] * 255 / 100, t[3] * 255 / 100, t[4]) : (t = gh.exec(e)) ? Fh(t[1], t[2] / 100, t[3] / 100, 1) : (t = _h.exec(e)) ? Fh(t[1], t[2] / 100, t[3] / 100, t[4]) : vh.hasOwnProperty(e) ? wh(vh[e]) : e === "transparent" ? new Oh(NaN, NaN, NaN, 0) : null;
}
function wh(e) {
	return new Oh(e >> 16 & 255, e >> 8 & 255, e & 255, 1);
}
function Th(e, t, n, r) {
	return r <= 0 && (e = t = n = NaN), new Oh(e, t, n, r);
}
function Eh(e) {
	return e instanceof ah || (e = Ch(e)), e ? (e = e.rgb(), new Oh(e.r, e.g, e.b, e.opacity)) : new Oh();
}
function Dh(e, t, n, r) {
	return arguments.length === 1 ? Eh(e) : new Oh(e, t, n, r == null ? 1 : r);
}
function Oh(e, t, n, r) {
	this.r = +e, this.g = +t, this.b = +n, this.opacity = +r;
}
rh(Oh, Dh, ih(ah, {
	brighter(e) {
		return e = e == null ? sh : sh ** +e, new Oh(this.r * e, this.g * e, this.b * e, this.opacity);
	},
	darker(e) {
		return e = e == null ? oh : oh ** +e, new Oh(this.r * e, this.g * e, this.b * e, this.opacity);
	},
	rgb() {
		return this;
	},
	clamp() {
		return new Oh(Nh(this.r), Nh(this.g), Nh(this.b), Mh(this.opacity));
	},
	displayable() {
		return -.5 <= this.r && this.r < 255.5 && -.5 <= this.g && this.g < 255.5 && -.5 <= this.b && this.b < 255.5 && 0 <= this.opacity && this.opacity <= 1;
	},
	hex: kh,
	formatHex: kh,
	formatHex8: Ah,
	formatRgb: jh,
	toString: jh
}));
function kh() {
	return `#${Ph(this.r)}${Ph(this.g)}${Ph(this.b)}`;
}
function Ah() {
	return `#${Ph(this.r)}${Ph(this.g)}${Ph(this.b)}${Ph((isNaN(this.opacity) ? 1 : this.opacity) * 255)}`;
}
function jh() {
	let e = Mh(this.opacity);
	return `${e === 1 ? "rgb(" : "rgba("}${Nh(this.r)}, ${Nh(this.g)}, ${Nh(this.b)}${e === 1 ? ")" : `, ${e})`}`;
}
function Mh(e) {
	return isNaN(e) ? 1 : Math.max(0, Math.min(1, e));
}
function Nh(e) {
	return Math.max(0, Math.min(255, Math.round(e) || 0));
}
function Ph(e) {
	return e = Nh(e), (e < 16 ? "0" : "") + e.toString(16);
}
function Fh(e, t, n, r) {
	return r <= 0 ? e = t = n = NaN : n <= 0 || n >= 1 ? e = t = NaN : t <= 0 && (e = NaN), new Rh(e, t, n, r);
}
function Ih(e) {
	if (e instanceof Rh) return new Rh(e.h, e.s, e.l, e.opacity);
	if (e instanceof ah || (e = Ch(e)), !e) return new Rh();
	if (e instanceof Rh) return e;
	e = e.rgb();
	var t = e.r / 255, n = e.g / 255, r = e.b / 255, i = Math.min(t, n, r), a = Math.max(t, n, r), o = NaN, s = a - i, c = (a + i) / 2;
	return s ? (o = t === a ? (n - r) / s + (n < r) * 6 : n === a ? (r - t) / s + 2 : (t - n) / s + 4, s /= c < .5 ? a + i : 2 - a - i, o *= 60) : s = c > 0 && c < 1 ? 0 : o, new Rh(o, s, c, e.opacity);
}
function Lh(e, t, n, r) {
	return arguments.length === 1 ? Ih(e) : new Rh(e, t, n, r == null ? 1 : r);
}
function Rh(e, t, n, r) {
	this.h = +e, this.s = +t, this.l = +n, this.opacity = +r;
}
rh(Rh, Lh, ih(ah, {
	brighter(e) {
		return e = e == null ? sh : sh ** +e, new Rh(this.h, this.s, this.l * e, this.opacity);
	},
	darker(e) {
		return e = e == null ? oh : oh ** +e, new Rh(this.h, this.s, this.l * e, this.opacity);
	},
	rgb() {
		var e = this.h % 360 + (this.h < 0) * 360, t = isNaN(e) || isNaN(this.s) ? 0 : this.s, n = this.l, r = n + (n < .5 ? n : 1 - n) * t, i = 2 * n - r;
		return new Oh(Vh(e >= 240 ? e - 240 : e + 120, i, r), Vh(e, i, r), Vh(e < 120 ? e + 240 : e - 120, i, r), this.opacity);
	},
	clamp() {
		return new Rh(zh(this.h), Bh(this.s), Bh(this.l), Mh(this.opacity));
	},
	displayable() {
		return (0 <= this.s && this.s <= 1 || isNaN(this.s)) && 0 <= this.l && this.l <= 1 && 0 <= this.opacity && this.opacity <= 1;
	},
	formatHsl() {
		let e = Mh(this.opacity);
		return `${e === 1 ? "hsl(" : "hsla("}${zh(this.h)}, ${Bh(this.s) * 100}%, ${Bh(this.l) * 100}%${e === 1 ? ")" : `, ${e})`}`;
	}
}));
function zh(e) {
	return e = (e || 0) % 360, e < 0 ? e + 360 : e;
}
function Bh(e) {
	return Math.max(0, Math.min(1, e || 0));
}
function Vh(e, t, n) {
	return (e < 60 ? t + (n - t) * e / 60 : e < 180 ? n : e < 240 ? t + (n - t) * (240 - e) / 60 : t) * 255;
}
//#endregion
//#region node_modules/d3-interpolate/src/constant.js
var Hh = (e) => () => e;
//#endregion
//#region node_modules/d3-interpolate/src/color.js
function Uh(e, t) {
	return function(n) {
		return e + n * t;
	};
}
function Wh(e, t, n) {
	return e **= +n, t = t ** +n - e, n = 1 / n, function(r) {
		return (e + r * t) ** +n;
	};
}
function Gh(e) {
	return (e = +e) == 1 ? Kh : function(t, n) {
		return n - t ? Wh(t, n, e) : Hh(isNaN(t) ? n : t);
	};
}
function Kh(e, t) {
	var n = t - e;
	return n ? Uh(e, n) : Hh(isNaN(e) ? t : e);
}
//#endregion
//#region node_modules/d3-interpolate/src/rgb.js
var qh = (function e(t) {
	var n = Gh(t);
	function r(e, t) {
		var r = n((e = Dh(e)).r, (t = Dh(t)).r), i = n(e.g, t.g), a = n(e.b, t.b), o = Kh(e.opacity, t.opacity);
		return function(t) {
			return e.r = r(t), e.g = i(t), e.b = a(t), e.opacity = o(t), e + "";
		};
	}
	return r.gamma = e, r;
})(1);
//#endregion
//#region node_modules/d3-interpolate/src/numberArray.js
function Jh(e, t) {
	t || (t = []);
	var n = e ? Math.min(t.length, e.length) : 0, r = t.slice(), i;
	return function(a) {
		for (i = 0; i < n; ++i) r[i] = e[i] * (1 - a) + t[i] * a;
		return r;
	};
}
function Yh(e) {
	return ArrayBuffer.isView(e) && !(e instanceof DataView);
}
//#endregion
//#region node_modules/d3-interpolate/src/array.js
function Xh(e, t) {
	var n = t ? t.length : 0, r = e ? Math.min(n, e.length) : 0, i = Array(r), a = Array(n), o;
	for (o = 0; o < r; ++o) i[o] = ag(e[o], t[o]);
	for (; o < n; ++o) a[o] = t[o];
	return function(e) {
		for (o = 0; o < r; ++o) a[o] = i[o](e);
		return a;
	};
}
//#endregion
//#region node_modules/d3-interpolate/src/date.js
function Zh(e, t) {
	var n = /* @__PURE__ */ new Date();
	return e = +e, t = +t, function(r) {
		return n.setTime(e * (1 - r) + t * r), n;
	};
}
//#endregion
//#region node_modules/d3-interpolate/src/number.js
function Qh(e, t) {
	return e = +e, t = +t, function(n) {
		return e * (1 - n) + t * n;
	};
}
//#endregion
//#region node_modules/d3-interpolate/src/object.js
function $h(e, t) {
	var n = {}, r = {}, i;
	for (i in (typeof e != "object" || !e) && (e = {}), (typeof t != "object" || !t) && (t = {}), t) i in e ? n[i] = ag(e[i], t[i]) : r[i] = t[i];
	return function(e) {
		for (i in n) r[i] = n[i](e);
		return r;
	};
}
//#endregion
//#region node_modules/d3-interpolate/src/string.js
var eg = /[-+]?(?:\d+\.?\d*|\.?\d+)(?:[eE][-+]?\d+)?/g, tg = new RegExp(eg.source, "g");
function ng(e) {
	return function() {
		return e;
	};
}
function rg(e) {
	return function(t) {
		return e(t) + "";
	};
}
function ig(e, t) {
	var n = eg.lastIndex = tg.lastIndex = 0, r, i, a, o = -1, s = [], c = [];
	for (e += "", t += ""; (r = eg.exec(e)) && (i = tg.exec(t));) (a = i.index) > n && (a = t.slice(n, a), s[o] ? s[o] += a : s[++o] = a), (r = r[0]) === (i = i[0]) ? s[o] ? s[o] += i : s[++o] = i : (s[++o] = null, c.push({
		i: o,
		x: Qh(r, i)
	})), n = tg.lastIndex;
	return n < t.length && (a = t.slice(n), s[o] ? s[o] += a : s[++o] = a), s.length < 2 ? c[0] ? rg(c[0].x) : ng(t) : (t = c.length, function(e) {
		for (var n = 0, r; n < t; ++n) s[(r = c[n]).i] = r.x(e);
		return s.join("");
	});
}
//#endregion
//#region node_modules/d3-interpolate/src/value.js
function ag(e, t) {
	var n = typeof t, r;
	return t == null || n === "boolean" ? Hh(t) : (n === "number" ? Qh : n === "string" ? (r = Ch(t)) ? (t = r, qh) : ig : t instanceof Ch ? qh : t instanceof Date ? Zh : Yh(t) ? Jh : Array.isArray(t) ? Xh : typeof t.valueOf != "function" && typeof t.toString != "function" || isNaN(t) ? $h : Qh)(e, t);
}
//#endregion
//#region node_modules/d3-interpolate/src/round.js
function og(e, t) {
	return e = +e, t = +t, function(n) {
		return Math.round(e * (1 - n) + t * n);
	};
}
//#endregion
//#region node_modules/d3-interpolate/src/piecewise.js
function sg(e, t) {
	t === void 0 && (t = e, e = ag);
	for (var n = 0, r = t.length - 1, i = t[0], a = Array(r < 0 ? 0 : r); n < r;) a[n] = e(i, i = t[++n]);
	return function(e) {
		var t = Math.max(0, Math.min(r - 1, Math.floor(e *= r)));
		return a[t](e - t);
	};
}
//#endregion
//#region node_modules/d3-scale/src/constant.js
function cg(e) {
	return function() {
		return e;
	};
}
//#endregion
//#region node_modules/d3-scale/src/number.js
function lg(e) {
	return +e;
}
//#endregion
//#region node_modules/d3-scale/src/continuous.js
var ug = [0, 1];
function dg(e) {
	return e;
}
function fg(e, t) {
	return (t -= e = +e) ? function(n) {
		return (n - e) / t;
	} : cg(isNaN(t) ? NaN : .5);
}
function pg(e, t) {
	var n;
	return e > t && (n = e, e = t, t = n), function(n) {
		return Math.max(e, Math.min(t, n));
	};
}
function mg(e, t, n) {
	var r = e[0], i = e[1], a = t[0], o = t[1];
	return i < r ? (r = fg(i, r), a = n(o, a)) : (r = fg(r, i), a = n(a, o)), function(e) {
		return a(r(e));
	};
}
function hg(e, t, n) {
	var r = Math.min(e.length, t.length) - 1, i = Array(r), a = Array(r), o = -1;
	for (e[r] < e[0] && (e = e.slice().reverse(), t = t.slice().reverse()); ++o < r;) i[o] = fg(e[o], e[o + 1]), a[o] = n(t[o], t[o + 1]);
	return function(t) {
		var n = Om(e, t, 1, r) - 1;
		return a[n](i[n](t));
	};
}
function gg(e, t) {
	return t.domain(e.domain()).range(e.range()).interpolate(e.interpolate()).clamp(e.clamp()).unknown(e.unknown());
}
function _g() {
	var e = ug, t = ug, n = ag, r, i, a, o = dg, s, c, l;
	function u() {
		var n = Math.min(e.length, t.length);
		return o !== dg && (o = pg(e[0], e[n - 1])), s = n > 2 ? hg : mg, c = l = null, d;
	}
	function d(i) {
		return i == null || isNaN(i = +i) ? a : (c || (c = s(e.map(r), t, n)))(r(o(i)));
	}
	return d.invert = function(n) {
		return o(i((l || (l = s(t, e.map(r), Qh)))(n)));
	}, d.domain = function(t) {
		return arguments.length ? (e = Array.from(t, lg), u()) : e.slice();
	}, d.range = function(e) {
		return arguments.length ? (t = Array.from(e), u()) : t.slice();
	}, d.rangeRound = function(e) {
		return t = Array.from(e), n = og, u();
	}, d.clamp = function(e) {
		return arguments.length ? (o = e ? !0 : dg, u()) : o !== dg;
	}, d.interpolate = function(e) {
		return arguments.length ? (n = e, u()) : n;
	}, d.unknown = function(e) {
		return arguments.length ? (a = e, d) : a;
	}, function(e, t) {
		return r = e, i = t, u();
	};
}
function vg() {
	return _g()(dg, dg);
}
//#endregion
//#region node_modules/d3-format/src/formatDecimal.js
function yg(e) {
	return Math.abs(e = Math.round(e)) >= 1e21 ? e.toLocaleString("en").replace(/,/g, "") : e.toString(10);
}
function bg(e, t) {
	if (!isFinite(e) || e === 0) return null;
	var n = (e = t ? e.toExponential(t - 1) : e.toExponential()).indexOf("e"), r = e.slice(0, n);
	return [r.length > 1 ? r[0] + r.slice(2) : r, +e.slice(n + 1)];
}
//#endregion
//#region node_modules/d3-format/src/exponent.js
function xg(e) {
	return e = bg(Math.abs(e)), e ? e[1] : NaN;
}
//#endregion
//#region node_modules/d3-format/src/formatGroup.js
function Sg(e, t) {
	return function(n, r) {
		for (var i = n.length, a = [], o = 0, s = e[0], c = 0; i > 0 && s > 0 && (c + s + 1 > r && (s = Math.max(1, r - c)), a.push(n.substring(i -= s, i + s)), !((c += s + 1) > r));) s = e[o = (o + 1) % e.length];
		return a.reverse().join(t);
	};
}
//#endregion
//#region node_modules/d3-format/src/formatNumerals.js
function Cg(e) {
	return function(t) {
		return t.replace(/[0-9]/g, function(t) {
			return e[+t];
		});
	};
}
//#endregion
//#region node_modules/d3-format/src/formatSpecifier.js
var wg = /^(?:(.)?([<>=^]))?([+\-( ])?([$#])?(0)?(\d+)?(,)?(\.\d+)?(~)?([a-z%])?$/i;
function Tg(e) {
	if (!(t = wg.exec(e))) throw Error("invalid format: " + e);
	var t;
	return new Eg({
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
Tg.prototype = Eg.prototype;
function Eg(e) {
	this.fill = e.fill === void 0 ? " " : e.fill + "", this.align = e.align === void 0 ? ">" : e.align + "", this.sign = e.sign === void 0 ? "-" : e.sign + "", this.symbol = e.symbol === void 0 ? "" : e.symbol + "", this.zero = !!e.zero, this.width = e.width === void 0 ? void 0 : +e.width, this.comma = !!e.comma, this.precision = e.precision === void 0 ? void 0 : +e.precision, this.trim = !!e.trim, this.type = e.type === void 0 ? "" : e.type + "";
}
Eg.prototype.toString = function() {
	return this.fill + this.align + this.sign + this.symbol + (this.zero ? "0" : "") + (this.width === void 0 ? "" : Math.max(1, this.width | 0)) + (this.comma ? "," : "") + (this.precision === void 0 ? "" : "." + Math.max(0, this.precision | 0)) + (this.trim ? "~" : "") + this.type;
};
//#endregion
//#region node_modules/d3-format/src/formatTrim.js
function Dg(e) {
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
var Og;
function kg(e, t) {
	var n = bg(e, t);
	if (!n) return Og = void 0, e.toPrecision(t);
	var r = n[0], i = n[1], a = i - (Og = Math.max(-8, Math.min(8, Math.floor(i / 3))) * 3) + 1, o = r.length;
	return a === o ? r : a > o ? r + Array(a - o + 1).join("0") : a > 0 ? r.slice(0, a) + "." + r.slice(a) : "0." + Array(1 - a).join("0") + bg(e, Math.max(0, t + a - 1))[0];
}
//#endregion
//#region node_modules/d3-format/src/formatRounded.js
function Ag(e, t) {
	var n = bg(e, t);
	if (!n) return e + "";
	var r = n[0], i = n[1];
	return i < 0 ? "0." + Array(-i).join("0") + r : r.length > i + 1 ? r.slice(0, i + 1) + "." + r.slice(i + 1) : r + Array(i - r.length + 2).join("0");
}
//#endregion
//#region node_modules/d3-format/src/formatTypes.js
var jg = {
	"%": (e, t) => (e * 100).toFixed(t),
	b: (e) => Math.round(e).toString(2),
	c: (e) => e + "",
	d: yg,
	e: (e, t) => e.toExponential(t),
	f: (e, t) => e.toFixed(t),
	g: (e, t) => e.toPrecision(t),
	o: (e) => Math.round(e).toString(8),
	p: (e, t) => Ag(e * 100, t),
	r: Ag,
	s: kg,
	X: (e) => Math.round(e).toString(16).toUpperCase(),
	x: (e) => Math.round(e).toString(16)
};
//#endregion
//#region node_modules/d3-format/src/identity.js
function Mg(e) {
	return e;
}
//#endregion
//#region node_modules/d3-format/src/locale.js
var Ng = Array.prototype.map, Pg = [
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
function Fg(e) {
	var t = e.grouping === void 0 || e.thousands === void 0 ? Mg : Sg(Ng.call(e.grouping, Number), e.thousands + ""), n = e.currency === void 0 ? "" : e.currency[0] + "", r = e.currency === void 0 ? "" : e.currency[1] + "", i = e.decimal === void 0 ? "." : e.decimal + "", a = e.numerals === void 0 ? Mg : Cg(Ng.call(e.numerals, String)), o = e.percent === void 0 ? "%" : e.percent + "", s = e.minus === void 0 ? "−" : e.minus + "", c = e.nan === void 0 ? "NaN" : e.nan + "";
	function l(e, l) {
		e = Tg(e);
		var u = e.fill, d = e.align, f = e.sign, p = e.symbol, m = e.zero, h = e.width, g = e.comma, _ = e.precision, v = e.trim, y = e.type;
		y === "n" ? (g = !0, y = "g") : jg[y] || (_ === void 0 && (_ = 12), v = !0, y = "g"), (m || u === "0" && d === "=") && (m = !0, u = "0", d = "=");
		var b = (l && l.prefix !== void 0 ? l.prefix : "") + (p === "$" ? n : p === "#" && /[boxX]/.test(y) ? "0" + y.toLowerCase() : ""), x = (p === "$" ? r : /[%p]/.test(y) ? o : "") + (l && l.suffix !== void 0 ? l.suffix : ""), S = jg[y], C = /[defgprs%]/.test(y);
		_ = _ === void 0 ? 6 : /[gprs]/.test(y) ? Math.max(1, Math.min(21, _)) : Math.max(0, Math.min(20, _));
		function w(e) {
			var n = b, r = x, o, l, p;
			if (y === "c") r = S(e) + r, e = "";
			else {
				e = +e;
				var w = e < 0 || 1 / e < 0;
				if (e = isNaN(e) ? c : S(Math.abs(e), _), v && (e = Dg(e)), w && +e == 0 && f !== "+" && (w = !1), n = (w ? f === "(" ? f : s : f === "-" || f === "(" ? "" : f) + n, r = (y === "s" && !isNaN(e) && Og !== void 0 ? Pg[8 + Og / 3] : "") + r + (w && f === "(" ? ")" : ""), C) {
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
		var n = Math.max(-8, Math.min(8, Math.floor(xg(t) / 3))) * 3, r = 10 ** -n, i = l((e = Tg(e), e.type = "f", e), { suffix: Pg[8 + n / 3] });
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
var Ig, Lg, Rg;
zg({
	thousands: ",",
	grouping: [3],
	currency: ["$", ""]
});
function zg(e) {
	return Ig = Fg(e), Lg = Ig.format, Rg = Ig.formatPrefix, Ig;
}
//#endregion
//#region node_modules/d3-format/src/precisionFixed.js
function Bg(e) {
	return Math.max(0, -xg(Math.abs(e)));
}
//#endregion
//#region node_modules/d3-format/src/precisionPrefix.js
function Vg(e, t) {
	return Math.max(0, Math.max(-8, Math.min(8, Math.floor(xg(t) / 3))) * 3 - xg(Math.abs(e)));
}
//#endregion
//#region node_modules/d3-format/src/precisionRound.js
function Hg(e, t) {
	return e = Math.abs(e), t = Math.abs(t) - e, Math.max(0, xg(t) - xg(e)) + 1;
}
//#endregion
//#region node_modules/d3-scale/src/tickFormat.js
function Ug(e, t, n, r) {
	var i = Hm(e, t, n), a;
	switch (r = Tg(r == null ? ",f" : r), r.type) {
		case "s":
			var o = Math.max(Math.abs(e), Math.abs(t));
			return r.precision == null && !isNaN(a = Vg(i, o)) && (r.precision = a), Rg(r, o);
		case "":
		case "e":
		case "g":
		case "p":
		case "r":
			r.precision == null && !isNaN(a = Hg(i, Math.max(Math.abs(e), Math.abs(t)))) && (r.precision = a - (r.type === "e"));
			break;
		case "f":
		case "%":
			r.precision == null && !isNaN(a = Bg(i)) && (r.precision = a - (r.type === "%") * 2);
			break;
	}
	return Lg(r);
}
//#endregion
//#region node_modules/d3-scale/src/linear.js
function Wg(e) {
	var t = e.domain;
	return e.ticks = function(e) {
		var n = t();
		return Bm(n[0], n[n.length - 1], e == null ? 10 : e);
	}, e.tickFormat = function(e, n) {
		var r = t();
		return Ug(r[0], r[r.length - 1], e == null ? 10 : e, n);
	}, e.nice = function(n) {
		n == null && (n = 10);
		var r = t(), i = 0, a = r.length - 1, o = r[i], s = r[a], c, l, u = 10;
		for (s < o && (l = o, o = s, s = l, l = i, i = a, a = l); u-- > 0;) {
			if (l = Vm(o, s, n), l === c) return r[i] = o, r[a] = s, t(r);
			if (l > 0) o = Math.floor(o / l) * l, s = Math.ceil(s / l) * l;
			else if (l < 0) o = Math.ceil(o * l) / l, s = Math.floor(s * l) / l;
			else break;
			c = l;
		}
		return e;
	}, e;
}
function Gg() {
	var e = vg();
	return e.copy = function() {
		return gg(e, Gg());
	}, Xm.apply(e, arguments), Wg(e);
}
//#endregion
//#region node_modules/d3-scale/src/identity.js
function Kg(e) {
	var t;
	function n(e) {
		return e == null || isNaN(e = +e) ? t : e;
	}
	return n.invert = n, n.domain = n.range = function(t) {
		return arguments.length ? (e = Array.from(t, lg), n) : e.slice();
	}, n.unknown = function(e) {
		return arguments.length ? (t = e, n) : t;
	}, n.copy = function() {
		return Kg(e).unknown(t);
	}, e = arguments.length ? Array.from(e, lg) : [0, 1], Wg(n);
}
//#endregion
//#region node_modules/d3-scale/src/nice.js
function qg(e, t) {
	e = e.slice();
	var n = 0, r = e.length - 1, i = e[n], a = e[r], o;
	return a < i && (o = n, n = r, r = o, o = i, i = a, a = o), e[n] = t.floor(i), e[r] = t.ceil(a), e;
}
//#endregion
//#region node_modules/d3-scale/src/log.js
function Jg(e) {
	return Math.log(e);
}
function Yg(e) {
	return Math.exp(e);
}
function Xg(e) {
	return -Math.log(-e);
}
function Zg(e) {
	return -Math.exp(-e);
}
function Qg(e) {
	return isFinite(e) ? +("1e" + e) : e < 0 ? 0 : e;
}
function $g(e) {
	return e === 10 ? Qg : e === Math.E ? Math.exp : (t) => e ** +t;
}
function e_(e) {
	return e === Math.E ? Math.log : e === 10 && Math.log10 || e === 2 && Math.log2 || (e = Math.log(e), (t) => Math.log(t) / e);
}
function t_(e) {
	return (t, n) => -e(-t, n);
}
function n_(e) {
	let t = e(Jg, Yg), n = t.domain, r = 10, i, a;
	function o() {
		return i = e_(r), a = $g(r), n()[0] < 0 ? (i = t_(i), a = t_(a), e(Xg, Zg)) : e(Jg, Yg), t;
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
			m.length * 2 < p && (m = Bm(o, s, p));
		} else m = Bm(l, u, Math.min(u - l, p)).map(a);
		return c ? m.reverse() : m;
	}, t.tickFormat = (e, n) => {
		if (e == null && (e = 10), n == null && (n = r === 10 ? "s" : ","), typeof n != "function" && (!(r % 1) && (n = Tg(n)).precision == null && (n.trim = !0), n = Lg(n)), e === Infinity) return n;
		let o = Math.max(1, r * e / t.ticks().length);
		return (e) => {
			let t = e / a(Math.round(i(e)));
			return t * r < r - .5 && (t *= r), t <= o ? n(e) : "";
		};
	}, t.nice = () => n(qg(n(), {
		floor: (e) => a(Math.floor(i(e))),
		ceil: (e) => a(Math.ceil(i(e)))
	})), t;
}
function r_() {
	let e = n_(_g()).domain([1, 10]);
	return e.copy = () => gg(e, r_()).base(e.base()), Xm.apply(e, arguments), e;
}
//#endregion
//#region node_modules/d3-scale/src/symlog.js
function i_(e) {
	return function(t) {
		return Math.sign(t) * Math.log1p(Math.abs(t / e));
	};
}
function a_(e) {
	return function(t) {
		return Math.sign(t) * Math.expm1(Math.abs(t)) * e;
	};
}
function o_(e) {
	var t = 1, n = e(i_(t), a_(t));
	return n.constant = function(n) {
		return arguments.length ? e(i_(t = +n), a_(t)) : t;
	}, Wg(n);
}
function s_() {
	var e = o_(_g());
	return e.copy = function() {
		return gg(e, s_()).constant(e.constant());
	}, Xm.apply(e, arguments);
}
//#endregion
//#region node_modules/d3-scale/src/pow.js
function c_(e) {
	return function(t) {
		return t < 0 ? -((-t) ** +e) : t ** +e;
	};
}
function l_(e) {
	return e < 0 ? -Math.sqrt(-e) : Math.sqrt(e);
}
function u_(e) {
	return e < 0 ? -e * e : e * e;
}
function d_(e) {
	var t = e(dg, dg), n = 1;
	function r() {
		return n === 1 ? e(dg, dg) : n === .5 ? e(l_, u_) : e(c_(n), c_(1 / n));
	}
	return t.exponent = function(e) {
		return arguments.length ? (n = +e, r()) : n;
	}, Wg(t);
}
function f_() {
	var e = d_(_g());
	return e.copy = function() {
		return gg(e, f_()).exponent(e.exponent());
	}, Xm.apply(e, arguments), e;
}
function p_() {
	return f_.apply(null, arguments).exponent(.5);
}
//#endregion
//#region node_modules/d3-scale/src/radial.js
function m_(e) {
	return Math.sign(e) * e * e;
}
function h_(e) {
	return Math.sign(e) * Math.sqrt(Math.abs(e));
}
function g_() {
	var e = vg(), t = [0, 1], n = !1, r;
	function i(t) {
		var i = h_(e(t));
		return isNaN(i) ? r : n ? Math.round(i) : i;
	}
	return i.invert = function(t) {
		return e.invert(m_(t));
	}, i.domain = function(t) {
		return arguments.length ? (e.domain(t), i) : e.domain();
	}, i.range = function(n) {
		return arguments.length ? (e.range((t = Array.from(n, lg)).map(m_)), i) : t.slice();
	}, i.rangeRound = function(e) {
		return i.range(e).round(!0);
	}, i.round = function(e) {
		return arguments.length ? (n = !!e, i) : n;
	}, i.clamp = function(t) {
		return arguments.length ? (e.clamp(t), i) : e.clamp();
	}, i.unknown = function(e) {
		return arguments.length ? (r = e, i) : r;
	}, i.copy = function() {
		return g_(e.domain(), t).round(n).clamp(e.clamp()).unknown(r);
	}, Xm.apply(i, arguments), Wg(i);
}
//#endregion
//#region node_modules/d3-scale/src/quantile.js
function __() {
	var e = [], t = [], n = [], r;
	function i() {
		var r = 0, i = Math.max(1, t.length);
		for (n = Array(i - 1); ++r < i;) n[r - 1] = Jm(e, r / i);
		return a;
	}
	function a(e) {
		return e == null || isNaN(e = +e) ? r : t[Om(n, e)];
	}
	return a.invertExtent = function(r) {
		var i = t.indexOf(r);
		return i < 0 ? [NaN, NaN] : [i > 0 ? n[i - 1] : e[0], i < n.length ? n[i] : e[e.length - 1]];
	}, a.domain = function(t) {
		if (!arguments.length) return e.slice();
		e = [];
		for (let n of t) n != null && !isNaN(n = +n) && e.push(n);
		return e.sort(xm), i();
	}, a.range = function(e) {
		return arguments.length ? (t = Array.from(e), i()) : t.slice();
	}, a.unknown = function(e) {
		return arguments.length ? (r = e, a) : r;
	}, a.quantiles = function() {
		return n.slice();
	}, a.copy = function() {
		return __().domain(e).range(t).unknown(r);
	}, Xm.apply(a, arguments);
}
//#endregion
//#region node_modules/d3-scale/src/quantize.js
function v_() {
	var e = 0, t = 1, n = 1, r = [.5], i = [0, 1], a;
	function o(e) {
		return e != null && e <= e ? i[Om(r, e, 0, n)] : a;
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
		return v_().domain([e, t]).range(i).unknown(a);
	}, Xm.apply(Wg(o), arguments);
}
//#endregion
//#region node_modules/d3-scale/src/threshold.js
function y_() {
	var e = [.5], t = [0, 1], n, r = 1;
	function i(i) {
		return i != null && i <= i ? t[Om(e, i, 0, r)] : n;
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
		return y_().domain(e).range(t).unknown(n);
	}, Xm.apply(i, arguments);
}
//#endregion
//#region node_modules/d3-time/src/interval.js
var b_ = /* @__PURE__ */ new Date(), x_ = /* @__PURE__ */ new Date();
function S_(e, t, n, r) {
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
	}, i.filter = (n) => S_((t) => {
		if (t >= t) for (; e(t), !n(t);) t.setTime(t - 1);
	}, (e, r) => {
		if (e >= e) if (r < 0) for (; ++r <= 0;) for (; t(e, -1), !n(e););
		else for (; --r >= 0;) for (; t(e, 1), !n(e););
	}), n && (i.count = (t, r) => (b_.setTime(+t), x_.setTime(+r), e(b_), e(x_), Math.floor(n(b_, x_))), i.every = (e) => (e = Math.floor(e), !isFinite(e) || !(e > 0) ? null : e > 1 ? i.filter(r ? (t) => r(t) % e === 0 : (t) => i.count(0, t) % e === 0) : i)), i;
}
//#endregion
//#region node_modules/d3-time/src/millisecond.js
var C_ = S_(() => {}, (e, t) => {
	e.setTime(+e + t);
}, (e, t) => t - e);
C_.every = (e) => (e = Math.floor(e), !isFinite(e) || !(e > 0) ? null : e > 1 ? S_((t) => {
	t.setTime(Math.floor(t / e) * e);
}, (t, n) => {
	t.setTime(+t + n * e);
}, (t, n) => (n - t) / e) : C_), C_.range;
//#endregion
//#region node_modules/d3-time/src/duration.js
var w_ = 1e3, T_ = w_ * 60, E_ = T_ * 60, D_ = E_ * 24, O_ = D_ * 7, k_ = D_ * 30, A_ = D_ * 365, j_ = S_((e) => {
	e.setTime(e - e.getMilliseconds());
}, (e, t) => {
	e.setTime(+e + t * w_);
}, (e, t) => (t - e) / w_, (e) => e.getUTCSeconds());
j_.range;
//#endregion
//#region node_modules/d3-time/src/minute.js
var M_ = S_((e) => {
	e.setTime(e - e.getMilliseconds() - e.getSeconds() * w_);
}, (e, t) => {
	e.setTime(+e + t * T_);
}, (e, t) => (t - e) / T_, (e) => e.getMinutes());
M_.range;
var N_ = S_((e) => {
	e.setUTCSeconds(0, 0);
}, (e, t) => {
	e.setTime(+e + t * T_);
}, (e, t) => (t - e) / T_, (e) => e.getUTCMinutes());
N_.range;
//#endregion
//#region node_modules/d3-time/src/hour.js
var P_ = S_((e) => {
	e.setTime(e - e.getMilliseconds() - e.getSeconds() * w_ - e.getMinutes() * T_);
}, (e, t) => {
	e.setTime(+e + t * E_);
}, (e, t) => (t - e) / E_, (e) => e.getHours());
P_.range;
var F_ = S_((e) => {
	e.setUTCMinutes(0, 0, 0);
}, (e, t) => {
	e.setTime(+e + t * E_);
}, (e, t) => (t - e) / E_, (e) => e.getUTCHours());
F_.range;
//#endregion
//#region node_modules/d3-time/src/day.js
var I_ = S_((e) => e.setHours(0, 0, 0, 0), (e, t) => e.setDate(e.getDate() + t), (e, t) => (t - e - (t.getTimezoneOffset() - e.getTimezoneOffset()) * T_) / D_, (e) => e.getDate() - 1);
I_.range;
var L_ = S_((e) => {
	e.setUTCHours(0, 0, 0, 0);
}, (e, t) => {
	e.setUTCDate(e.getUTCDate() + t);
}, (e, t) => (t - e) / D_, (e) => e.getUTCDate() - 1);
L_.range;
var R_ = S_((e) => {
	e.setUTCHours(0, 0, 0, 0);
}, (e, t) => {
	e.setUTCDate(e.getUTCDate() + t);
}, (e, t) => (t - e) / D_, (e) => Math.floor(e / D_));
R_.range;
//#endregion
//#region node_modules/d3-time/src/week.js
function z_(e) {
	return S_((t) => {
		t.setDate(t.getDate() - (t.getDay() + 7 - e) % 7), t.setHours(0, 0, 0, 0);
	}, (e, t) => {
		e.setDate(e.getDate() + t * 7);
	}, (e, t) => (t - e - (t.getTimezoneOffset() - e.getTimezoneOffset()) * T_) / O_);
}
var B_ = z_(0), V_ = z_(1), H_ = z_(2), U_ = z_(3), W_ = z_(4), G_ = z_(5), K_ = z_(6);
B_.range, V_.range, H_.range, U_.range, W_.range, G_.range, K_.range;
function q_(e) {
	return S_((t) => {
		t.setUTCDate(t.getUTCDate() - (t.getUTCDay() + 7 - e) % 7), t.setUTCHours(0, 0, 0, 0);
	}, (e, t) => {
		e.setUTCDate(e.getUTCDate() + t * 7);
	}, (e, t) => (t - e) / O_);
}
var J_ = q_(0), Y_ = q_(1), X_ = q_(2), Z_ = q_(3), Q_ = q_(4), $_ = q_(5), ev = q_(6);
J_.range, Y_.range, X_.range, Z_.range, Q_.range, $_.range, ev.range;
//#endregion
//#region node_modules/d3-time/src/month.js
var tv = S_((e) => {
	e.setDate(1), e.setHours(0, 0, 0, 0);
}, (e, t) => {
	e.setMonth(e.getMonth() + t);
}, (e, t) => t.getMonth() - e.getMonth() + (t.getFullYear() - e.getFullYear()) * 12, (e) => e.getMonth());
tv.range;
var nv = S_((e) => {
	e.setUTCDate(1), e.setUTCHours(0, 0, 0, 0);
}, (e, t) => {
	e.setUTCMonth(e.getUTCMonth() + t);
}, (e, t) => t.getUTCMonth() - e.getUTCMonth() + (t.getUTCFullYear() - e.getUTCFullYear()) * 12, (e) => e.getUTCMonth());
nv.range;
//#endregion
//#region node_modules/d3-time/src/year.js
var rv = S_((e) => {
	e.setMonth(0, 1), e.setHours(0, 0, 0, 0);
}, (e, t) => {
	e.setFullYear(e.getFullYear() + t);
}, (e, t) => t.getFullYear() - e.getFullYear(), (e) => e.getFullYear());
rv.every = (e) => !isFinite(e = Math.floor(e)) || !(e > 0) ? null : S_((t) => {
	t.setFullYear(Math.floor(t.getFullYear() / e) * e), t.setMonth(0, 1), t.setHours(0, 0, 0, 0);
}, (t, n) => {
	t.setFullYear(t.getFullYear() + n * e);
}), rv.range;
var iv = S_((e) => {
	e.setUTCMonth(0, 1), e.setUTCHours(0, 0, 0, 0);
}, (e, t) => {
	e.setUTCFullYear(e.getUTCFullYear() + t);
}, (e, t) => t.getUTCFullYear() - e.getUTCFullYear(), (e) => e.getUTCFullYear());
iv.every = (e) => !isFinite(e = Math.floor(e)) || !(e > 0) ? null : S_((t) => {
	t.setUTCFullYear(Math.floor(t.getUTCFullYear() / e) * e), t.setUTCMonth(0, 1), t.setUTCHours(0, 0, 0, 0);
}, (t, n) => {
	t.setUTCFullYear(t.getUTCFullYear() + n * e);
}), iv.range;
//#endregion
//#region node_modules/d3-time/src/ticks.js
function av(e, t, n, r, i, a) {
	let o = [
		[
			j_,
			1,
			w_
		],
		[
			j_,
			5,
			5 * w_
		],
		[
			j_,
			15,
			15 * w_
		],
		[
			j_,
			30,
			30 * w_
		],
		[
			a,
			1,
			T_
		],
		[
			a,
			5,
			5 * T_
		],
		[
			a,
			15,
			15 * T_
		],
		[
			a,
			30,
			30 * T_
		],
		[
			i,
			1,
			E_
		],
		[
			i,
			3,
			3 * E_
		],
		[
			i,
			6,
			6 * E_
		],
		[
			i,
			12,
			12 * E_
		],
		[
			r,
			1,
			D_
		],
		[
			r,
			2,
			2 * D_
		],
		[
			n,
			1,
			O_
		],
		[
			t,
			1,
			k_
		],
		[
			t,
			3,
			3 * k_
		],
		[
			e,
			1,
			A_
		]
	];
	function s(e, t, n) {
		let r = t < e;
		r && ([e, t] = [t, e]);
		let i = n && typeof n.range == "function" ? n : c(e, t, n), a = i ? i.range(e, +t + 1) : [];
		return r ? a.reverse() : a;
	}
	function c(t, n, r) {
		let i = Math.abs(n - t) / r, a = Cm(([, , e]) => e).right(o, i);
		if (a === o.length) return e.every(Hm(t / A_, n / A_, r));
		if (a === 0) return C_.every(Math.max(Hm(t, n, r), 1));
		let [s, c] = o[i / o[a - 1][2] < o[a][2] / i ? a - 1 : a];
		return s.every(c);
	}
	return [s, c];
}
var [ov, sv] = av(iv, nv, J_, R_, F_, N_), [cv, lv] = av(rv, tv, B_, I_, P_, M_);
//#endregion
//#region node_modules/d3-time-format/src/locale.js
function uv(e) {
	if (0 <= e.y && e.y < 100) {
		var t = new Date(-1, e.m, e.d, e.H, e.M, e.S, e.L);
		return t.setFullYear(e.y), t;
	}
	return new Date(e.y, e.m, e.d, e.H, e.M, e.S, e.L);
}
function dv(e) {
	if (0 <= e.y && e.y < 100) {
		var t = new Date(Date.UTC(-1, e.m, e.d, e.H, e.M, e.S, e.L));
		return t.setUTCFullYear(e.y), t;
	}
	return new Date(Date.UTC(e.y, e.m, e.d, e.H, e.M, e.S, e.L));
}
function fv(e, t, n) {
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
function pv(e) {
	var t = e.dateTime, n = e.date, r = e.time, i = e.periods, a = e.days, o = e.shortDays, s = e.months, c = e.shortMonths, l = yv(i), u = bv(i), d = yv(a), f = bv(a), p = yv(o), m = bv(o), h = yv(s), g = bv(s), _ = yv(c), v = bv(c), y = {
		a: N,
		A: P,
		b: F,
		B: ee,
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
		p: te,
		q: ne,
		Q: Oy,
		s: ky,
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
		"%": Dy
	}, b = {
		a: re,
		A: ie,
		b: ae,
		B: oe,
		c: null,
		d: sy,
		e: sy,
		f: fy,
		g: Cy,
		G: Ty,
		H: cy,
		I: ly,
		j: uy,
		L: dy,
		m: py,
		M: my,
		p: se,
		q: ce,
		Q: Oy,
		s: ky,
		S: hy,
		u: gy,
		U: _y,
		V: yy,
		w: by,
		W: xy,
		x: null,
		X: null,
		y: Sy,
		Y: wy,
		Z: Ey,
		"%": Dy
	}, x = {
		a: E,
		A: D,
		b: O,
		B: k,
		c: A,
		d: jv,
		e: jv,
		f: Lv,
		g: Dv,
		G: Ev,
		H: Nv,
		I: Nv,
		j: Mv,
		L: Iv,
		m: Av,
		M: Pv,
		p: T,
		q: kv,
		Q: zv,
		s: Bv,
		S: Fv,
		u: Sv,
		U: Cv,
		V: wv,
		w: xv,
		W: Tv,
		x: j,
		X: M,
		y: Dv,
		Y: Ev,
		Z: Ov,
		"%": Rv
	};
	y.x = S(n, y), y.X = S(r, y), y.c = S(t, y), b.x = S(n, b), b.X = S(r, b), b.c = S(t, b);
	function S(e, t) {
		return function(n) {
			var r = [], i = -1, a = 0, o = e.length, s, c, l;
			for (n instanceof Date || (n = /* @__PURE__ */ new Date(+n)); ++i < o;) e.charCodeAt(i) === 37 && (r.push(e.slice(a, i)), (c = mv[s = e.charAt(++i)]) == null ? c = s === "e" ? " " : "0" : s = e.charAt(++i), (l = t[s]) && (s = l(n, c)), r.push(s), a = i + 1);
			return r.push(e.slice(a, i)), r.join("");
		};
	}
	function C(e, t) {
		return function(n) {
			var r = fv(1900, void 0, 1), i = w(r, e, n += "", 0), a, o;
			if (i != n.length) return null;
			if ("Q" in r) return new Date(r.Q);
			if ("s" in r) return new Date(r.s * 1e3 + ("L" in r ? r.L : 0));
			if (t && !("Z" in r) && (r.Z = 0), "p" in r && (r.H = r.H % 12 + r.p * 12), r.m === void 0 && (r.m = "q" in r ? r.q : 0), "V" in r) {
				if (r.V < 1 || r.V > 53) return null;
				"w" in r || (r.w = 1), "Z" in r ? (a = dv(fv(r.y, 0, 1)), o = a.getUTCDay(), a = o > 4 || o === 0 ? Y_.ceil(a) : Y_(a), a = L_.offset(a, (r.V - 1) * 7), r.y = a.getUTCFullYear(), r.m = a.getUTCMonth(), r.d = a.getUTCDate() + (r.w + 6) % 7) : (a = uv(fv(r.y, 0, 1)), o = a.getDay(), a = o > 4 || o === 0 ? V_.ceil(a) : V_(a), a = I_.offset(a, (r.V - 1) * 7), r.y = a.getFullYear(), r.m = a.getMonth(), r.d = a.getDate() + (r.w + 6) % 7);
			} else ("W" in r || "U" in r) && ("w" in r || (r.w = "u" in r ? r.u % 7 : +("W" in r)), o = "Z" in r ? dv(fv(r.y, 0, 1)).getUTCDay() : uv(fv(r.y, 0, 1)).getDay(), r.m = 0, r.d = "W" in r ? (r.w + 6) % 7 + r.W * 7 - (o + 5) % 7 : r.w + r.U * 7 - (o + 6) % 7);
			return "Z" in r ? (r.H += r.Z / 100 | 0, r.M += r.Z % 100, dv(r)) : uv(r);
		};
	}
	function w(e, t, n, r) {
		for (var i = 0, a = t.length, o = n.length, s, c; i < a;) {
			if (r >= o) return -1;
			if (s = t.charCodeAt(i++), s === 37) {
				if (s = t.charAt(i++), c = x[s in mv ? t.charAt(i++) : s], !c || (r = c(e, n, r)) < 0) return -1;
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
	function F(e) {
		return c[e.getMonth()];
	}
	function ee(e) {
		return s[e.getMonth()];
	}
	function te(e) {
		return i[+(e.getHours() >= 12)];
	}
	function ne(e) {
		return 1 + ~~(e.getMonth() / 3);
	}
	function re(e) {
		return o[e.getUTCDay()];
	}
	function ie(e) {
		return a[e.getUTCDay()];
	}
	function ae(e) {
		return c[e.getUTCMonth()];
	}
	function oe(e) {
		return s[e.getUTCMonth()];
	}
	function se(e) {
		return i[+(e.getUTCHours() >= 12)];
	}
	function ce(e) {
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
var mv = {
	"-": "",
	_: " ",
	0: "0"
}, hv = /^\s*\d+/, gv = /^%/, _v = /[\\^$*+?|[\]().{}]/g;
function J(e, t, n) {
	var r = e < 0 ? "-" : "", i = (r ? -e : e) + "", a = i.length;
	return r + (a < n ? Array(n - a + 1).join(t) + i : i);
}
function vv(e) {
	return e.replace(_v, "\\$&");
}
function yv(e) {
	return RegExp("^(?:" + e.map(vv).join("|") + ")", "i");
}
function bv(e) {
	return new Map(e.map((e, t) => [e.toLowerCase(), t]));
}
function xv(e, t, n) {
	var r = hv.exec(t.slice(n, n + 1));
	return r ? (e.w = +r[0], n + r[0].length) : -1;
}
function Sv(e, t, n) {
	var r = hv.exec(t.slice(n, n + 1));
	return r ? (e.u = +r[0], n + r[0].length) : -1;
}
function Cv(e, t, n) {
	var r = hv.exec(t.slice(n, n + 2));
	return r ? (e.U = +r[0], n + r[0].length) : -1;
}
function wv(e, t, n) {
	var r = hv.exec(t.slice(n, n + 2));
	return r ? (e.V = +r[0], n + r[0].length) : -1;
}
function Tv(e, t, n) {
	var r = hv.exec(t.slice(n, n + 2));
	return r ? (e.W = +r[0], n + r[0].length) : -1;
}
function Ev(e, t, n) {
	var r = hv.exec(t.slice(n, n + 4));
	return r ? (e.y = +r[0], n + r[0].length) : -1;
}
function Dv(e, t, n) {
	var r = hv.exec(t.slice(n, n + 2));
	return r ? (e.y = +r[0] + (+r[0] > 68 ? 1900 : 2e3), n + r[0].length) : -1;
}
function Ov(e, t, n) {
	var r = /^(Z)|([+-]\d\d)(?::?(\d\d))?/.exec(t.slice(n, n + 6));
	return r ? (e.Z = r[1] ? 0 : -(r[2] + (r[3] || "00")), n + r[0].length) : -1;
}
function kv(e, t, n) {
	var r = hv.exec(t.slice(n, n + 1));
	return r ? (e.q = r[0] * 3 - 3, n + r[0].length) : -1;
}
function Av(e, t, n) {
	var r = hv.exec(t.slice(n, n + 2));
	return r ? (e.m = r[0] - 1, n + r[0].length) : -1;
}
function jv(e, t, n) {
	var r = hv.exec(t.slice(n, n + 2));
	return r ? (e.d = +r[0], n + r[0].length) : -1;
}
function Mv(e, t, n) {
	var r = hv.exec(t.slice(n, n + 3));
	return r ? (e.m = 0, e.d = +r[0], n + r[0].length) : -1;
}
function Nv(e, t, n) {
	var r = hv.exec(t.slice(n, n + 2));
	return r ? (e.H = +r[0], n + r[0].length) : -1;
}
function Pv(e, t, n) {
	var r = hv.exec(t.slice(n, n + 2));
	return r ? (e.M = +r[0], n + r[0].length) : -1;
}
function Fv(e, t, n) {
	var r = hv.exec(t.slice(n, n + 2));
	return r ? (e.S = +r[0], n + r[0].length) : -1;
}
function Iv(e, t, n) {
	var r = hv.exec(t.slice(n, n + 3));
	return r ? (e.L = +r[0], n + r[0].length) : -1;
}
function Lv(e, t, n) {
	var r = hv.exec(t.slice(n, n + 6));
	return r ? (e.L = Math.floor(r[0] / 1e3), n + r[0].length) : -1;
}
function Rv(e, t, n) {
	var r = gv.exec(t.slice(n, n + 1));
	return r ? n + r[0].length : -1;
}
function zv(e, t, n) {
	var r = hv.exec(t.slice(n));
	return r ? (e.Q = +r[0], n + r[0].length) : -1;
}
function Bv(e, t, n) {
	var r = hv.exec(t.slice(n));
	return r ? (e.s = +r[0], n + r[0].length) : -1;
}
function Vv(e, t) {
	return J(e.getDate(), t, 2);
}
function Hv(e, t) {
	return J(e.getHours(), t, 2);
}
function Uv(e, t) {
	return J(e.getHours() % 12 || 12, t, 2);
}
function Wv(e, t) {
	return J(1 + I_.count(rv(e), e), t, 3);
}
function Gv(e, t) {
	return J(e.getMilliseconds(), t, 3);
}
function Kv(e, t) {
	return Gv(e, t) + "000";
}
function qv(e, t) {
	return J(e.getMonth() + 1, t, 2);
}
function Jv(e, t) {
	return J(e.getMinutes(), t, 2);
}
function Yv(e, t) {
	return J(e.getSeconds(), t, 2);
}
function Xv(e) {
	var t = e.getDay();
	return t === 0 ? 7 : t;
}
function Zv(e, t) {
	return J(B_.count(rv(e) - 1, e), t, 2);
}
function Qv(e) {
	var t = e.getDay();
	return t >= 4 || t === 0 ? W_(e) : W_.ceil(e);
}
function $v(e, t) {
	return e = Qv(e), J(W_.count(rv(e), e) + (rv(e).getDay() === 4), t, 2);
}
function ey(e) {
	return e.getDay();
}
function ty(e, t) {
	return J(V_.count(rv(e) - 1, e), t, 2);
}
function ny(e, t) {
	return J(e.getFullYear() % 100, t, 2);
}
function ry(e, t) {
	return e = Qv(e), J(e.getFullYear() % 100, t, 2);
}
function iy(e, t) {
	return J(e.getFullYear() % 1e4, t, 4);
}
function ay(e, t) {
	var n = e.getDay();
	return e = n >= 4 || n === 0 ? W_(e) : W_.ceil(e), J(e.getFullYear() % 1e4, t, 4);
}
function oy(e) {
	var t = e.getTimezoneOffset();
	return (t > 0 ? "-" : (t *= -1, "+")) + J(t / 60 | 0, "0", 2) + J(t % 60, "0", 2);
}
function sy(e, t) {
	return J(e.getUTCDate(), t, 2);
}
function cy(e, t) {
	return J(e.getUTCHours(), t, 2);
}
function ly(e, t) {
	return J(e.getUTCHours() % 12 || 12, t, 2);
}
function uy(e, t) {
	return J(1 + L_.count(iv(e), e), t, 3);
}
function dy(e, t) {
	return J(e.getUTCMilliseconds(), t, 3);
}
function fy(e, t) {
	return dy(e, t) + "000";
}
function py(e, t) {
	return J(e.getUTCMonth() + 1, t, 2);
}
function my(e, t) {
	return J(e.getUTCMinutes(), t, 2);
}
function hy(e, t) {
	return J(e.getUTCSeconds(), t, 2);
}
function gy(e) {
	var t = e.getUTCDay();
	return t === 0 ? 7 : t;
}
function _y(e, t) {
	return J(J_.count(iv(e) - 1, e), t, 2);
}
function vy(e) {
	var t = e.getUTCDay();
	return t >= 4 || t === 0 ? Q_(e) : Q_.ceil(e);
}
function yy(e, t) {
	return e = vy(e), J(Q_.count(iv(e), e) + (iv(e).getUTCDay() === 4), t, 2);
}
function by(e) {
	return e.getUTCDay();
}
function xy(e, t) {
	return J(Y_.count(iv(e) - 1, e), t, 2);
}
function Sy(e, t) {
	return J(e.getUTCFullYear() % 100, t, 2);
}
function Cy(e, t) {
	return e = vy(e), J(e.getUTCFullYear() % 100, t, 2);
}
function wy(e, t) {
	return J(e.getUTCFullYear() % 1e4, t, 4);
}
function Ty(e, t) {
	var n = e.getUTCDay();
	return e = n >= 4 || n === 0 ? Q_(e) : Q_.ceil(e), J(e.getUTCFullYear() % 1e4, t, 4);
}
function Ey() {
	return "+0000";
}
function Dy() {
	return "%";
}
function Oy(e) {
	return +e;
}
function ky(e) {
	return Math.floor(e / 1e3);
}
//#endregion
//#region node_modules/d3-time-format/src/defaultLocale.js
var Ay, jy, My;
Ny({
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
function Ny(e) {
	return Ay = pv(e), jy = Ay.format, Ay.parse, My = Ay.utcFormat, Ay.utcParse, Ay;
}
//#endregion
//#region node_modules/d3-scale/src/time.js
function Py(e) {
	return new Date(e);
}
function Fy(e) {
	return e instanceof Date ? +e : +/* @__PURE__ */ new Date(+e);
}
function Iy(e, t, n, r, i, a, o, s, c, l) {
	var u = vg(), d = u.invert, f = u.domain, p = l(".%L"), m = l(":%S"), h = l("%I:%M"), g = l("%I %p"), _ = l("%a %d"), v = l("%b %d"), y = l("%B"), b = l("%Y");
	function x(e) {
		return (c(e) < e ? p : s(e) < e ? m : o(e) < e ? h : a(e) < e ? g : r(e) < e ? i(e) < e ? _ : v : n(e) < e ? y : b)(e);
	}
	return u.invert = function(e) {
		return new Date(d(e));
	}, u.domain = function(e) {
		return arguments.length ? f(Array.from(e, Fy)) : f().map(Py);
	}, u.ticks = function(t) {
		var n = f();
		return e(n[0], n[n.length - 1], t == null ? 10 : t);
	}, u.tickFormat = function(e, t) {
		return t == null ? x : l(t);
	}, u.nice = function(e) {
		var n = f();
		return (!e || typeof e.range != "function") && (e = t(n[0], n[n.length - 1], e == null ? 10 : e)), e ? f(qg(n, e)) : u;
	}, u.copy = function() {
		return gg(u, Iy(e, t, n, r, i, a, o, s, c, l));
	}, u;
}
function Ly() {
	return Xm.apply(Iy(cv, lv, rv, tv, B_, I_, P_, M_, j_, jy).domain([new Date(2e3, 0, 1), new Date(2e3, 0, 2)]), arguments);
}
//#endregion
//#region node_modules/d3-scale/src/utcTime.js
function Ry() {
	return Xm.apply(Iy(ov, sv, iv, nv, J_, L_, F_, N_, j_, My).domain([Date.UTC(2e3, 0, 1), Date.UTC(2e3, 0, 2)]), arguments);
}
//#endregion
//#region node_modules/d3-scale/src/sequential.js
function zy() {
	var e = 0, t = 1, n, r, i, a, o = dg, s = !1, c;
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
	return l.range = u(ag), l.rangeRound = u(og), l.unknown = function(e) {
		return arguments.length ? (c = e, l) : c;
	}, function(o) {
		return a = o, n = o(e), r = o(t), i = n === r ? 0 : 1 / (r - n), l;
	};
}
function By(e, t) {
	return t.domain(e.domain()).interpolator(e.interpolator()).clamp(e.clamp()).unknown(e.unknown());
}
function Vy() {
	var e = Wg(zy()(dg));
	return e.copy = function() {
		return By(e, Vy());
	}, Zm.apply(e, arguments);
}
function Hy() {
	var e = n_(zy()).domain([1, 10]);
	return e.copy = function() {
		return By(e, Hy()).base(e.base());
	}, Zm.apply(e, arguments);
}
function Uy() {
	var e = o_(zy());
	return e.copy = function() {
		return By(e, Uy()).constant(e.constant());
	}, Zm.apply(e, arguments);
}
function Wy() {
	var e = d_(zy());
	return e.copy = function() {
		return By(e, Wy()).exponent(e.exponent());
	}, Zm.apply(e, arguments);
}
function Gy() {
	return Wy.apply(null, arguments).exponent(.5);
}
//#endregion
//#region node_modules/d3-scale/src/sequentialQuantile.js
function Ky() {
	var e = [], t = dg;
	function n(n) {
		if (n != null && !isNaN(n = +n)) return t((Om(e, n, 1) - 1) / (e.length - 1));
	}
	return n.domain = function(t) {
		if (!arguments.length) return e.slice();
		e = [];
		for (let n of t) n != null && !isNaN(n = +n) && e.push(n);
		return e.sort(xm), n;
	}, n.interpolator = function(e) {
		return arguments.length ? (t = e, n) : t;
	}, n.range = function() {
		return e.map((n, r) => t(r / (e.length - 1)));
	}, n.quantiles = function(t) {
		return Array.from({ length: t + 1 }, (n, r) => qm(e, r / t));
	}, n.copy = function() {
		return Ky(t).domain(e);
	}, Zm.apply(n, arguments);
}
//#endregion
//#region node_modules/d3-scale/src/diverging.js
function qy() {
	var e = 0, t = .5, n = 1, r = 1, i, a, o, s, c, l = dg, u, d = !1, f;
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
			return arguments.length ? ([n, r, i] = t, l = sg(e, [
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
	return p.range = m(ag), p.rangeRound = m(og), p.unknown = function(e) {
		return arguments.length ? (f = e, p) : f;
	}, function(l) {
		return u = l, i = l(e), a = l(t), o = l(n), s = i === a ? 0 : .5 / (a - i), c = a === o ? 0 : .5 / (o - a), r = a < i ? -1 : 1, p;
	};
}
function Jy() {
	var e = Wg(qy()(dg));
	return e.copy = function() {
		return By(e, Jy());
	}, Zm.apply(e, arguments);
}
function Yy() {
	var e = n_(qy()).domain([
		.1,
		1,
		10
	]);
	return e.copy = function() {
		return By(e, Yy()).base(e.base());
	}, Zm.apply(e, arguments);
}
function Xy() {
	var e = o_(qy());
	return e.copy = function() {
		return By(e, Xy()).constant(e.constant());
	}, Zm.apply(e, arguments);
}
function Zy() {
	var e = d_(qy());
	return e.copy = function() {
		return By(e, Zy()).exponent(e.exponent());
	}, Zm.apply(e, arguments);
}
function Qy() {
	return Zy.apply(null, arguments).exponent(.5);
}
//#endregion
//#region node_modules/victory-vendor/es/d3-scale.js
var $y = /* @__PURE__ */ s({
	scaleBand: () => eh,
	scaleDiverging: () => Jy,
	scaleDivergingLog: () => Yy,
	scaleDivergingPow: () => Zy,
	scaleDivergingSqrt: () => Qy,
	scaleDivergingSymlog: () => Xy,
	scaleIdentity: () => Kg,
	scaleImplicit: () => Qm,
	scaleLinear: () => Gg,
	scaleLog: () => r_,
	scaleOrdinal: () => $m,
	scalePoint: () => nh,
	scalePow: () => f_,
	scaleQuantile: () => __,
	scaleQuantize: () => v_,
	scaleRadial: () => g_,
	scaleSequential: () => Vy,
	scaleSequentialLog: () => Hy,
	scaleSequentialPow: () => Wy,
	scaleSequentialQuantile: () => Ky,
	scaleSequentialSqrt: () => Gy,
	scaleSequentialSymlog: () => Uy,
	scaleSqrt: () => p_,
	scaleSymlog: () => s_,
	scaleThreshold: () => y_,
	scaleTime: () => Ly,
	scaleUtc: () => Ry,
	tickFormat: () => Ug
});
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineConfiguredScale.js
function eb(e) {
	var t = $y;
	if (e in t && typeof t[e] == "function") return t[e]();
	var n = `scale${bn(e)}`;
	if (n in t && typeof t[n] == "function") return t[n]();
}
function tb(e, t, n) {
	if (typeof e == "function") return e.copy().domain(t).range(n);
	if (e != null) {
		var r = eb(e);
		if (r != null) return r.domain(t).range(n), r;
	}
}
function nb(e, t, n, r) {
	if (!(n == null || r == null)) return typeof e.scale == "function" ? tb(e.scale, n, r) : tb(t, n, r);
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineRealScaleType.js
function rb(e) {
	return `scale${bn(e)}`;
}
function ib(e) {
	return rb(e) in $y;
}
var ab = (e, t, n) => {
	if (e != null) {
		var r = e.scale, i = e.type;
		if (r === "auto") return i === "category" && n && (n.indexOf("LineChart") >= 0 || n.indexOf("AreaChart") >= 0 || n.indexOf("ComposedChart") >= 0 && !t) ? "point" : i === "category" ? "band" : "linear";
		if (typeof r == "string") return ib(r) ? r : "point";
	}
};
//#endregion
//#region node_modules/recharts/es6/util/scale/createCategoricalInverse.js
function ob(e, t) {
	for (var n = 0, r = e.length, i = e[0] < e[e.length - 1]; n < r;) {
		var a = Math.floor((n + r) / 2);
		(i ? e[a] < t : e[a] > t) ? n = a + 1 : r = a;
	}
	return n;
}
function sb(e, t) {
	if (e) {
		var n = t == null ? e.domain() : t, r = n.map((t) => {
			var n;
			return (n = e(t)) == null ? 0 : n;
		}), i = e.range();
		if (!(n.length === 0 || i.length < 2)) return (e) => {
			var t, i, a = ob(r, e);
			if (a <= 0) return n[0];
			if (a >= n.length) return n[n.length - 1];
			var o = (t = r[a - 1]) == null ? 0 : t, s = (i = r[a]) == null ? 0 : i;
			return Math.abs(e - o) <= Math.abs(e - s) ? n[a - 1] : n[a];
		};
	}
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineInverseScaleFunction.js
function cb(e) {
	if (e != null) return "invert" in e && typeof e.invert == "function" ? e.invert.bind(e) : sb(e, void 0);
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/axisSelectors.js
function lb(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function ub(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? lb(Object(n), !0).forEach(function(t) {
			db(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : lb(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function db(e, t, n) {
	return (t = fb(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function fb(e) {
	var t = pb(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function pb(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function mb(e, t) {
	return yb(e) || vb(e, t) || gb(e, t) || hb();
}
function hb() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function gb(e, t) {
	if (e) {
		if (typeof e == "string") return _b(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? _b(e, t) : void 0;
	}
}
function _b(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function vb(e, t) {
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
function yb(e) {
	if (Array.isArray(e)) return e;
}
var bb = [0, "auto"], xb = {
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
}, Sb = (e, t) => e.cartesianAxis.xAxis[t], Cb = (e, t) => {
	var n = Sb(e, t);
	return n == null ? xb : n;
}, wb = {
	allowDataOverflow: !1,
	allowDecimals: !0,
	allowDuplicatedCategory: !0,
	angle: 0,
	dataKey: void 0,
	domain: bb,
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
}, Tb = (e, t) => e.cartesianAxis.yAxis[t], Eb = (e, t) => {
	var n = Tb(e, t);
	return n == null ? wb : n;
}, Db = {
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
}, Ob = (e, t) => {
	var n = e.cartesianAxis.zAxis[t];
	return n == null ? Db : n;
}, kb = (e, t, n) => {
	switch (t) {
		case "xAxis": return Cb(e, n);
		case "yAxis": return Eb(e, n);
		case "zAxis": return Ob(e, n);
		case "angleAxis": return em(e, n);
		case "radiusAxis": return tm(e, n);
		default: throw Error(`Unexpected axis type: ${t}`);
	}
}, Ab = (e, t, n) => {
	switch (t) {
		case "xAxis": return Cb(e, n);
		case "yAxis": return Eb(e, n);
		default: throw Error(`Unexpected axis type: ${t}`);
	}
}, jb = (e, t, n) => {
	switch (t) {
		case "xAxis": return Cb(e, n);
		case "yAxis": return Eb(e, n);
		case "angleAxis": return em(e, n);
		case "radiusAxis": return tm(e, n);
		default: throw Error(`Unexpected axis type: ${t}`);
	}
}, Mb = (e) => e.graphicalItems.cartesianItems.some((e) => e.type === "bar") || e.graphicalItems.polarItems.some((e) => e.type === "radialBar");
function Nb(e, t) {
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
var Pb = (e) => e.graphicalItems.cartesianItems, Fb = z([lm, um], Nb), Ib = (e, t, n) => e.filter(n).filter((e) => (t == null ? void 0 : t.includeHidden) === !0 || !e.hide), Lb = z([
	Pb,
	kb,
	Fb
], Ib, { memoizeOptions: { resultEqualityCheck: hm } }), Rb = z([Lb], (e) => e.filter((e) => e.type === "area" || e.type === "bar").filter(pm)), zb = (e) => e.filter((e) => !("stackId" in e) || e.stackId === void 0), Bb = z([Lb], zb), Vb = (e) => e.map((e) => e.data).filter(Boolean).flat(1), Hb = z([Lb], (e) => e.some((e) => !e.data)), Ub = z([Lb], Vb, { memoizeOptions: { resultEqualityCheck: hm } }), Wb = (e, t) => {
	var n = t.chartData, r = n === void 0 ? [] : n, i = t.dataStartIndex, a = t.dataEndIndex;
	return e.length > 0 ? e : r.slice(i, a + 1);
}, Gb = z([Ub, rp], Wb), Kb = (e, t, n) => (t == null ? void 0 : t.dataKey) == null ? n.length > 0 ? n.map((e) => e.dataKey).flatMap((t) => e.map((e) => ({ value: Hs(e, t) }))) : e.map((e) => ({ value: e })) : e.map((e) => ({ value: Hs(e, t.dataKey) })), qb = (e, t, n, r, i, a) => {
	var o = r.chartData, s = o === void 0 ? [] : o, c = r.dataStartIndex, l = r.dataEndIndex, u = Kb(e, t, n);
	return i && (t == null ? void 0 : t.dataKey) != null && a.length > 0 ? [...s.slice(c, l + 1).map((e) => ({ value: Hs(e, t.dataKey) })).filter((e) => e.value != null), ...u] : u;
}, Jb = z([
	Gb,
	kb,
	Lb,
	rp,
	Hb,
	Ub
], qb);
function Yb(e) {
	if (fn(e) || e instanceof Date) {
		var t = Number(e);
		if (U(t)) return t;
	}
}
function Xb(e) {
	if (Array.isArray(e)) {
		var t = [Yb(e[0]), Yb(e[1])];
		return pp(t) ? t : void 0;
	}
	var n = Yb(e);
	if (n != null) return [n, n];
}
function Zb(e) {
	return e.map(Yb).filter(xn);
}
function Qb(e, t) {
	var n = Yb(e), r = Yb(t);
	return n == null && r == null ? 0 : n == null ? -1 : r == null ? 1 : n - r;
}
var $b = z([Jb], (e) => e == null ? void 0 : e.map((e) => e.value).sort(Qb));
function ex(e, t) {
	switch (e) {
		case "xAxis": return t.direction === "x";
		case "yAxis": return t.direction === "y";
		default: return !1;
	}
}
function tx(e, t, n) {
	if (!n || !n.length) return [];
	var r;
	if (typeof t == "number" && !un(t)) r = t;
	else if (Array.isArray(t)) {
		var i = Zb(t);
		i.length > 0 && (r = Math.max(...i));
	}
	return r == null ? [] : Zb(n.flatMap((t) => {
		var n = Hs(e, t.dataKey), i, a;
		if (Array.isArray(n)) {
			var o = mb(n, 2);
			i = o[0], a = o[1];
		} else i = a = n;
		if (!(!U(i) || !U(a))) return [r - i, r + a];
	}));
}
var nx = (e) => jb(e, _m(e), vm(e)), rx = z([nx], (e) => e == null ? void 0 : e.dataKey), ix = z([
	Rb,
	rp,
	nx
], fm), ax = (e, t, n, r) => {
	var i = t.reduce((e, t) => {
		if (t.stackId == null) return e;
		var n = e[t.stackId];
		return n == null && (n = []), n.push(t), e[t.stackId] = n, e;
	}, {});
	return Object.fromEntries(Object.entries(i).map((t) => {
		var i = mb(t, 2), a = i[0], o = i[1], s = r ? [...o].reverse() : o;
		return [a, {
			stackedData: qs(e, s.map(dm), n),
			graphicalItems: s
		}];
	}));
}, ox = z([
	ix,
	Rb,
	Ip,
	Lp
], ax), sx = (e, t, n, r) => {
	var i = t.dataStartIndex, a = t.dataEndIndex;
	if (r == null && n !== "zAxis") return $s(e, i, a);
}, cx = z([kb], (e) => e.allowDataOverflow), lx = (e) => {
	var t;
	if (e == null || !("domain" in e)) return bb;
	if (e.domain != null) return e.domain;
	if ("ticks" in e && e.ticks != null) {
		if (e.type === "number") {
			var n = Zb(e.ticks);
			return [Math.min(...n), Math.max(...n)];
		}
		if (e.type === "category") return e.ticks.map(String);
	}
	return (t = e == null ? void 0 : e.domain) == null ? bb : t;
}, ux = z([kb], lx), dx = z([ux, cx], hp), fx = z([
	ox,
	tp,
	lm,
	dx
], sx, { memoizeOptions: { resultEqualityCheck: mm } }), px = (e) => e.errorBars, mx = (e, t, n) => e.flatMap((e) => t[e.id]).filter(Boolean).filter((e) => ex(n, e)), hx = function() {
	var e = [...arguments].filter(Boolean);
	if (e.length !== 0) {
		var t = e.flat();
		return [Math.min(...t), Math.max(...t)];
	}
}, gx = function(e, t, n, r, i) {
	var a = arguments.length > 5 && arguments[5] !== void 0 ? arguments[5] : [], o, s;
	if (n.length > 0 && n.forEach((e) => {
		var n, c = e.data == null ? a : [...e.data], l = (n = r[e.id]) == null ? void 0 : n.filter((e) => ex(i, e));
		c.forEach((n) => {
			var r, i = Hs(n, (r = t.dataKey) == null ? e.dataKey : r), a = tx(n, i, l);
			if (a.length >= 2) {
				var c = Math.min(...a), u = Math.max(...a);
				(o == null || c < o) && (o = c), (s == null || u > s) && (s = u);
			}
			var d = Xb(i);
			d != null && (o = o == null ? d[0] : Math.min(o, d[0]), s = s == null ? d[1] : Math.max(s, d[1]));
		});
	}), (t == null ? void 0 : t.dataKey) != null && n.length === 0 && e.forEach((e) => {
		var n = Xb(Hs(e, t.dataKey));
		n != null && (o = o == null ? n[0] : Math.min(o, n[0]), s = s == null ? n[1] : Math.max(s, n[1]));
	}), U(o) && U(s)) return [o, s];
}, _x = z([
	Gb,
	kb,
	Bb,
	px,
	lm,
	ap
], gx, { memoizeOptions: { resultEqualityCheck: mm } });
function vx(e) {
	var t = e.value;
	if (fn(t) || t instanceof Date) return t;
}
var yx = (e, t, n) => {
	var r = e.map(vx).filter((e) => e != null);
	return n && (t.dataKey == null || t.allowDuplicatedCategory && gn(r)) ? ep(0, e.length) : t.allowDuplicatedCategory ? r : Array.from(new Set(r));
}, bx = (e) => e.referenceElements.dots, xx = (e, t, n) => e.filter((e) => e.ifOverflow === "extendDomain").filter((e) => t === "xAxis" ? e.xAxisId === n : e.yAxisId === n), Sx = z([
	bx,
	lm,
	um
], xx), Cx = (e) => e.referenceElements.areas, wx = z([
	Cx,
	lm,
	um
], xx), Tx = (e) => e.referenceElements.lines, Ex = z([
	Tx,
	lm,
	um
], xx), Dx = (e, t) => {
	if (e != null) {
		var n = Zb(e.map((e) => t === "xAxis" ? e.x : e.y));
		if (n.length !== 0) return [Math.min(...n), Math.max(...n)];
	}
}, Ox = z(Sx, lm, Dx), kx = (e, t) => {
	if (e != null) {
		var n = Zb(e.flatMap((e) => [t === "xAxis" ? e.x1 : e.y1, t === "xAxis" ? e.x2 : e.y2]));
		if (n.length !== 0) return [Math.min(...n), Math.max(...n)];
	}
}, Ax = z([wx, lm], kx);
function jx(e) {
	var t;
	if (e.x != null) return Zb([e.x]);
	var n = (t = e.segment) == null ? void 0 : t.map((e) => e.x);
	return n == null || n.length === 0 ? [] : Zb(n);
}
function Mx(e) {
	var t;
	if (e.y != null) return Zb([e.y]);
	var n = (t = e.segment) == null ? void 0 : t.map((e) => e.y);
	return n == null || n.length === 0 ? [] : Zb(n);
}
var Nx = (e, t) => {
	if (e != null) {
		var n = e.flatMap((e) => t === "xAxis" ? jx(e) : Mx(e));
		if (n.length !== 0) return [Math.min(...n), Math.max(...n)];
	}
}, Px = z(Ox, z([Ex, lm], Nx), Ax, (e, t, n) => hx(e, n, t)), Fx = (e, t, n, r, i, a, o, s, c) => {
	if (n != null) return n;
	var l = o === "vertical" && s === "xAxis" || o === "horizontal" && s === "yAxis" ? hx(r, a, i) : hx(a, i), u = gp(t, l, e.allowDataOverflow);
	return u == null && e.allowDataOverflow && l == null && c != null ? c : u;
}, Ix = z([
	kb,
	ux,
	dx,
	fx,
	_x,
	Px,
	K,
	lm,
	z([kb], (e) => {
		if (!(e == null || e.type !== "number" || !("ticks" in e) || e.ticks == null)) {
			var t = Zb(e.ticks);
			if (t.length !== 0) return [Math.min(...t), Math.max(...t)];
		}
	}, { memoizeOptions: { resultEqualityCheck: mm } })
], Fx, { memoizeOptions: { resultEqualityCheck: mm } }), Lx = [0, 1], Rx = (e, t, n, r, i, a, o) => {
	if (!((e == null || n == null || n.length === 0) && o === void 0)) {
		var s = e.dataKey, c = e.type, l = Ws(t, a);
		if (l && s == null) {
			var u;
			return ep(0, (u = n == null ? void 0 : n.length) == null ? 0 : u);
		}
		return c === "category" ? yx(r, e, l) : i === "expand" && !l ? Lx : o;
	}
}, zx = z([
	kb,
	K,
	Gb,
	Jb,
	Ip,
	lm,
	Ix
], Rx), Bx = z([
	kb,
	Mb,
	Rp
], ab), Vx = (e, t, n) => {
	var r = t.niceTicks;
	if (r !== "none") {
		var i = lx(t), a = Array.isArray(i) && (i[0] === "auto" || i[1] === "auto");
		if ((r === "snap125" || r === "adaptive") && t != null && t.tickCount && pp(e)) {
			if (a) return Ap(e, t.tickCount, t.allowDecimals, r);
			if (t.type === "number") return jp(e, t.tickCount, t.allowDecimals, r);
		}
		if (r === "auto" && n === "linear" && t != null && t.tickCount) {
			if (a && pp(e)) return Ap(e, t.tickCount, t.allowDecimals, "adaptive");
			if (t.type === "number" && pp(e)) return jp(e, t.tickCount, t.allowDecimals, "adaptive");
		}
	}
}, Hx = z([
	zx,
	jb,
	Bx
], Vx), Ux = (e, t, n, r) => {
	if (r !== "angleAxis" && (e == null ? void 0 : e.type) === "number" && pp(t) && Array.isArray(n) && n.length > 0) {
		var i, a, o = t[0], s = (i = n[0]) == null ? 0 : i, c = t[1], l = (a = n[n.length - 1]) == null ? 0 : a;
		return [Math.min(o, s), Math.max(c, l)];
	}
	return t;
}, Wx = z([
	kb,
	zx,
	Hx,
	lm
], Ux), Gx = z(z(Jb, kb, (e, t) => {
	if (!(!t || t.type !== "number")) {
		var n = Infinity, r = Array.from(Zb(e.map((e) => e.value))).sort((e, t) => e - t), i = r[0], a = r[r.length - 1];
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
}), K, Pp, Cc, (e, t, n, r, i) => i, (e, t, n, r, i) => {
	if (!U(e)) return 0;
	var a = t === "vertical" ? r.height : r.width;
	if (i === "gap") return e * a / 2;
	if (i === "no-gap") {
		var o = hn(n, e * a), s = e * a / 2;
		return s - o - (s - o) / a * o;
	}
	return 0;
}), Kx = (e, t, n) => {
	var r = Cb(e, t);
	return r == null || typeof r.padding != "string" ? 0 : Gx(e, "xAxis", t, n, r.padding);
}, qx = (e, t, n) => {
	var r = Eb(e, t);
	return r == null || typeof r.padding != "string" ? 0 : Gx(e, "yAxis", t, n, r.padding);
}, Jx = z(Cb, Kx, (e, t) => {
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
}), Yx = z(Eb, qx, (e, t) => {
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
}), Xx = z([
	Cc,
	Jx,
	kc,
	Oc,
	(e, t, n) => n
], (e, t, n, r, i) => {
	var a = r.padding;
	return i ? [a.left, n.width - a.right] : [e.left + t.left, e.left + e.width - t.right];
}), Zx = z([
	Cc,
	K,
	Yx,
	kc,
	Oc,
	(e, t, n) => n
], (e, t, n, r, i, a) => {
	var o = i.padding;
	return a ? [r.height - o.bottom, o.top] : t === "horizontal" ? [e.top + e.height - n.bottom, e.top + n.top] : [e.top + n.top, e.top + e.height - n.bottom];
}), Qx = (e, t, n, r) => {
	var i;
	switch (t) {
		case "xAxis": return Xx(e, n, r);
		case "yAxis": return Zx(e, n, r);
		case "zAxis": return (i = Ob(e, n)) == null ? void 0 : i.range;
		case "angleAxis": return om(e);
		case "radiusAxis": return sm(e, n);
		default: return;
	}
}, $x = z([kb, Qx], Gp), eS = z([
	kb,
	Bx,
	z([Bx, Wx], bm),
	$x
], nb), tS = (e, t, n, r) => {
	if (!(n == null || n.dataKey == null)) {
		var i = n.type, a = n.scale;
		if (Ws(e, r) && (i === "number" || a !== "auto")) return t.map((e) => e.value);
	}
}, nS = z([
	K,
	Jb,
	jb,
	lm
], tS), rS = z([eS], ym);
z([eS], cb), z([eS, $b], sb), z([
	Lb,
	px,
	lm
], mx);
function iS(e, t) {
	return e.id < t.id ? -1 : +(e.id > t.id);
}
var aS = (e, t) => t, oS = (e, t, n) => n, sS = z(dc, aS, oS, (e, t, n) => e.filter((e) => e.orientation === t).filter((e) => e.mirror === n).sort(iS)), cS = z(fc, aS, oS, (e, t, n) => e.filter((e) => e.orientation === t).filter((e) => e.mirror === n).sort(iS)), lS = (e, t) => ({
	width: e.width,
	height: t.height
}), uS = (e, t) => ({
	width: typeof t.width == "number" ? t.width : 60,
	height: e.height
}), dS = z(Cc, Cb, lS), fS = (e, t, n) => {
	switch (t) {
		case "top": return e.top;
		case "bottom": return n - e.bottom;
		default: return 0;
	}
}, pS = (e, t, n) => {
	switch (t) {
		case "left": return e.left;
		case "right": return n - e.right;
		default: return 0;
	}
}, mS = z(cc, Cc, sS, aS, oS, (e, t, n, r, i) => {
	var a = {}, o;
	return n.forEach((n) => {
		var s = lS(t, n);
		o == null && (o = fS(t, r, e));
		var c = r === "top" && !i || r === "bottom" && i;
		a[n.id] = o - Number(c) * s.height, o += (c ? -1 : 1) * s.height;
	}), a;
}), hS = z(sc, Cc, cS, aS, oS, (e, t, n, r, i) => {
	var a = {}, o;
	return n.forEach((n) => {
		var s = uS(t, n);
		o == null && (o = pS(t, r, e));
		var c = r === "left" && !i || r === "right" && i;
		a[n.id] = o - Number(c) * s.width, o += (c ? -1 : 1) * s.width;
	}), a;
}), gS = z([
	Cc,
	Cb,
	(e, t) => {
		var n = Cb(e, t);
		if (n != null) return mS(e, n.orientation, n.mirror);
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
}), _S = z([
	Cc,
	Eb,
	(e, t) => {
		var n = Eb(e, t);
		if (n != null) return hS(e, n.orientation, n.mirror);
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
}), vS = z(Cc, Eb, (e, t) => ({
	width: typeof t.width == "number" ? t.width : 60,
	height: e.height
})), yS = (e, t, n) => {
	switch (t) {
		case "xAxis": return dS(e, n).width;
		case "yAxis": return vS(e, n).height;
		default: return;
	}
}, bS = (e, t, n, r) => {
	if (n != null) {
		var i = n.allowDuplicatedCategory, a = n.type, o = n.dataKey, s = Ws(e, r), c = t.map((e) => e.value), l = c.filter((e) => e != null);
		if (o && s && a === "category" && i && gn(l)) return c;
	}
}, xS = z([
	K,
	Jb,
	kb,
	lm
], bS);
z([
	K,
	Ab,
	Bx,
	rS,
	xS,
	nS,
	Qx,
	Hx,
	lm
], (e, t, n, r, i, a, o, s, c) => {
	if (t != null) {
		var l = Ws(e, c);
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
var SS = z([
	K,
	jb,
	Bx,
	rS,
	Hx,
	Qx,
	xS,
	nS,
	lm
], (e, t, n, r, i, a, o, s, c) => {
	if (!(t == null || r == null)) {
		var l = Ws(e, c), u = t.type, d = t.ticks, f = t.tickCount, p = n === "scaleBand" && typeof r.bandwidth == "function" ? r.bandwidth() / 2 : 2, m = u === "category" && r.bandwidth ? r.bandwidth() / p : 0;
		m = c === "angleAxis" && a != null && a.length >= 2 ? ln(a[0] - a[1]) * 2 * m : m;
		var h = d || i;
		return h ? h.map((e, t) => {
			var n = o ? o.indexOf(e) : e, i = r.map(n);
			return U(i) ? {
				index: t,
				coordinate: i + m,
				value: e,
				offset: m
			} : null;
		}).filter(xn) : l && s ? s.map((e, t) => {
			var n = r.map(e);
			return U(n) ? {
				coordinate: n + m,
				value: e,
				index: t,
				offset: m
			} : null;
		}).filter(xn) : r.ticks ? r.ticks(f).map((e, t) => {
			var n = r.map(e);
			return U(n) ? {
				coordinate: n + m,
				value: e,
				index: t,
				offset: m
			} : null;
		}).filter(xn) : r.domain().map((e, t) => {
			var n = r.map(e);
			return U(n) ? {
				coordinate: n + m,
				value: o ? o[e] : e,
				index: t,
				offset: m
			} : null;
		}).filter(xn);
	}
}), CS = z([
	K,
	jb,
	rS,
	Qx,
	xS,
	nS,
	lm
], (e, t, n, r, i, a, o) => {
	if (!(t == null || n == null || r == null || r[0] === r[1])) {
		var s = Ws(e, o), c = t.tickCount, l = 0;
		return l = o === "angleAxis" && (r == null ? void 0 : r.length) >= 2 ? ln(r[0] - r[1]) * 2 * l : l, s && a ? a.map((e, t) => {
			var r = n.map(e);
			return U(r) ? {
				coordinate: r + l,
				value: e,
				index: t,
				offset: l
			} : null;
		}).filter(xn) : n.ticks ? n.ticks(c).map((e, t) => {
			var r = n.map(e);
			return U(r) ? {
				coordinate: r + l,
				value: e,
				index: t,
				offset: l
			} : null;
		}).filter(xn) : n.domain().map((e, t) => {
			var r = n.map(e);
			return U(r) ? {
				coordinate: r + l,
				value: i ? i[e] : e,
				index: t,
				offset: l
			} : null;
		}).filter(xn);
	}
}), wS = z(kb, rS, (e, t) => {
	if (!(e == null || t == null)) return ub(ub({}, e), {}, { scale: t });
});
z((e, t, n) => Ob(e, n), z([z([
	kb,
	Bx,
	zx,
	$x
], nb)], ym), (e, t) => {
	if (!(e == null || t == null)) return ub(ub({}, e), {}, { scale: t });
});
var TS = z([
	K,
	dc,
	fc
], (e, t, n) => {
	switch (e) {
		case "horizontal": return t.some((e) => e.reversed) ? "right-to-left" : "left-to-right";
		case "vertical": return n.some((e) => e.reversed) ? "bottom-to-top" : "top-to-bottom";
		case "centric":
		case "radial": return "left-to-right";
		default: return;
	}
});
z([(e, t, n) => {
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
var ES = (e) => e.options.defaultTooltipEventType, DS = (e) => e.options.validateTooltipEventTypes;
function OS(e, t, n) {
	if (e == null) return t;
	var r = e ? "axis" : "item";
	return n == null ? t : n.includes(r) ? r : t;
}
function kS(e, t) {
	return OS(t, ES(e), DS(e));
}
function AS(e) {
	return R((t) => kS(t, e));
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineActiveLabel.js
var jS = (e, t) => {
	var n, r = Number(t);
	if (!(un(r) || t == null)) return r >= 0 ? e == null || (n = e[r]) == null ? void 0 : n.value : void 0;
}, MS = (e) => e.tooltip.settings, NS = {
	active: !1,
	index: null,
	dataKey: void 0,
	graphicalItemId: void 0,
	coordinate: void 0
}, PS = Bo({
	name: "tooltip",
	initialState: {
		itemInteraction: {
			click: NS,
			hover: NS
		},
		axisInteraction: {
			click: NS,
			hover: NS
		},
		keyboardInteraction: NS,
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
			prepare: To()
		},
		replaceTooltipEntrySettings: {
			reducer(e, t) {
				var n = t.payload, r = n.prev, i = n.next, a = uo(e).tooltipItemPayloads.indexOf(H(r));
				a > -1 && (e.tooltipItemPayloads[a] = H(i));
			},
			prepare: To()
		},
		removeTooltipEntrySettings: {
			reducer(e, t) {
				var n = uo(e).tooltipItemPayloads.indexOf(H(t.payload));
				n > -1 && e.tooltipItemPayloads.splice(n, 1);
			},
			prepare: To()
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
}), FS = PS.actions, IS = FS.addTooltipEntrySettings, LS = FS.replaceTooltipEntrySettings, RS = FS.removeTooltipEntrySettings, zS = FS.setTooltipSettingsState, BS = FS.setActiveMouseOverItemIndex, VS = FS.mouseLeaveItem, HS = FS.mouseLeaveChart, US = FS.setActiveClickItemIndex, WS = FS.setMouseOverAxisIndex, GS = FS.setMouseClickAxisIndex, KS = FS.setSyncInteraction, qS = FS.setKeyboardInteraction, JS = PS.reducer;
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineTooltipInteractionState.js
function YS(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function XS(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? YS(Object(n), !0).forEach(function(t) {
			ZS(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : YS(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function ZS(e, t, n) {
	return (t = QS(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function QS(e) {
	var t = $S(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function $S(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function eC(e, t, n) {
	return t === "axis" ? n === "click" ? e.axisInteraction.click : e.axisInteraction.hover : n === "click" ? e.itemInteraction.click : e.itemInteraction.hover;
}
function tC(e) {
	return e.index != null;
}
var nC = (e, t, n, r) => {
	if (t == null) return NS;
	var i = eC(e, t, n);
	if (i == null) return NS;
	if (i.active) return i;
	if (e.keyboardInteraction.active) return e.keyboardInteraction;
	if (e.syncInteraction.active && e.syncInteraction.index != null) return e.syncInteraction;
	var a = e.settings.active === !0;
	if (tC(i)) {
		if (a) return XS(XS({}, i), {}, { active: !0 });
	} else if (r != null) return {
		active: !0,
		coordinate: void 0,
		dataKey: void 0,
		index: r,
		graphicalItemId: void 0
	};
	return XS(XS({}, NS), {}, { coordinate: i.coordinate });
};
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineActiveTooltipIndex.js
function rC(e) {
	if (typeof e == "number") return Number.isFinite(e) ? e : void 0;
	if (e instanceof Date) {
		var t = e.valueOf();
		return Number.isFinite(t) ? t : void 0;
	}
	var n = Number(e);
	return Number.isFinite(n) ? n : void 0;
}
function iC(e, t) {
	var n = rC(e), r = t[0], i = t[1];
	return n !== void 0 && n >= Math.min(r, i) && n <= Math.max(r, i);
}
function aC(e, t, n) {
	if (n == null || t == null) return !0;
	var r = Hs(e, t);
	return r == null || !pp(n) || iC(r, n);
}
var oC = (e, t, n, r) => {
	var i = e == null ? void 0 : e.index;
	if (i == null) return null;
	var a = Number(i);
	if (!U(a)) return i;
	var o = 0, s = Infinity;
	t.length > 0 && (s = t.length - 1);
	var c = Math.max(o, Math.min(a, s)), l = t[c];
	return l == null || aC(l, n, r) ? String(c) : null;
}, sC = (e, t, n, r, i, a, o) => {
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
}, cC = (e, t, n, r) => {
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
}, lC = (e) => e.options.tooltipPayloadSearcher, uC = (e) => e.tooltip;
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineTooltipPayload.js
function dC(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function fC(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? dC(Object(n), !0).forEach(function(t) {
			pC(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : dC(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function pC(e, t, n) {
	return (t = mC(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function mC(e) {
	var t = hC(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function hC(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function gC(e) {
	if (typeof e == "string" || typeof e == "number") return e;
}
function _C(e) {
	if (typeof e == "string" || typeof e == "number" || typeof e == "boolean") return e;
}
function vC(e) {
	if (typeof e == "string" || typeof e == "number") return e;
	if (typeof e == "function") return (t) => e(t);
}
function yC(e) {
	if (typeof e == "string") return e;
}
function bC(e) {
	if (!(typeof e != "object" || !e)) return {
		name: "name" in e ? gC(e.name) : void 0,
		unit: "unit" in e ? _C(e.unit) : void 0,
		dataKey: "dataKey" in e ? vC(e.dataKey) : void 0,
		payload: "payload" in e ? e.payload : void 0,
		color: "color" in e ? yC(e.color) : void 0,
		fill: "fill" in e ? yC(e.fill) : void 0
	};
}
function xC(e, t) {
	return e == null ? t : e;
}
var SC = (e, t, n, r, i, a, o) => {
	if (!(t == null || a == null)) {
		var s = n.chartData, c = n.computedData, l = n.dataStartIndex, u = n.dataEndIndex;
		return e.reduce((e, n) => {
			var d, f = n.dataDefinedOnItem, p = n.settings, m = xC(f, s), h = Array.isArray(m) ? Fs(m, l, u) : m, g = (d = p == null ? void 0 : p.dataKey) == null ? r : d, _ = p == null ? void 0 : p.nameKey, v = r && Array.isArray(h) && !Array.isArray(h[0]) && o === "axis" ? vn(h, r, i) : a(h, t, c, _);
			if (Array.isArray(v)) v.forEach((t) => {
				var n, r, i = bC(t), a = i == null ? void 0 : i.name, o = i == null ? void 0 : i.dataKey, s = i == null ? void 0 : i.payload, c = fC(fC({}, p), {}, {
					name: a,
					unit: i == null ? void 0 : i.unit,
					color: (n = i == null ? void 0 : i.color) == null ? p == null ? void 0 : p.color : n,
					fill: (r = i == null ? void 0 : i.fill) == null ? p == null ? void 0 : p.fill : r
				});
				e.push(rc({
					tooltipEntrySettings: c,
					dataKey: o,
					payload: s,
					value: Hs(s, o),
					name: a == null ? void 0 : String(a)
				}));
			});
			else {
				var y;
				e.push(rc({
					tooltipEntrySettings: p,
					dataKey: g,
					payload: v,
					value: Hs(v, g),
					name: (y = Hs(v, _)) == null ? p == null ? void 0 : p.name : y
				}));
			}
			return e;
		}, []);
	}
}, CC = z([
	nx,
	Mb,
	Rp
], ab), wC = z([
	z([(e) => e.graphicalItems.cartesianItems, (e) => e.graphicalItems.polarItems], (e, t) => [...e, ...t]),
	nx,
	z([_m, vm], Nb)
], Ib, { memoizeOptions: { resultEqualityCheck: hm } }), TC = z([wC], (e) => e.filter(pm)), EC = z([wC], Vb, { memoizeOptions: { resultEqualityCheck: hm } }), DC = z([wC], (e) => e.some((e) => !e.data)), OC = z([EC, tp], Wb), kC = z([
	TC,
	tp,
	nx
], fm), AC = z([
	OC,
	nx,
	wC,
	tp,
	DC,
	EC
], qb), jC = z([nx], lx), MC = z([jC, z([nx], (e) => e.allowDataOverflow)], hp), NC = z([
	z([
		kC,
		z([wC], (e) => e.filter(pm)),
		Ip,
		Lp
	], ax),
	tp,
	_m,
	MC
], sx), PC = z([
	OC,
	nx,
	z([wC], zb),
	px,
	_m,
	op
], gx, { memoizeOptions: { resultEqualityCheck: mm } }), FC = z([z([
	bx,
	_m,
	vm
], xx), _m], Dx), IC = z([z([
	Cx,
	_m,
	vm
], xx), _m], kx), LC = z([
	nx,
	K,
	OC,
	AC,
	Ip,
	_m,
	z([
		nx,
		jC,
		MC,
		NC,
		PC,
		z([
			FC,
			z([z([
				Tx,
				_m,
				vm
			], xx), _m], Nx),
			IC
		], hx),
		K,
		_m
	], Fx)
], Rx), RC = z([
	nx,
	LC,
	z([
		LC,
		nx,
		CC
	], Vx),
	_m
], Ux), zC = (e) => Qx(e, _m(e), vm(e), !1), BC = z([nx, zC], Gp), VC = z([z([
	nx,
	CC,
	RC,
	BC
], nb)], ym), HC = z([
	K,
	nx,
	CC,
	VC,
	zC,
	z([
		K,
		AC,
		nx,
		_m
	], bS),
	z([
		K,
		AC,
		nx,
		_m
	], tS),
	_m
], (e, t, n, r, i, a, o, s) => {
	if (t) {
		var c = t.type, l = Ws(e, s);
		if (r) {
			var u = n === "scaleBand" && r.bandwidth ? r.bandwidth() / 2 : 2, d = c === "category" && r.bandwidth ? r.bandwidth() / u : 0;
			return d = s === "angleAxis" && i != null && (i == null ? void 0 : i.length) >= 2 ? ln(i[0] - i[1]) * 2 * d : d, l && o ? o.map((e, t) => {
				var n = r.map(e);
				return U(n) ? {
					coordinate: n + d,
					value: e,
					index: t,
					offset: d
				} : null;
			}).filter(xn) : r.domain().map((e, t) => {
				var n = r.map(e);
				return U(n) ? {
					coordinate: n + d,
					value: a ? a[e] : e,
					index: t,
					offset: d
				} : null;
			}).filter(xn);
		}
	}
}), UC = z([
	ES,
	DS,
	MS
], (e, t, n) => OS(n.shared, e, t)), WC = (e) => e.tooltip.settings.trigger, GC = (e) => e.tooltip.settings.defaultIndex, KC = z([
	uC,
	UC,
	WC,
	GC
], nC), qC = z([
	KC,
	OC,
	rx,
	LC
], oC), JC = z([HC, qC], jS), YC = z([KC], (e) => {
	if (e) return e.dataKey;
}), XC = z([KC], (e) => {
	if (e) return e.graphicalItemId;
}), ZC = z([
	uC,
	UC,
	WC,
	GC
], cC), QC = z([KC, z([
	sc,
	cc,
	K,
	Cc,
	HC,
	GC,
	ZC
], sC)], (e, t) => e != null && e.coordinate ? e.coordinate : t), $C = z([KC], (e) => {
	var t;
	return (t = e == null ? void 0 : e.active) != null && t;
});
z([z([
	ZC,
	qC,
	tp,
	rx,
	JC,
	lC,
	UC
], SC)], (e) => {
	if (e != null) {
		var t = e.map((e) => e.payload).filter((e) => e != null);
		return Array.from(new Set(t));
	}
});
//#endregion
//#region node_modules/recharts/es6/context/useTooltipAxis.js
function ew(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function tw(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? ew(Object(n), !0).forEach(function(t) {
			nw(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : ew(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function nw(e, t, n) {
	return (t = rw(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function rw(e) {
	var t = iw(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function iw(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var aw = () => R(nx), ow = () => {
	var e = aw(), t = R(HC), n = R(VC);
	return nc(!e || !n ? void 0 : tw(tw({}, e), {}, { scale: n }), t);
};
//#endregion
//#region node_modules/recharts/es6/util/getActiveCoordinate.js
function sw(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function cw(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? sw(Object(n), !0).forEach(function(t) {
			lw(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : sw(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function lw(e, t, n) {
	return (t = uw(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function uw(e) {
	var t = dw(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function dw(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var fw = (e, t, n, r) => {
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
}, pw = (e, t, n, r) => {
	var i = t.find((e) => e && e.index === n);
	if (i) {
		if (e === "centric") {
			var a = i.coordinate, o = r.radius;
			return cw(cw(cw({}, r), Of(r.cx, r.cy, o, a)), {}, {
				angle: a,
				radius: o
			});
		}
		var s = i.coordinate, c = r.angle;
		return cw(cw(cw({}, r), Of(r.cx, r.cy, s, c)), {}, {
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
function mw(e, t) {
	var n = e.relativeX, r = e.relativeY;
	return n >= t.left && n <= t.left + t.width && r >= t.top && r <= t.top + t.height;
}
var hw = (e, t, n, r, i) => {
	var a, o = (a = t == null ? void 0 : t.length) == null ? 0 : a;
	if (o <= 1 || e == null) return 0;
	if (r === "angleAxis" && i != null && Math.abs(Math.abs(i[1] - i[0]) - 360) <= 1e-6) for (var s = 0; s < o; s++) {
		var c, l, u, d, f, p = s > 0 ? (c = n[s - 1]) == null ? void 0 : c.coordinate : (l = n[o - 1]) == null ? void 0 : l.coordinate, m = (u = n[s]) == null ? void 0 : u.coordinate, h = s >= o - 1 ? (d = n[0]) == null ? void 0 : d.coordinate : (f = n[s + 1]) == null ? void 0 : f.coordinate, g = void 0;
		if (!(p == null || m == null || h == null)) if (ln(m - p) !== ln(h - m)) {
			var _ = [];
			if (ln(h - m) === ln(i[1] - i[0])) {
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
}, gw = () => R(Rp), _w = (e, t) => t, vw = (e, t, n) => n, yw = (e, t, n, r) => r, bw = z(HC, (e) => Ci(e, (e) => e.coordinate)), xw = z([
	uC,
	_w,
	vw,
	yw
], nC), Sw = z([
	xw,
	OC,
	rx,
	LC
], oC), Cw = (e, t, n) => {
	if (t != null) {
		var r = uC(e);
		return t === "axis" ? n === "hover" ? r.axisInteraction.hover.dataKey : r.axisInteraction.click.dataKey : n === "hover" ? r.itemInteraction.hover.dataKey : r.itemInteraction.click.dataKey;
	}
}, ww = z([
	uC,
	_w,
	vw,
	yw
], cC), Tw = z([
	sc,
	cc,
	K,
	Cc,
	HC,
	yw,
	ww
], sC), Ew = z([xw, Tw], (e, t) => {
	var n;
	return (n = e.coordinate) == null ? t : n;
}), Dw = z([HC, Sw], jS), Ow = z([
	ww,
	Sw,
	tp,
	rx,
	Dw,
	lC,
	_w
], SC), kw = z([xw, Sw], (e, t) => ({
	isActive: e.active && t != null,
	activeIndex: t
})), Aw = (e, t, n, r, i, a, o) => {
	if (!(!e || !n || !r || !i) && mw(e, o)) {
		var s = hw(ac(e, t), a, i, n, r), c = fw(t, i, s, e);
		return {
			activeIndex: String(s),
			activeCoordinate: c
		};
	}
}, jw = (e, t, n, r, i, a, o) => {
	if (!(!e || !r || !i || !a || !n)) {
		var s = Pf(e, n);
		if (s) {
			var c = hw(oc(s, t), o, a, r, i), l = pw(t, a, c, s);
			return {
				activeIndex: String(c),
				activeCoordinate: l
			};
		}
	}
}, Mw = (e, t, n, r, i, a, o, s) => {
	if (!(!e || !t || !r || !i || !a)) return t === "horizontal" || t === "vertical" ? Aw(e, t, r, i, a, o, s) : jw(e, t, n, r, i, a, o);
}, Nw = z((e) => e.zIndex.zIndexMap, (e, t) => t, (e, t, n) => n, (e, t, n) => {
	if (t != null) {
		var r = e[t];
		if (r != null) return n ? r.panoramaElement : r.element;
	}
}), Pw = z((e) => e.zIndex.zIndexMap, (e) => {
	var t = Object.keys(e).map((e) => parseInt(e, 10)).concat(Object.values(Hp));
	return Array.from(new Set(t)).sort((e, t) => e - t);
}, { memoizeOptions: { resultEqualityCheck: gm } });
//#endregion
//#region node_modules/recharts/es6/state/zIndexSlice.js
function Fw(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Iw(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Fw(Object(n), !0).forEach(function(t) {
			Lw(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Fw(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Lw(e, t, n) {
	return (t = Rw(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function Rw(e) {
	var t = zw(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function zw(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var Bw = { zIndexMap: Object.values(Hp).reduce((e, t) => Iw(Iw({}, e), {}, { [t]: {
	element: void 0,
	panoramaElement: void 0,
	consumers: 0
} }), {}) }, Vw = new Set(Object.values(Hp));
function Hw(e) {
	return Vw.has(e);
}
var Uw = Bo({
	name: "zIndex",
	initialState: Bw,
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
			prepare: To()
		},
		unregisterZIndexPortal: {
			reducer: (e, t) => {
				var n = t.payload.zIndex;
				e.zIndexMap[n] && (--e.zIndexMap[n].consumers, e.zIndexMap[n].consumers <= 0 && !Hw(n) && delete e.zIndexMap[n]);
			},
			prepare: To()
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
			prepare: To()
		},
		unregisterZIndexPortalElement: {
			reducer: (e, t) => {
				var n = t.payload.zIndex;
				e.zIndexMap[n] && (t.payload.isPanorama ? e.zIndexMap[n].panoramaElement = void 0 : e.zIndexMap[n].element = void 0);
			},
			prepare: To()
		}
	}
}), Ww = Uw.actions, Gw = Ww.registerZIndexPortal, Kw = Ww.unregisterZIndexPortal, qw = Ww.registerZIndexPortalElement, Jw = Ww.unregisterZIndexPortalElement, Yw = Uw.reducer, Xw = h();
function Zw(e) {
	var t = e.zIndex, n = e.children, r = _l() && t !== void 0 && t !== 0, i = Dc(), a = (0, C.useRef)(void 0), o = (0, C.useRef)(/* @__PURE__ */ new Set()), s = qr(), c = R((e) => Nw(e, t, i));
	if ((0, C.useLayoutEffect)(() => {
		if (!r) {
			var e = o.current;
			e.forEach((e) => {
				s(Kw({ zIndex: e }));
			}), e.clear(), a.current = void 0;
			return;
		}
		if (o.current.has(t) || (s(Gw({ zIndex: t })), o.current.add(t)), c) {
			a.current = c;
			var n = o.current;
			n.forEach((e) => {
				e !== t && (s(Kw({ zIndex: e })), n.delete(e));
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
				s(Kw({ zIndex: e }));
			}), e.clear();
		};
	}, [s]), !r) return n;
	var l = c == null ? a.current : c;
	return l ? /*#__PURE__*/ (0, Xw.createPortal)(n, l) : null;
}
//#endregion
//#region node_modules/recharts/es6/component/Cursor.js
function Qw() {
	return Qw = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, Qw.apply(null, arguments);
}
function $w(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function eT(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? $w(Object(n), !0).forEach(function(t) {
			tT(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : $w(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function tT(e, t, n) {
	return (t = nT(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function nT(e) {
	var t = rT(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function rT(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function iT(e) {
	var t = e.cursor, n = e.cursorComp, r = e.cursorProps;
	return /*#__PURE__*/ (0, C.isValidElement)(t) ? /*#__PURE__*/ (0, C.cloneElement)(t, r) : /*#__PURE__*/ (0, C.createElement)(n, r);
}
function aT(e) {
	var t, n = e.coordinate, r = e.payload, i = e.index, a = e.offset, o = e.tooltipAxisBandSize, s = e.layout, c = e.cursor, l = e.tooltipEventType, u = e.chartName, d = n, f = r, p = i;
	if (!c || !d || u !== "ScatterChart" && l !== "axis") return null;
	var m, h, g;
	if (u === "ScatterChart") m = d, h = od, g = Hp.cursorLine;
	else if (u === "BarChart") m = sd(s, d, a, o), h = bf, g = Hp.cursorRectangle;
	else if (s === "radial" && Cn(d)) {
		var _ = Ff(d), v = _.cx, y = _.cy, b = _.radius;
		m = {
			cx: v,
			cy: y,
			startAngle: _.startAngle,
			endAngle: _.endAngle,
			innerRadius: b,
			outerRadius: b
		}, h = Xf, g = Hp.cursorLine;
	} else m = { points: Zf(s, d, a) }, h = Yu, g = Hp.cursorLine;
	var x = typeof c == "object" && "className" in c ? c.className : void 0, S = eT(eT(eT(eT({
		stroke: "#ccc",
		pointerEvents: "none"
	}, a), m), Be(c)), {}, {
		payload: f,
		payloadIndex: p,
		className: Ne("recharts-tooltip-cursor", x)
	});
	return /*#__PURE__*/ C.createElement(Zw, { zIndex: (t = e.zIndex) == null ? g : t }, /*#__PURE__*/ C.createElement(iT, {
		cursor: c,
		cursorComp: h,
		cursorProps: S
	}));
}
function oT(e) {
	var t = ow(), n = dl(), r = ml(), i = gw();
	return t == null || n == null || r == null || i == null ? null : /*#__PURE__*/ C.createElement(aT, Qw({}, e, {
		offset: n,
		layout: r,
		tooltipAxisBandSize: t,
		chartName: i
	}));
}
//#endregion
//#region node_modules/recharts/es6/context/tooltipPortalContext.js
var sT = /*#__PURE__*/ (0, C.createContext)(null), cT = () => (0, C.useContext)(sT), lT = (/* @__PURE__ */ l((/* @__PURE__ */ o(((e, t) => {
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
})))(), 1)).default, uT = new lT(), dT = "recharts.syncEvent.tooltip", fT = "recharts.syncEvent.brush", pT = (e, t) => {
	if (t && Array.isArray(e)) {
		var n = Number.parseInt(t, 10);
		if (!un(n)) return e[n];
	}
}, mT = Bo({
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
}), hT = mT.reducer, gT = mT.actions.createEventEmitter;
//#endregion
//#region node_modules/recharts/es6/synchronisation/syncSelectors.js
function _T(e) {
	return e.tooltip.syncInteraction;
}
var vT = Bo({
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
}), yT = vT.actions, bT = yT.setChartData, xT = yT.setDataStartEndIndexes;
yT.setComputedData;
var ST = vT.reducer, CT = ["x", "y"];
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
	if (e == null) return {};
	var n, r, i = AT(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function AT(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function jT() {
	var e = R(zp), t = R(Vp), n = qr(), r = R(Bp), i = R(HC), a = ml(), o = ll();
	(0, C.useEffect)(() => {
		if (e == null) return Sn;
		var s = (s, c, l) => {
			if (t !== l && e === s) {
				if (c.payload.active === !1) {
					n(KS({
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
						var d = c.payload.coordinate, f = d.x, p = d.y, m = kT(d, CT), h = c.payload.sourceViewBox, g = h.x, _ = h.y, v = h.width, y = h.height, b = TT(TT({}, m), {}, {
							x: o.x + (v ? (f - g) / v : 0) * o.width,
							y: o.y + (y ? (p - _) / y : 0) * o.height
						});
						n(TT(TT({}, c), {}, { payload: TT(TT({}, c.payload), {}, { coordinate: b }) }));
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
						n(KS({
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
						n(KS({
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
					n(KS({
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
		return uT.on(dT, s), () => {
			uT.off(dT, s);
		};
	}, [
		R((e) => e.rootProps.className),
		n,
		t,
		e,
		r,
		i,
		a,
		o
	]);
}
function MT() {
	var e = R(zp), t = R(Vp), n = qr();
	(0, C.useEffect)(() => {
		if (e == null) return Sn;
		var r = (r, i, a) => {
			t !== a && e === r && n(xT(i));
		};
		return uT.on(fT, r), () => {
			uT.off(fT, r);
		};
	}, [
		n,
		t,
		e
	]);
}
function NT() {
	var e = qr();
	(0, C.useEffect)(() => {
		e(gT());
	}, [e]), jT(), MT();
}
function PT(e, t, n, r, i, a) {
	var o = R((n) => Cw(n, e, t)), s = R(XC), c = R(Vp), l = R(zp), u = R(Bp), d = R(_T), f = (d == null ? void 0 : d.sourceViewBox) != null, p = ll();
	(0, C.useEffect)(() => {
		if (!f && l != null && c != null) {
			var e = KS({
				active: a,
				coordinate: n,
				dataKey: o,
				index: i,
				label: typeof r == "number" ? String(r) : r,
				sourceViewBox: p,
				graphicalItemId: s
			});
			uT.emit(dT, l, e, c);
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
function FT(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function IT(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? FT(Object(n), !0).forEach(function(t) {
			LT(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : FT(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function LT(e, t, n) {
	return (t = RT(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function RT(e) {
	var t = zT(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function zT(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function BT(e, t) {
	return GT(e) || WT(e, t) || HT(e, t) || VT();
}
function VT() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function HT(e, t) {
	if (e) {
		if (typeof e == "string") return UT(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? UT(e, t) : void 0;
	}
}
function UT(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function WT(e, t) {
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
function GT(e) {
	if (Array.isArray(e)) return e;
}
function KT(e) {
	return e.dataKey;
}
function qT(e, t) {
	return /*#__PURE__*/ C.isValidElement(e) ? /*#__PURE__*/ C.cloneElement(e, t) : typeof e == "function" ? /*#__PURE__*/ C.createElement(e, t) : /*#__PURE__*/ C.createElement(au, t);
}
var JT = [], YT = {
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
function XT(e) {
	var t, n, r = Mn(e, YT), i = r.active, a = r.allowEscapeViewBox, o = r.animationDuration, s = r.animationEasing, c = r.content, l = r.filterNull, u = r.isAnimationActive, d = r.offset, f = r.payloadUniqBy, p = r.position, m = r.reverseDirection, h = r.useTranslate3d, g = r.wrapperStyle, _ = r.cursor, v = r.shared, y = r.trigger, b = r.defaultIndex, x = r.portal, S = r.axisId, w = qr(), T = typeof b == "number" ? String(b) : b;
	(0, C.useEffect)(() => {
		w(zS({
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
	var E = ll(), D = Pu(), O = AS(v), k = (t = R((e) => kw(e, O, y, T))) == null ? {} : t, A = k.activeIndex, j = k.isActive, M = R((e) => Ow(e, O, y, T)), N = R((e) => Dw(e, O, y, T)), P = R((e) => Ew(e, O, y, T)), F = M, ee = cT(), te = (n = i == null ? j : i) != null && n, ne = BT(Fi([F, te]), 2), re = ne[0], ie = ne[1], ae = O === "axis" ? N : void 0;
	PT(O, y, P, ae, A, te);
	var oe = x == null ? ee : x;
	if (oe == null || E == null || O == null) return null;
	var se = F == null ? JT : F;
	te || (se = JT), l && se.length && (se = zr(se.filter((e) => e.value != null && (e.hide !== !0 || r.includeHidden)), f, KT));
	var ce = se.length > 0, le = IT(IT({}, r), {}, {
		payload: se,
		label: ae,
		active: te,
		activeIndex: A,
		coordinate: P,
		accessibilityLayer: D
	}), ue = /*#__PURE__*/ C.createElement(Nu, {
		allowEscapeViewBox: a,
		animationDuration: o,
		animationEasing: s,
		isAnimationActive: u,
		active: te,
		coordinate: P,
		hasPayload: ce,
		offset: d,
		position: p,
		reverseDirection: m,
		useTranslate3d: h,
		viewBox: E,
		wrapperStyle: g,
		lastBoundingBox: re,
		innerRef: ie,
		hasPortalFromProps: !!x
	}, qT(c, le));
	return /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ (0, Xw.createPortal)(ue, oe), te && /*#__PURE__*/ C.createElement(oT, {
		cursor: _,
		tooltipEventType: O,
		coordinate: P,
		payload: se,
		index: A
	}));
}
//#endregion
//#region node_modules/recharts/es6/component/Cell.js
var ZT = (e) => null;
ZT.displayName = "Cell";
//#endregion
//#region node_modules/recharts/es6/util/LRUCache.js
function QT(e, t, n) {
	return (t = $T(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function $T(e) {
	var t = eE(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function eE(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var tE = class {
	constructor(e) {
		QT(this, "cache", /* @__PURE__ */ new Map()), this.maxSize = e;
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
function nE(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function rE(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? nE(Object(n), !0).forEach(function(t) {
			iE(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : nE(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function iE(e, t, n) {
	return (t = aE(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function aE(e) {
	var t = oE(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function oE(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var sE = rE({}, {
	cacheSize: 2e3,
	enableCache: !0
}), cE = new tE(sE.cacheSize), lE = {
	position: "absolute",
	top: "-20000px",
	left: 0,
	padding: 0,
	margin: 0,
	border: "none",
	whiteSpace: "pre"
}, uE = "recharts_measurement_span";
function dE(e, t) {
	return `${e}|${t.fontSize || ""}|${t.fontFamily || ""}|${t.fontWeight || ""}|${t.fontStyle || ""}|${t.letterSpacing || ""}|${t.textTransform || ""}`;
}
var fE = (e, t) => {
	try {
		var n = document.getElementById(uE);
		n || (n = document.createElement("span"), n.setAttribute("id", uE), n.setAttribute("aria-hidden", "true"), document.body.appendChild(n)), Object.assign(n.style, lE, t), n.textContent = `${e}`;
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
}, pE = function(e) {
	var t = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : {};
	if (e == null || fu.isSsr) return {
		width: 0,
		height: 0
	};
	if (!sE.enableCache) return fE(e, t);
	var n = dE(e, t), r = cE.get(n);
	if (r) return r;
	var i = fE(e, t);
	return cE.set(n, i), i;
}, mE;
function hE(e, t) {
	return bE(e) || yE(e, t) || _E(e, t) || gE();
}
function gE() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function _E(e, t) {
	if (e) {
		if (typeof e == "string") return vE(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? vE(e, t) : void 0;
	}
}
function vE(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function yE(e, t) {
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
function bE(e) {
	if (Array.isArray(e)) return e;
}
function xE(e, t, n) {
	return (t = SE(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function SE(e) {
	var t = CE(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function CE(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var wE = /(-?\d+(?:\.\d+)?[a-zA-Z%]*)([*/])(-?\d+(?:\.\d+)?[a-zA-Z%]*)/, TE = /(-?\d+(?:\.\d+)?[a-zA-Z%]*)([+-])(-?\d+(?:\.\d+)?[a-zA-Z%]*)/, EE = /^(px|cm|vh|vw|em|rem|%|mm|in|pt|pc|ex|ch|vmin|vmax|Q)$/, DE = /(-?\d+(?:\.\d+)?)([a-zA-Z%]+)?/, OE = {
	cm: 96 / 2.54,
	mm: 96 / 25.4,
	pt: 96 / 72,
	pc: 96 / 6,
	in: 96,
	Q: 96 / (2.54 * 40),
	px: 1
}, kE = [
	"cm",
	"mm",
	"pt",
	"pc",
	"in",
	"Q",
	"px"
];
function AE(e) {
	return kE.includes(e);
}
var jE = "NaN";
function ME(e, t) {
	return e * OE[t];
}
var NE = class e {
	static parse(t) {
		var n, r = hE((n = DE.exec(t)) == null ? [] : n, 3), i = r[1], a = r[2];
		return i == null ? e.NaN : new e(parseFloat(i), a == null ? "" : a);
	}
	constructor(e, t) {
		this.num = e, this.unit = t, this.num = e, this.unit = t, un(e) && (this.unit = ""), t !== "" && !EE.test(t) && (this.num = NaN, this.unit = ""), AE(t) && (this.num = ME(e, t), this.unit = "px");
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
		return un(this.num);
	}
};
mE = NE, xE(NE, "NaN", new mE(NaN, ""));
function PE(e) {
	if (e == null || e.includes(jE)) return jE;
	for (var t = e; t.includes("*") || t.includes("/");) {
		var n, r = hE((n = wE.exec(t)) == null ? [] : n, 4), i = r[1], a = r[2], o = r[3], s = NE.parse(i == null ? "" : i), c = NE.parse(o == null ? "" : o), l = a === "*" ? s.multiply(c) : s.divide(c);
		if (l.isNaN()) return jE;
		t = t.replace(wE, l.toString());
	}
	for (; t.includes("+") || /.-\d+(?:\.\d+)?/.test(t);) {
		var u, d = hE((u = TE.exec(t)) == null ? [] : u, 4), f = d[1], p = d[2], m = d[3], h = NE.parse(f == null ? "" : f), g = NE.parse(m == null ? "" : m), _ = p === "+" ? h.add(g) : h.subtract(g);
		if (_.isNaN()) return jE;
		t = t.replace(TE, _.toString());
	}
	return t;
}
var FE = /\(([^()]*)\)/;
function IE(e) {
	for (var t = e, n; (n = FE.exec(t)) != null;) {
		var r = hE(n, 2)[1];
		t = t.replace(FE, PE(r));
	}
	return t;
}
function LE(e) {
	var t = e.replace(/\s+/g, "");
	return t = IE(t), t = PE(t), t;
}
function RE(e) {
	try {
		return LE(e);
	} catch (e) {
		return jE;
	}
}
function zE(e) {
	var t = RE(e.slice(5, -1));
	return t === jE ? "" : t;
}
//#endregion
//#region node_modules/recharts/es6/component/Text.js
var BE = [
	"x",
	"y",
	"lineHeight",
	"capHeight",
	"fill",
	"scaleToFit",
	"textAnchor",
	"verticalAnchor"
], VE = [
	"dx",
	"dy",
	"angle",
	"className",
	"breakAll"
];
function HE() {
	return HE = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, HE.apply(null, arguments);
}
function UE(e, t) {
	if (e == null) return {};
	var n, r, i = WE(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function WE(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function GE(e, t) {
	return XE(e) || YE(e, t) || qE(e, t) || KE();
}
function KE() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function qE(e, t) {
	if (e) {
		if (typeof e == "string") return JE(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? JE(e, t) : void 0;
	}
}
function JE(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function YE(e, t) {
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
function XE(e) {
	if (Array.isArray(e)) return e;
}
var ZE = /[ \f\n\r\t\v\u2028\u2029]+/, QE = (e) => {
	var t = e.children, n = e.breakAll, r = e.style;
	try {
		var i = [];
		return yn(t) || (i = n ? t.toString().split("") : t.toString().split(ZE)), {
			wordsWithComputedWidth: i.map((e) => ({
				word: e,
				width: pE(e, r).width
			})),
			spaceWidth: n ? 0 : pE("\xA0", r).width
		};
	} catch (e) {
		return null;
	}
};
function $E(e) {
	return e === "start" || e === "middle" || e === "end" || e === "inherit";
}
function eD(e) {
	return yn(e) || typeof e == "string" || typeof e == "number" || typeof e == "boolean";
}
var tD = (e, t, n, r) => e.reduce((e, i) => {
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
}, []), nD = (e) => e.reduce((e, t) => e.width > t.width ? e : t), rD = "…", iD = (e, t, n, r, i, a, o, s) => {
	var c = QE({
		breakAll: n,
		style: r,
		children: e.slice(0, t) + rD
	});
	if (!c) return [!1, []];
	var l = tD(c.wordsWithComputedWidth, a, o, s);
	return [l.length > i || nD(l).width > Number(a), l];
}, aD = (e, t, n, r, i) => {
	var a = e.maxLines, o = e.children, s = e.style, c = e.breakAll, l = L(a), u = String(o), d = tD(t, r, n, i);
	if (!l || i || !(d.length > a || nD(d).width > Number(r))) return d;
	for (var f = 0, p = u.length - 1, m = 0, h; f <= p && m <= u.length - 1;) {
		var g = Math.floor((f + p) / 2), _ = GE(iD(u, g - 1, c, s, a, r, n, i), 2), v = _[0], y = _[1], b = GE(iD(u, g, c, s, a, r, n, i), 1)[0];
		if (!v && !b && (f = g + 1), v && b && (p = g - 1), !v && b) {
			h = y;
			break;
		}
		m++;
	}
	return h || d;
}, oD = (e) => [{
	words: yn(e) ? [] : e.toString().split(ZE),
	width: void 0
}], sD = (e) => {
	var t = e.width, n = e.scaleToFit, r = e.children, i = e.style, a = e.breakAll, o = e.maxLines;
	if ((t || n) && !fu.isSsr) {
		var s, c, l = QE({
			breakAll: a,
			children: r,
			style: i
		});
		if (l) {
			var u = l.wordsWithComputedWidth, d = l.spaceWidth;
			s = u, c = d;
		} else return oD(r);
		return aD({
			breakAll: a,
			children: r,
			maxLines: o,
			style: i
		}, s, c, t, !!n);
	}
	return oD(r);
}, cD = "#808080", lD = {
	angle: 0,
	breakAll: !1,
	capHeight: "0.71em",
	fill: cD,
	lineHeight: "1em",
	scaleToFit: !1,
	textAnchor: "start",
	verticalAnchor: "end",
	x: 0,
	y: 0
}, uD = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = Mn(e, lD), r = n.x, i = n.y, a = n.lineHeight, o = n.capHeight, s = n.fill, c = n.scaleToFit, l = n.textAnchor, u = n.verticalAnchor, d = UE(n, BE), f = (0, C.useMemo)(() => sD({
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
	]), p = d.dx, m = d.dy, h = d.angle, g = d.className, _ = d.breakAll, v = UE(d, VE);
	if (!fn(r) || !fn(i) || f.length === 0) return null;
	var y = Number(r) + (L(p) ? p : 0), b = Number(i) + (L(m) ? m : 0);
	if (!U(y) || !U(b)) return null;
	var x;
	switch (u) {
		case "start":
			x = zE(`calc(${o})`);
			break;
		case "middle":
			x = zE(`calc(${(f.length - 1) / 2} * -${a} + (${o} / 2))`);
			break;
		default:
			x = zE(`calc(${f.length - 1} * -${a})`);
			break;
	}
	var S = [], w = f[0];
	if (c && w != null) {
		var T = w.width, E = d.width;
		S.push(`scale(${L(E) && L(T) ? E / T : 1})`);
	}
	return h && S.push(`rotate(${h}, ${y}, ${b})`), S.length && (v.transform = S.join(" ")), /*#__PURE__*/ C.createElement("text", HE({}, Ve(v), {
		ref: t,
		x: y,
		y: b,
		className: Ne("recharts-text", g),
		textAnchor: l,
		fill: s.includes("url") ? cD : s
	}), f.map((e, t) => {
		var n = e.words.join(_ ? "" : " ");
		return /*#__PURE__*/ C.createElement("tspan", {
			x: y,
			dy: t === 0 ? x : a,
			key: `${n}-${t}`
		}, n);
	}));
});
uD.displayName = "Text";
//#endregion
//#region node_modules/recharts/es6/cartesian/getCartesianPosition.js
function dD(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function fD(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? dD(Object(n), !0).forEach(function(t) {
			pD(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : dD(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function pD(e, t, n) {
	return (t = mD(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function mD(e) {
	var t = hD(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function hD(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var gD = (e) => {
	var t = e.viewBox, n = e.position, r = e.offset, i = r === void 0 ? 0 : r, a = e.parentViewBox, o = e.clamp, s = cl(t), c = s.x, l = s.y, u = s.height, d = s.upperWidth, f = s.lowerWidth, p = c, m = c + (d - f) / 2, h = (p + m) / 2, g = (d + f) / 2, _ = p + d / 2, v = u >= 0 ? 1 : -1, y = v * i, b = v > 0 ? "end" : "start", x = v > 0 ? "start" : "end", S = d >= 0 ? 1 : -1, C = S * i, w = S > 0 ? "end" : "start", T = S > 0 ? "start" : "end", E = a;
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
	return n === "insideLeft" ? fD({
		x: h + C,
		y: l + u / 2,
		horizontalAnchor: T,
		verticalAnchor: "middle"
	}, j) : n === "insideRight" ? fD({
		x: h + g - C,
		y: l + u / 2,
		horizontalAnchor: w,
		verticalAnchor: "middle"
	}, j) : n === "insideTop" ? fD({
		x: p + d / 2,
		y: l + y,
		horizontalAnchor: "middle",
		verticalAnchor: x
	}, j) : n === "insideBottom" ? fD({
		x: m + f / 2,
		y: l + u - y,
		horizontalAnchor: "middle",
		verticalAnchor: b
	}, j) : n === "insideTopLeft" ? fD({
		x: p + C,
		y: l + y,
		horizontalAnchor: T,
		verticalAnchor: x
	}, j) : n === "insideTopRight" ? fD({
		x: p + d - C,
		y: l + y,
		horizontalAnchor: w,
		verticalAnchor: x
	}, j) : n === "insideBottomLeft" ? fD({
		x: m + C,
		y: l + u - y,
		horizontalAnchor: T,
		verticalAnchor: b
	}, j) : n === "insideBottomRight" ? fD({
		x: m + f - C,
		y: l + u - y,
		horizontalAnchor: w,
		verticalAnchor: b
	}, j) : n && typeof n == "object" && (L(n.x) || dn(n.x)) && (L(n.y) || dn(n.y)) ? fD({
		x: c + hn(n.x, g),
		y: l + hn(n.y, u),
		horizontalAnchor: "end",
		verticalAnchor: "end"
	}, j) : fD({
		x: _,
		y: l + u / 2,
		horizontalAnchor: "middle",
		verticalAnchor: "middle"
	}, j);
}, _D = ["labelRef"], vD = ["content"];
function yD(e, t) {
	if (e == null) return {};
	var n, r, i = bD(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function bD(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function xD(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function SD(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? xD(Object(n), !0).forEach(function(t) {
			CD(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : xD(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function CD(e, t, n) {
	return (t = wD(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function wD(e) {
	var t = TD(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function TD(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function ED() {
	return ED = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, ED.apply(null, arguments);
}
var DD = /*#__PURE__*/ (0, C.createContext)(null), OD = (e) => {
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
	return /*#__PURE__*/ C.createElement(DD.Provider, { value: c }, s);
}, kD = () => {
	var e = (0, C.useContext)(DD), t = ll();
	return e || (t ? cl(t) : void 0);
}, AD = /*#__PURE__*/ (0, C.createContext)(null), jD = () => {
	var e = (0, C.useContext)(AD), t = R(cm);
	return e || t;
}, MD = (e) => {
	var t = e.value, n = e.formatter, r = yn(e.children) ? t : e.children;
	return typeof n == "function" ? n(r) : r;
}, ND = (e) => e != null && typeof e == "function", PD = (e, t) => ln(t - e) * Math.min(Math.abs(t - e), 360), FD = (e, t, n, r, i) => {
	var a = e.offset, o = e.className, s = i.cx, c = i.cy, l = i.innerRadius, u = i.outerRadius, d = i.startAngle, f = i.endAngle, p = i.clockWise, m = (l + u) / 2, h = PD(d, f), g = h >= 0 ? 1 : -1, _, v;
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
	var y = Of(s, c, m, _), b = Of(s, c, m, _ + (v ? 1 : -1) * 359), x = `M${y.x},${y.y}
    A${m},${m},0,1,${+!v},
    ${b.x},${b.y}`, S = yn(e.id) ? mn("recharts-radial-line-") : e.id;
	return /*#__PURE__*/ C.createElement("text", ED({}, r, {
		dominantBaseline: "central",
		className: Ne("recharts-radial-bar-label", o)
	}), /*#__PURE__*/ C.createElement("defs", null, /*#__PURE__*/ C.createElement("path", {
		id: S,
		d: x
	})), /*#__PURE__*/ C.createElement("textPath", { xlinkHref: `#${S}` }, n));
}, ID = (e, t, n) => {
	var r = e.cx, i = e.cy, a = e.innerRadius, o = e.outerRadius, s = (e.startAngle + e.endAngle) / 2;
	if (n === "outside") {
		var c = Of(r, i, o + t, s), l = c.x;
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
	var u = Of(r, i, (a + o) / 2, s);
	return {
		x: u.x,
		y: u.y,
		textAnchor: "middle",
		verticalAnchor: "middle"
	};
}, LD = (e) => e != null && "cx" in e && L(e.cx), RD = {
	angle: 0,
	offset: 5,
	zIndex: Hp.label,
	position: "middle",
	textBreakAll: !1
};
function zD(e) {
	if (!LD(e)) return e;
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
function BD(e) {
	var t = Mn(e, RD), n = t.viewBox, r = t.parentViewBox, i = t.position, a = t.value, o = t.children, s = t.content, c = t.className, l = c === void 0 ? "" : c, u = t.textBreakAll, d = t.labelRef, f = jD(), p = kD(), m = n == null ? i === "center" || f == null ? p : f : LD(n) ? n : cl(n), h, g, _ = zD(m);
	if (!m || yn(a) && yn(o) && !/*#__PURE__*/ (0, C.isValidElement)(s) && typeof s != "function") return null;
	var v = SD(SD({}, t), {}, { viewBox: m });
	if (/*#__PURE__*/ (0, C.isValidElement)(s)) return v.labelRef, /*#__PURE__*/ (0, C.cloneElement)(s, yD(v, _D));
	if (typeof s == "function") {
		if (v.content, h = /*#__PURE__*/ (0, C.createElement)(s, yD(v, vD)), /*#__PURE__*/ (0, C.isValidElement)(h)) return h;
	} else h = MD(t);
	var y = Ve(t);
	if (LD(m)) {
		if (i === "insideStart" || i === "insideEnd" || i === "end") return FD(t, i, h, y, m);
		g = ID(m, t.offset, t.position);
	} else {
		if (!_) return null;
		var b = gD({
			viewBox: _,
			position: i,
			offset: t.offset,
			parentViewBox: LD(r) ? void 0 : r,
			clamp: !0
		});
		g = SD(SD({
			x: b.x,
			y: b.y,
			textAnchor: b.horizontalAnchor,
			verticalAnchor: b.verticalAnchor
		}, b.width === void 0 ? {} : { width: b.width }), b.height === void 0 ? {} : { height: b.height });
	}
	return /*#__PURE__*/ C.createElement(Zw, { zIndex: t.zIndex }, /*#__PURE__*/ C.createElement(uD, ED({
		ref: d,
		className: Ne("recharts-label", l)
	}, y, g, {
		textAnchor: $E(y.textAnchor) ? y.textAnchor : g.textAnchor,
		breakAll: u
	}), h));
}
BD.displayName = "Label";
var VD = (e, t, n) => {
	if (!e) return null;
	var r = {
		viewBox: t,
		labelRef: n
	};
	return e === !0 ? /*#__PURE__*/ C.createElement(BD, ED({ key: "label-implicit" }, r)) : fn(e) ? /*#__PURE__*/ C.createElement(BD, ED({
		key: "label-implicit",
		value: e
	}, r)) : /*#__PURE__*/ (0, C.isValidElement)(e) ? e.type === BD ? /*#__PURE__*/ (0, C.cloneElement)(e, SD({ key: "label-implicit" }, r)) : /*#__PURE__*/ C.createElement(BD, ED({
		key: "label-implicit",
		content: e
	}, r)) : ND(e) ? /*#__PURE__*/ C.createElement(BD, ED({
		key: "label-implicit",
		content: e
	}, r)) : e && typeof e == "object" ? /*#__PURE__*/ C.createElement(BD, ED({}, e, { key: "label-implicit" }, r)) : null;
};
function HD(e) {
	var t = e.label, n = e.labelRef;
	return VD(t, kD(), n) || null;
}
//#endregion
//#region node_modules/recharts/es6/component/LabelList.js
var UD = ["valueAccessor"], WD = [
	"dataKey",
	"clockWise",
	"id",
	"textBreakAll",
	"zIndex"
];
function GD() {
	return GD = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, GD.apply(null, arguments);
}
function KD(e, t) {
	if (e == null) return {};
	var n, r, i = qD(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function qD(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var JD = (e) => {
	var t = Array.isArray(e.value) ? e.value[e.value.length - 1] : e.value;
	if (eD(t)) return t;
}, YD = /*#__PURE__*/ (0, C.createContext)(void 0), XD = YD.Provider, ZD = /*#__PURE__*/ (0, C.createContext)(void 0);
ZD.Provider;
function QD() {
	return (0, C.useContext)(YD);
}
function $D() {
	return (0, C.useContext)(ZD);
}
function eO(e) {
	var t = e.valueAccessor, n = t === void 0 ? JD : t, r = KD(e, UD), i = r.dataKey;
	r.clockWise;
	var a = r.id, o = r.textBreakAll, s = r.zIndex, c = KD(r, WD), l = QD(), u = $D(), d = l || u;
	return !d || !d.length ? null : /*#__PURE__*/ C.createElement(Zw, { zIndex: s == null ? Hp.label : s }, /*#__PURE__*/ C.createElement(Ze, { className: "recharts-label-list" }, d.map((e, t) => {
		var s, l = yn(i) ? n(e, t) : Hs(e.payload, i), u = yn(a) ? {} : { id: `${a}-${t}` };
		return /*#__PURE__*/ C.createElement(BD, GD({ key: `label-${t}` }, Ve(e), c, u, {
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
eO.displayName = "LabelList";
function tO(e) {
	var t = e.label;
	return t ? t === !0 ? /*#__PURE__*/ C.createElement(eO, { key: "labelList-implicit" }) : /*#__PURE__*/ C.isValidElement(t) || ND(t) ? /*#__PURE__*/ C.createElement(eO, {
		key: "labelList-implicit",
		content: t
	}) : typeof t == "object" ? /*#__PURE__*/ C.createElement(eO, GD({ key: "labelList-implicit" }, t, { type: String(t.type) })) : null : null;
}
//#endregion
//#region node_modules/recharts/es6/state/polarAxisSlice.js
var nO = Bo({
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
}), rO = nO.actions;
rO.addRadiusAxis, rO.removeRadiusAxis, rO.addAngleAxis, rO.removeAngleAxis;
var iO = nO.reducer;
//#endregion
//#region node_modules/recharts/es6/util/getClassNameFromUnknown.js
function aO(e) {
	return e && typeof e == "object" && "className" in e && typeof e.className == "string" ? e.className : "";
}
//#endregion
//#region node_modules/react-is/cjs/react-is.production.min.js
var oO = /* @__PURE__ */ o(((e) => {
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
})), sO = (/* @__PURE__ */ o(((e, t) => {
	t.exports = oO();
})))(), cO = (e) => typeof e == "string" ? e : e ? e.displayName || e.name || "Component" : "", lO = null, uO = null, dO = (e) => {
	if (e === lO && Array.isArray(uO)) return uO;
	var t = [];
	return C.Children.forEach(e, (e) => {
		yn(e) || ((0, sO.isFragment)(e) ? t = t.concat(dO(e.props.children)) : t.push(e));
	}), uO = t, lO = e, t;
};
function fO(e, t) {
	var n = [], r = [];
	return r = Array.isArray(t) ? t.map((e) => cO(e)) : [cO(t)], dO(e).forEach((e) => {
		var t = rn(e, "type.displayName") || rn(e, "type.name");
		t && r.indexOf(t) !== -1 && n.push(e);
	}), n;
}
//#endregion
//#region node_modules/recharts/es6/util/ActiveShapeUtils.js
function pO(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function mO(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? pO(Object(n), !0).forEach(function(t) {
			hO(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : pO(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function hO(e, t, n) {
	return (t = gO(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function gO(e) {
	var t = _O(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function _O(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function vO(e, t) {
	return mO(mO({}, t), e);
}
function yO(e) {
	return /*#__PURE__*/ (0, C.isValidElement)(e) ? e.props : e;
}
function bO(e, t) {
	return /*#__PURE__*/ (0, C.cloneElement)(e, vO(yO(e), t));
}
function xO(e) {
	if ("index" in e) {
		var t = e.index;
		return typeof t == "number" || typeof t == "string" ? t : void 0;
	}
}
function SO(e) {
	return "isActive" in e && e.isActive === !0;
}
function CO(e) {
	var t = e.option, n = e.DefaultShape, r = e.shapeProps, i = e.activeClassName, a = i === void 0 ? "recharts-active-shape" : i, o = e.inActiveClassName, s = o === void 0 ? "recharts-shape" : o, c = xO(r), l = /*#__PURE__*/ (0, C.isValidElement)(t) ? bO(t, r) : t === n ? /*#__PURE__*/ C.createElement(n, r) : typeof t == "function" ? t(r, c) : typeof t == "object" ? /*#__PURE__*/ C.createElement(n, vO(t, r)) : /*#__PURE__*/ C.createElement(n, r);
	return SO(r) ? /*#__PURE__*/ C.createElement(Ze, { className: a }, l) : /*#__PURE__*/ C.createElement(Ze, { className: s }, l);
}
//#endregion
//#region node_modules/recharts/es6/context/tooltipContext.js
var wO = (e, t, n) => {
	var r = qr();
	return (i, a) => (o) => {
		e == null || e(i, a, o), r(BS({
			activeIndex: String(a),
			activeDataKey: t,
			activeCoordinate: i.tooltipPosition,
			activeGraphicalItemId: n
		}));
	};
}, TO = (e) => {
	var t = qr();
	return (n, r) => (i) => {
		e == null || e(n, r, i), t(VS());
	};
}, EO = (e, t, n) => {
	var r = qr();
	return (i, a) => (o) => {
		e == null || e(i, a, o), r(US({
			activeIndex: String(a),
			activeDataKey: t,
			activeCoordinate: i.tooltipPosition,
			activeGraphicalItemId: n
		}));
	};
};
//#endregion
//#region node_modules/recharts/es6/state/SetTooltipEntrySettings.js
function DO(e) {
	var t = e.tooltipEntrySettings, n = qr(), r = Dc(), i = (0, C.useRef)(null);
	return (0, C.useLayoutEffect)(() => {
		r || (i.current === null ? n(IS(t)) : i.current !== t && n(LS({
			prev: i.current,
			next: t
		})), i.current = t);
	}, [
		t,
		n,
		r
	]), (0, C.useLayoutEffect)(() => () => {
		i.current && (n(RS(i.current)), i.current = null);
	}, [n]), null;
}
//#endregion
//#region node_modules/recharts/es6/state/SetLegendPayload.js
function OO(e) {
	var t = e.legendPayload, n = qr(), r = Dc(), i = (0, C.useRef)(null);
	return (0, C.useLayoutEffect)(() => {
		r || (i.current === null ? n(xl(t)) : i.current !== t && n(Sl({
			prev: i.current,
			next: t
		})), i.current = t);
	}, [
		n,
		r,
		t
	]), (0, C.useLayoutEffect)(() => () => {
		i.current && (n(Cl(i.current)), i.current = null);
	}, [n]), null;
}
//#endregion
//#region node_modules/recharts/es6/animation/matchBy.js
function kO(e, t) {
	return PO(e) || NO(e, t) || jO(e, t) || AO();
}
function AO() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function jO(e, t) {
	if (e) {
		if (typeof e == "string") return MO(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? MO(e, t) : void 0;
	}
}
function MO(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function NO(e, t) {
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
function PO(e) {
	if (Array.isArray(e)) return e;
}
var FO = "index", IO = "append";
function LO(e, t) {
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
function RO(e, t) {
	var n = e.length / t.length;
	return LO(t.map((t, r) => e[Math.floor(r * n)]), t);
}
function zO(e, t) {
	return LO(t.map((t, n) => e[n]), t);
}
function BO(e, t) {
	for (var n = /* @__PURE__ */ new Map(), r = 0; r < e.length; r++) {
		var i = e[r];
		if (i != null) {
			var a = t(i, r);
			a != null && !n.has(a) && n.set(a, i);
		}
	}
	return n;
}
function VO(e, t, n) {
	var r = BO(e, n), i = /* @__PURE__ */ new Set(), a = t.map((e, t) => {
		var a = n(e, t);
		if (a != null) {
			var o = r.get(a);
			if (o !== void 0) return i.add(a), o;
		}
	}), o = [];
	for (var s of r) {
		var c = kO(s, 2), l = c[0], u = c[1];
		i.has(l) || o.push(u);
	}
	return LO(a, t, o);
}
function HO(e, t, n) {
	return t == null ? null : e == null ? t.map((e) => ({
		status: "added",
		next: e
	})) : n === "index" ? RO(e, t) : n === "append" ? zO(e, t) : VO(e, t, n);
}
//#endregion
//#region node_modules/recharts/es6/animation/useAnimationStartSnapshot.js
function UO(e, t) {
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
function WO(e, t) {
	return YO(e) || JO(e, t) || KO(e, t) || GO();
}
function GO() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function KO(e, t) {
	if (e) {
		if (typeof e == "string") return qO(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? qO(e, t) : void 0;
	}
}
function qO(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function JO(e, t) {
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
function YO(e) {
	if (Array.isArray(e)) return e;
}
function XO(e, t) {
	var n = WO((0, C.useState)(!1), 2), r = n[0], i = n[1];
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
function ZO(e) {
	var t, n = e.animationInput, r = e.animationIdPrefix, i = e.items, a = e.previousItemsRef, o = e.isAnimationActive, s = e.animationBegin, c = e.animationDuration, l = e.animationEasing, u = e.onAnimationStart, d = e.onAnimationEnd, f = e.animationInterpolateFn, p = e.animationMatchBy, m = e.shouldUpdatePreviousRef, h = e.children, g = e.layout, _ = Vd(n, r), v = UO(_, a), y = (t = v.startValue) == null ? null : t, b = HO(y, i, p == null ? FO : p);
	return /*#__PURE__*/ C.createElement(Bd, {
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
var QO;
function $O(e, t) {
	return ik(e) || rk(e, t) || tk(e, t) || ek();
}
function ek() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function tk(e, t) {
	if (e) {
		if (typeof e == "string") return nk(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? nk(e, t) : void 0;
	}
}
function nk(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function rk(e, t) {
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
function ik(e) {
	if (Array.isArray(e)) return e;
}
var ak = (QO = C.useId) == null ? () => $O(C.useState(() => mn("uid-")), 1)[0] : QO;
//#endregion
//#region node_modules/recharts/es6/util/useUniqueId.js
function ok(e, t) {
	var n = ak();
	return t || (e ? `${e}-${n}` : n);
}
//#endregion
//#region node_modules/recharts/es6/context/RegisterGraphicalItemId.js
var sk = /*#__PURE__*/ (0, C.createContext)(void 0), ck = (e) => {
	var t = e.id, n = e.type, r = e.children, i = ok(`recharts-${n}`, t);
	return /*#__PURE__*/ C.createElement(sk.Provider, { value: i }, r(i));
}, lk = Bo({
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
			prepare: To()
		},
		replaceCartesianGraphicalItem: {
			reducer(e, t) {
				var n = t.payload, r = n.prev, i = n.next, a = uo(e).cartesianItems.indexOf(H(r));
				a > -1 && (e.cartesianItems[a] = H(i));
			},
			prepare: To()
		},
		removeCartesianGraphicalItem: {
			reducer(e, t) {
				var n = uo(e).cartesianItems.indexOf(H(t.payload));
				n > -1 && e.cartesianItems.splice(n, 1);
			},
			prepare: To()
		},
		addPolarGraphicalItem: {
			reducer(e, t) {
				e.polarItems.push(H(t.payload));
			},
			prepare: To()
		},
		removePolarGraphicalItem: {
			reducer(e, t) {
				var n = uo(e).polarItems.indexOf(H(t.payload));
				n > -1 && e.polarItems.splice(n, 1);
			},
			prepare: To()
		},
		replacePolarGraphicalItem: {
			reducer(e, t) {
				var n = t.payload, r = n.prev, i = n.next, a = uo(e).polarItems.indexOf(H(r));
				a > -1 && (e.polarItems[a] = H(i));
			},
			prepare: To()
		}
	}
}), uk = lk.actions, dk = uk.addCartesianGraphicalItem, fk = uk.replaceCartesianGraphicalItem, pk = uk.removeCartesianGraphicalItem;
uk.addPolarGraphicalItem, uk.removePolarGraphicalItem, uk.replacePolarGraphicalItem;
var mk = lk.reducer, hk = /*#__PURE__*/ (0, C.memo)((e) => {
	var t = qr(), n = (0, C.useRef)(null);
	return (0, C.useLayoutEffect)(() => {
		n.current === null ? t(dk(e)) : n.current !== e && t(fk({
			prev: n.current,
			next: e
		})), n.current = e;
	}, [t, e]), (0, C.useLayoutEffect)(() => () => {
		n.current && (t(pk(n.current)), n.current = null);
	}, [t]), null;
});
//#endregion
//#region node_modules/recharts/es6/state/cartesianAxisSlice.js
function gk(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function _k(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? gk(Object(n), !0).forEach(function(t) {
			vk(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : gk(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function vk(e, t, n) {
	return (t = yk(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function yk(e) {
	var t = bk(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function bk(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var xk = Bo({
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
			prepare: To()
		},
		replaceXAxis: {
			reducer(e, t) {
				var n = t.payload, r = n.prev, i = n.next;
				e.xAxis[r.id] !== void 0 && (r.id !== i.id && delete e.xAxis[r.id], e.xAxis[i.id] = H(i));
			},
			prepare: To()
		},
		removeXAxis: {
			reducer(e, t) {
				delete e.xAxis[t.payload.id];
			},
			prepare: To()
		},
		addYAxis: {
			reducer(e, t) {
				e.yAxis[t.payload.id] = H(t.payload);
			},
			prepare: To()
		},
		replaceYAxis: {
			reducer(e, t) {
				var n = t.payload, r = n.prev, i = n.next;
				e.yAxis[r.id] !== void 0 && (r.id !== i.id && delete e.yAxis[r.id], e.yAxis[i.id] = H(i));
			},
			prepare: To()
		},
		removeYAxis: {
			reducer(e, t) {
				delete e.yAxis[t.payload.id];
			},
			prepare: To()
		},
		addZAxis: {
			reducer(e, t) {
				e.zAxis[t.payload.id] = H(t.payload);
			},
			prepare: To()
		},
		replaceZAxis: {
			reducer(e, t) {
				var n = t.payload, r = n.prev, i = n.next;
				e.zAxis[r.id] !== void 0 && (r.id !== i.id && delete e.zAxis[r.id], e.zAxis[i.id] = H(i));
			},
			prepare: To()
		},
		removeZAxis: {
			reducer(e, t) {
				delete e.zAxis[t.payload.id];
			},
			prepare: To()
		},
		updateYAxisWidth(e, t) {
			var n = t.payload, r = n.id, i = n.width, a = e.yAxis[r];
			if (a) {
				var o, s = a.widthHistory || [];
				if (s.length === 3 && s[0] === s[2] && i === s[1] && i !== a.width && Math.abs(i - ((o = s[0]) == null ? 0 : o)) <= 1) return;
				var c = [...s, i].slice(-3);
				e.yAxis[r] = _k(_k({}, a), {}, {
					width: i,
					widthHistory: c
				});
			}
		}
	}
}), Sk = xk.actions, Ck = Sk.addXAxis, wk = Sk.replaceXAxis, Tk = Sk.removeXAxis, Ek = Sk.addYAxis, Dk = Sk.replaceYAxis, Ok = Sk.removeYAxis;
Sk.addZAxis, Sk.replaceZAxis, Sk.removeZAxis;
var kk = Sk.updateYAxisWidth, Ak = xk.reducer, jk = z([
	z([Cc], (e) => ({
		top: e.top,
		bottom: e.bottom,
		left: e.left,
		right: e.right
	})),
	sc,
	cc
], (e, t, n) => {
	if (!(!e || t == null || n == null)) return {
		x: e.left,
		y: e.top,
		width: Math.max(0, t - e.left - e.right),
		height: Math.max(0, n - e.top - e.bottom)
	};
}), Mk = () => R(jk);
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineBarSizeList.js
function Nk(e, t) {
	return Rk(e) || Lk(e, t) || Fk(e, t) || Pk();
}
function Pk() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function Fk(e, t) {
	if (e) {
		if (typeof e == "string") return Ik(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? Ik(e, t) : void 0;
	}
}
function Ik(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function Lk(e, t) {
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
function Rk(e) {
	if (Array.isArray(e)) return e;
}
var zk = (e, t, n) => {
	var r = n == null ? e : n;
	if (!yn(r)) return hn(r, t, 0);
}, Bk = (e, t, n) => {
	var r = {}, i = e.filter(pm), a = e.filter((e) => e.stackId == null), o = i.reduce((e, t) => {
		var n = e[t.stackId];
		return n == null && (n = []), n.push(t), e[t.stackId] = n, e;
	}, r), s = Object.entries(o).map((e) => {
		var r, i = Nk(e, 2), a = i[0], o = i[1];
		return {
			stackId: a,
			dataKeys: o.map((e) => e.dataKey),
			barSize: zk(t, n, (r = o[0]) == null ? void 0 : r.barSize)
		};
	}), c = a.map((e) => ({
		stackId: void 0,
		dataKeys: [e.dataKey].filter((e) => e != null),
		barSize: zk(t, n, e.barSize)
	}));
	return [...s, ...c];
};
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineAllBarPositions.js
function Vk(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Hk(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Vk(Object(n), !0).forEach(function(t) {
			Uk(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Vk(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Uk(e, t, n) {
	return (t = Wk(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function Wk(e) {
	var t = Gk(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Gk(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function Kk(e, t, n, r, i) {
	var a, o = r.length;
	if (!(o < 1)) {
		var s = hn(e, n, 0, !0), c, l = [];
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
			var m = hn(t, n, 0, !0);
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
var qk = (e, t, n, r, i, a, o) => {
	var s = yn(o) ? t : o, c = Kk(n, r, i === a ? a : i, e, s);
	return i !== a && c != null && (c = c.map((e) => Hk(Hk({}, e), {}, { position: Hk(Hk({}, e.position), {}, { offset: e.position.offset - i / 2 }) }))), c;
}, Jk = (e, t) => {
	var n = dm(t);
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
}, Yk = (e, t) => {
	if (!(e == null || t == null)) {
		var n = e.find((e) => e.stackId === t.stackId && t.dataKey != null && e.dataKeys.includes(t.dataKey));
		if (n != null) return n.position;
	}
};
//#endregion
//#region node_modules/recharts/es6/zIndex/getZIndexFromUnknown.js
function Xk(e, t) {
	return e && typeof e == "object" && "zIndex" in e && typeof e.zIndex == "number" && U(e.zIndex) ? e.zIndex : t;
}
//#endregion
//#region node_modules/recharts/es6/context/chartDataContext.js
var Zk = (e) => {
	var t = e.chartData, n = qr(), r = Dc();
	return (0, C.useEffect)(() => r ? () => {} : (n(bT(t)), () => {
		n(bT(void 0));
	}), [
		t,
		n,
		r
	]), null;
}, Qk = {
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
}, $k = Bo({
	name: "brush",
	initialState: Qk,
	reducers: { setBrushSettings(e, t) {
		return t.payload == null ? Qk : t.payload;
	} }
});
$k.actions.setBrushSettings;
var eA = $k.reducer;
//#endregion
//#region node_modules/recharts/es6/util/CartesianUtils.js
function tA(e) {
	return (e % 180 + 180) % 180;
}
var nA = function(e) {
	var t = e.width, n = e.height, r = tA(arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : 0) * Math.PI / 180, i = Math.atan(n / t), a = r > i && r < Math.PI - i ? n / Math.sin(r) : t / Math.cos(r);
	return Math.abs(a);
}, rA = Bo({
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
			var n = uo(e).dots.findIndex((e) => e === t.payload);
			n !== -1 && e.dots.splice(n, 1);
		},
		addArea: (e, t) => {
			e.areas.push(t.payload);
		},
		removeArea: (e, t) => {
			var n = uo(e).areas.findIndex((e) => e === t.payload);
			n !== -1 && e.areas.splice(n, 1);
		},
		addLine: (e, t) => {
			e.lines.push(H(t.payload));
		},
		removeLine: (e, t) => {
			var n = uo(e).lines.findIndex((e) => e === t.payload);
			n !== -1 && e.lines.splice(n, 1);
		}
	}
}), iA = rA.actions;
iA.addDot, iA.removeDot, iA.addArea, iA.removeArea, iA.addLine, iA.removeLine;
var aA = rA.reducer;
//#endregion
//#region node_modules/recharts/es6/container/ClipPathProvider.js
function oA(e, t) {
	return dA(e) || uA(e, t) || cA(e, t) || sA();
}
function sA() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function cA(e, t) {
	if (e) {
		if (typeof e == "string") return lA(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? lA(e, t) : void 0;
	}
}
function lA(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function uA(e, t) {
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
function dA(e) {
	if (Array.isArray(e)) return e;
}
var fA = /*#__PURE__*/ (0, C.createContext)(void 0), pA = (e) => {
	var t = e.children, n = oA((0, C.useState)(`${mn("recharts")}-clip`), 1)[0], r = Mk();
	if (r == null) return null;
	var i = r.x, a = r.y, o = r.width, s = r.height;
	return /*#__PURE__*/ C.createElement(fA.Provider, { value: n }, /*#__PURE__*/ C.createElement("defs", null, /*#__PURE__*/ C.createElement("clipPath", { id: n }, /*#__PURE__*/ C.createElement("rect", {
		x: i,
		y: a,
		height: s,
		width: o
	}))), t);
};
//#endregion
//#region node_modules/recharts/es6/util/getEveryNth.js
function mA(e, t) {
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
function hA(e, t, n) {
	return nA({
		width: e.width + t.width,
		height: e.height + t.height
	}, n);
}
function gA(e, t, n) {
	var r = n === "width", i = e.x, a = e.y, o = e.width, s = e.height;
	return t === 1 ? {
		start: r ? i : a,
		end: r ? i + o : a + s
	} : {
		start: r ? i + o : a + s,
		end: r ? i : a
	};
}
function _A(e, t, n, r, i) {
	if (e * t < e * r || e * t > e * i) return !1;
	var a = n();
	return e * (t - e * a / 2 - r) >= 0 && e * (t + e * a / 2 - i) <= 0;
}
function vA(e, t) {
	return mA(e, t + 1);
}
//#endregion
//#region node_modules/recharts/es6/cartesian/getEquidistantTicks.js
function yA(e, t, n, r, i) {
	for (var a = (r || []).slice(), o = t.start, s = t.end, c = 0, l = 1, u = o, d = function() {
		var t = r == null ? void 0 : r[c];
		if (t === void 0) return { v: mA(r, l) };
		var a = c, d, f = () => (d === void 0 && (d = n(t, a)), d), p = t.coordinate, m = c === 0 || _A(e, p, f, u, s);
		m || (c = 0, u = o, l += 1), m && (u = p + e * (f() / 2 + i), c += l);
	}, f; l <= a.length;) if (f = d(), f) return f.v;
	return [];
}
function bA(e, t, n, r, i) {
	var a = (r || []).slice().length;
	if (a === 0) return [];
	for (var o = t.start, s = t.end, c = 1; c <= a; c++) {
		for (var l = (a - 1) % c, u = o, d = !0, f = function() {
			var t = r[m];
			if (t == null) return 0;
			var a = m, o, c = () => (o === void 0 && (o = n(t, a)), o), f = t.coordinate, p = m === l || _A(e, f, c, u, s);
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
function xA(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function SA(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? xA(Object(n), !0).forEach(function(t) {
			CA(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : xA(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function CA(e, t, n) {
	return (t = wA(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function wA(e) {
	var t = TA(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function TA(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function EA(e, t, n, r, i) {
	for (var a = (r || []).slice(), o = a.length, s = t.start, c = t.end, l = function(t) {
		var r = a[t];
		if (r == null) return 1;
		var l = r, u, d = () => (u === void 0 && (u = n(r, t)), u);
		if (t === o - 1) {
			var f = e * (l.coordinate + e * d() / 2 - c);
			a[t] = l = SA(SA({}, l), {}, { tickCoord: f > 0 ? l.coordinate - f * e : l.coordinate });
		} else a[t] = l = SA(SA({}, l), {}, { tickCoord: l.coordinate });
		l.tickCoord != null && _A(e, l.tickCoord, d, s, c) && (c = l.tickCoord - e * (d() / 2 + i), a[t] = SA(SA({}, l), {}, { isShow: !0 }));
	}, u = o - 1; u >= 0; u--) if (l(u)) continue;
	return a;
}
function DA(e, t, n, r, i, a) {
	var o = (r || []).slice(), s = o.length, c = t.start, l = t.end;
	if (a) {
		var u = r[s - 1];
		if (u != null) {
			var d = n(u, s - 1), f = e * (u.coordinate + e * d / 2 - l);
			o[s - 1] = u = SA(SA({}, u), {}, { tickCoord: f > 0 ? u.coordinate - f * e : u.coordinate }), u.tickCoord != null && _A(e, u.tickCoord, () => d, c, l) && (l = u.tickCoord - e * (d / 2 + i), o[s - 1] = SA(SA({}, u), {}, { isShow: !0 }));
		}
	}
	for (var p = a ? s - 1 : s, m = function(t) {
		var r = o[t];
		if (r == null) return 1;
		var a = r, s, u = () => (s === void 0 && (s = n(r, t)), s);
		if (t === 0) {
			var d = e * (a.coordinate - e * u() / 2 - c);
			o[t] = a = SA(SA({}, a), {}, { tickCoord: d < 0 ? a.coordinate - d * e : a.coordinate });
		} else o[t] = a = SA(SA({}, a), {}, { tickCoord: a.coordinate });
		a.tickCoord != null && _A(e, a.tickCoord, u, c, l) && (c = a.tickCoord + e * (u() / 2 + i), o[t] = SA(SA({}, a), {}, { isShow: !0 }));
	}, h = 0; h < p; h++) if (m(h)) continue;
	return o;
}
function OA(e, t, n) {
	var r = e.tick, i = e.ticks, a = e.viewBox, o = e.minTickGap, s = e.orientation, c = e.interval, l = e.tickFormatter, u = e.unit, d = e.angle;
	if (!i || !i.length || !r) return [];
	if (L(c) || fu.isSsr) {
		var f;
		return (f = vA(i, L(c) ? c : 0)) == null ? [] : f;
	}
	var p = [], m = s === "top" || s === "bottom" ? "width" : "height", h = u && m === "width" ? pE(u, {
		fontSize: t,
		letterSpacing: n
	}) : {
		width: 0,
		height: 0
	}, g = (e, r) => {
		var i = typeof l == "function" ? l(e.value, r) : e.value;
		return m === "width" ? hA(pE(i, {
			fontSize: t,
			letterSpacing: n
		}), h, d) : pE(i, {
			fontSize: t,
			letterSpacing: n
		})[m];
	}, _ = i[0], v = i[1], y = i.length >= 2 && _ != null && v != null ? ln(v.coordinate - _.coordinate) : 1, b = gA(a, y, m);
	return c === "equidistantPreserveStart" ? yA(y, b, g, i, o) : c === "equidistantPreserveEnd" ? bA(y, b, g, i, o) : (p = c === "preserveStart" || c === "preserveStartEnd" ? DA(y, b, g, i, o, c === "preserveStartEnd") : EA(y, b, g, i, o), p.filter((e) => e.isShow));
}
//#endregion
//#region node_modules/recharts/es6/util/YAxisUtils.js
var kA = (e) => {
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
}, AA = Bo({
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
}), jA = AA.actions, MA = jA.setRenderedTicks, NA = jA.removeRenderedTicks, PA = AA.reducer, FA = [
	"axisLine",
	"width",
	"height",
	"className",
	"hide",
	"ticks",
	"axisType",
	"axisId"
];
function IA(e, t) {
	return VA(e) || BA(e, t) || RA(e, t) || LA();
}
function LA() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function RA(e, t) {
	if (e) {
		if (typeof e == "string") return zA(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? zA(e, t) : void 0;
	}
}
function zA(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function BA(e, t) {
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
function VA(e) {
	if (Array.isArray(e)) return e;
}
function HA(e, t) {
	if (e == null) return {};
	var n, r, i = UA(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function UA(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function WA() {
	return WA = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, WA.apply(null, arguments);
}
function GA(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function KA(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? GA(Object(n), !0).forEach(function(t) {
			qA(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : GA(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function qA(e, t, n) {
	return (t = JA(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function JA(e) {
	var t = YA(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function YA(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var XA = {
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
	zIndex: Hp.axis
};
function ZA(e) {
	var t = e.x, n = e.y, r = e.width, i = e.height, a = e.orientation, o = e.mirror, s = e.axisLine, c = e.otherSvgProps;
	if (!s) return null;
	var l = KA(KA(KA({}, c), ze(s)), {}, { fill: "none" });
	if (a === "top" || a === "bottom") {
		var u = +(a === "top" && !o || a === "bottom" && o);
		l = KA(KA({}, l), {}, {
			x1: t,
			y1: n + u * i,
			x2: t + r,
			y2: n + u * i
		});
	} else {
		var d = +(a === "left" && !o || a === "right" && o);
		l = KA(KA({}, l), {}, {
			x1: t + d * r,
			y1: n,
			x2: t + d * r,
			y2: n + i
		});
	}
	return /*#__PURE__*/ C.createElement("line", WA({}, l, { className: Ne("recharts-cartesian-axis-line", rn(s, "className")) }));
}
function QA(e, t, n, r, i, a, o, s, c) {
	var l, u, d, f, p, m, h = s ? -1 : 1, g = e.tickSize || o, _ = L(e.tickCoord) ? e.tickCoord : e.coordinate;
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
function $A(e, t) {
	switch (e) {
		case "left": return t ? "start" : "end";
		case "right": return t ? "end" : "start";
		default: return "middle";
	}
}
function ej(e, t) {
	switch (e) {
		case "left":
		case "right": return "middle";
		case "top": return t ? "start" : "end";
		default: return t ? "end" : "start";
	}
}
function tj(e) {
	var t = e.option, n = e.tickProps, r = e.value, i, a = Ne(n.className, "recharts-cartesian-axis-tick-value");
	if (/*#__PURE__*/ C.isValidElement(t)) i = /*#__PURE__*/ C.cloneElement(t, KA(KA({}, n), {}, { className: a }));
	else if (typeof t == "function") i = t(KA(KA({}, n), {}, { className: a }));
	else {
		var o = "recharts-cartesian-axis-tick-value";
		typeof t != "boolean" && (o = Ne(o, aO(t))), i = /*#__PURE__*/ C.createElement(uD, WA({}, n, { className: o }), r);
	}
	return i;
}
function nj(e) {
	var t = e.ticks, n = e.axisType, r = e.axisId, i = qr();
	return (0, C.useEffect)(() => r == null || n == null ? Sn : (i(MA({
		ticks: t.map((e) => ({
			value: e.value,
			coordinate: e.coordinate,
			offset: e.offset,
			index: e.index
		})),
		axisId: r,
		axisType: n
	})), () => {
		i(NA({
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
var rj = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.ticks, r = n === void 0 ? [] : n, i = e.tick, a = e.tickLine, o = e.stroke, s = e.tickFormatter, c = e.unit, l = e.padding, u = e.tickTextProps, d = e.orientation, f = e.mirror, p = e.x, m = e.y, h = e.width, g = e.height, _ = e.tickSize, v = e.tickMargin, y = e.fontSize, b = e.letterSpacing, x = e.getTicksConfig, S = e.events, w = e.axisType, T = e.axisId, E = OA(KA(KA({}, x), {}, { ticks: r }), y, b), D = ze(x), O = Be(i), k = $E(D.textAnchor) ? D.textAnchor : $A(d, f), A = ej(d, f), j = {};
	typeof a == "object" && (j = a);
	var M = KA(KA({}, D), {}, { fill: "none" }, j), N = E.map((e) => KA({ entry: e }, QA(e, p, m, h, g, d, _, f, v))), P = N.map((e) => {
		var t = e.entry, n = e.line;
		return /*#__PURE__*/ C.createElement(Ze, {
			className: "recharts-cartesian-axis-tick",
			key: `tick-${t.value}-${t.coordinate}-${t.tickCoord}`
		}, a && /*#__PURE__*/ C.createElement("line", WA({}, M, n, { className: Ne("recharts-cartesian-axis-tick-line", rn(a, "className")) })));
	}), F = N.map((e, t) => {
		var n, r, a = e.entry, d = e.tick, f = KA(KA({}, KA(KA(KA(KA({ verticalAnchor: A }, D), {}, {
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
		return /*#__PURE__*/ C.createElement(Ze, WA({
			className: "recharts-cartesian-axis-tick-label",
			key: `tick-label-${a.value}-${a.coordinate}-${a.tickCoord}`
		}, En(S, a, t)), i && /*#__PURE__*/ C.createElement(tj, {
			option: i,
			tickProps: f,
			value: `${typeof s == "function" ? s(a.value, t) : a.value}${c || ""}`
		}));
	});
	return /*#__PURE__*/ C.createElement("g", { className: `recharts-cartesian-axis-ticks recharts-${w}-ticks` }, /*#__PURE__*/ C.createElement(nj, {
		ticks: E,
		axisId: T,
		axisType: w
	}), F.length > 0 && /*#__PURE__*/ C.createElement(Zw, { zIndex: Hp.label }, /*#__PURE__*/ C.createElement("g", {
		className: `recharts-cartesian-axis-tick-labels recharts-${w}-tick-labels`,
		ref: t
	}, F)), P.length > 0 && /*#__PURE__*/ C.createElement("g", { className: `recharts-cartesian-axis-tick-lines recharts-${w}-tick-lines` }, P));
}), ij = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.axisLine, r = e.width, i = e.height, a = e.className, o = e.hide, s = e.ticks, c = e.axisType, l = e.axisId, u = HA(e, FA), d = IA((0, C.useState)(""), 2), f = d[0], p = d[1], m = IA((0, C.useState)(""), 2), h = m[0], g = m[1], _ = (0, C.useRef)(null);
	(0, C.useImperativeHandle)(t, () => ({ getCalculatedWidth: () => {
		var t;
		return kA({
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
	return o || r != null && r <= 0 || i != null && i <= 0 ? null : /*#__PURE__*/ C.createElement(Zw, { zIndex: e.zIndex }, /*#__PURE__*/ C.createElement(Ze, { className: Ne("recharts-cartesian-axis", a) }, /*#__PURE__*/ C.createElement(ZA, {
		x: e.x,
		y: e.y,
		width: r,
		height: i,
		orientation: e.orientation,
		mirror: e.mirror,
		axisLine: n,
		otherSvgProps: ze(e)
	}), /*#__PURE__*/ C.createElement(rj, {
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
	}), /*#__PURE__*/ C.createElement(OD, {
		x: e.x,
		y: e.y,
		width: e.width,
		height: e.height,
		lowerWidth: e.width,
		upperWidth: e.width
	}, /*#__PURE__*/ C.createElement(HD, {
		label: e.label,
		labelRef: e.labelRef
	}), e.children)));
}), aj = /*#__PURE__*/ C.forwardRef((e, t) => {
	var n = Mn(e, XA);
	return /*#__PURE__*/ C.createElement(ij, WA({}, n, { ref: t }));
});
aj.displayName = "CartesianAxis";
//#endregion
//#region node_modules/recharts/es6/state/errorBarSlice.js
var oj = Bo({
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
}), sj = oj.actions;
sj.addErrorBar, sj.replaceErrorBar, sj.removeErrorBar;
var cj = oj.reducer, lj = ["children"];
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
var fj = /*#__PURE__*/ (0, C.createContext)({
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
function pj(e) {
	var t = e.children, n = uj(e, lj);
	return /*#__PURE__*/ C.createElement(fj.Provider, { value: n }, t);
}
//#endregion
//#region node_modules/recharts/es6/cartesian/GraphicalItemClipPath.js
function mj(e, t) {
	var n, r, i = R((t) => Cb(t, e)), a = R((e) => Eb(e, t)), o = (n = i == null ? void 0 : i.allowDataOverflow) == null ? xb.allowDataOverflow : n, s = (r = a == null ? void 0 : a.allowDataOverflow) == null ? wb.allowDataOverflow : r;
	return {
		needClip: o || s,
		needClipX: o,
		needClipY: s
	};
}
function hj(e) {
	var t = e.xAxisId, n = e.yAxisId, r = e.clipPathId, i = Mk(), a = mj(t, n), o = a.needClipX, s = a.needClipY, c = a.needClip, l = R((e) => Xx(e, t, !1)), u = R((e) => Zx(e, n, !1));
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
function gj(e, t) {
	var n, r;
	return (n = (r = e.graphicalItems.cartesianItems.find((e) => e.id === t)) == null ? void 0 : r.xAxisId) == null ? 0 : n;
}
function _j(e, t) {
	var n, r;
	return (n = (r = e.graphicalItems.cartesianItems.find((e) => e.id === t)) == null ? void 0 : r.yAxisId) == null ? 0 : n;
}
//#endregion
//#region node_modules/tiny-invariant/dist/esm/tiny-invariant.js
var vj = "Invariant failed";
function yj(e, t) {
	if (!e) throw Error(vj);
}
//#endregion
//#region node_modules/recharts/es6/util/BarUtils.js
var bj = ["option"];
function xj(e, t) {
	if (e == null) return {};
	var n, r, i = Sj(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function Sj(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var Cj = bf;
function wj(e) {
	var t = e.option, n = xj(e, bj);
	return /*#__PURE__*/ C.createElement(CO, {
		option: t,
		DefaultShape: Cj,
		shapeProps: n,
		activeClassName: "recharts-active-bar",
		inActiveClassName: "recharts-inactive-bar"
	});
}
var Tj = function(e) {
	var t = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : 0;
	return (n, r) => {
		if (L(e)) return e;
		var i = L(n) || yn(n);
		return i ? e(n, r) : (!i && yj(!1, `minPointSize callback function received a value with type of ${typeof n}. Currently only numbers or null/undefined are supported.`), t);
	};
}, Ej = (e, t, n) => n, Dj = z([Pb, (e, t) => t], (e, t) => e.filter((e) => e.type === "bar").find((e) => e.id === t)), Oj = z([Dj], (e) => e == null ? void 0 : e.maxBarSize), kj = (e, t, n, r) => r, Aj = z([
	K,
	Pb,
	gj,
	_j,
	Ej
], (e, t, n, r, i) => t.filter((t) => e === "horizontal" ? t.xAxisId === n : t.yAxisId === r).filter((e) => e.isPanorama === i).filter((e) => e.hide === !1).filter((e) => e.type === "bar")), jj = (e, t, n) => {
	var r = K(e), i = gj(e, t), a = _j(e, t);
	if (!(i == null || a == null)) return r === "horizontal" ? ox(e, "yAxis", a, n) : ox(e, "xAxis", i, n);
}, Mj = z([
	Aj,
	Fp,
	(e, t) => {
		var n = K(e), r = gj(e, t), i = _j(e, t);
		if (!(r == null || i == null)) return n === "horizontal" ? yS(e, "xAxis", r) : yS(e, "yAxis", i);
	}
], Bk), Nj = (e, t, n) => {
	var r, i, a = Dj(e, t);
	if (a == null) return 0;
	var o = gj(e, t), s = _j(e, t);
	if (o == null || s == null) return 0;
	var c = K(e), l = Mp(e), u = a.maxBarSize, d = yn(u) ? l : u, f, p;
	return c === "horizontal" ? (f = wS(e, "xAxis", o, n), p = CS(e, "xAxis", o, n)) : (f = wS(e, "yAxis", s, n), p = CS(e, "yAxis", s, n)), (r = (i = nc(f, p, !0)) == null ? d : i) == null ? 0 : r;
}, Pj = (e, t, n) => {
	var r = K(e), i = gj(e, t), a = _j(e, t);
	if (!(i == null || a == null)) {
		var o, s;
		return r === "horizontal" ? (o = wS(e, "xAxis", i, n), s = CS(e, "xAxis", i, n)) : (o = wS(e, "yAxis", a, n), s = CS(e, "yAxis", a, n)), nc(o, s);
	}
}, Fj = z([
	Cc,
	Tc,
	(e, t, n) => {
		var r = gj(e, t);
		if (r != null) return wS(e, "xAxis", r, n);
	},
	(e, t, n) => {
		var r = _j(e, t);
		if (r != null) return wS(e, "yAxis", r, n);
	},
	(e, t, n) => {
		var r = gj(e, t);
		if (r != null) return CS(e, "xAxis", r, n);
	},
	(e, t, n) => {
		var r = _j(e, t);
		if (r != null) return CS(e, "yAxis", r, n);
	},
	z([z([
		Mj,
		Mp,
		Np,
		Pp,
		Nj,
		Pj,
		Oj
	], qk), Dj], Yk),
	K,
	ip,
	Pj,
	z([jj, Dj], Jk),
	Dj,
	kj
], (e, t, n, r, i, a, o, s, c, l, u, d, f) => {
	var p = c.chartData, m = c.dataStartIndex, h = c.dataEndIndex;
	if (!(d == null || o == null || t == null || s !== "horizontal" && s !== "vertical" || n == null || r == null || i == null || a == null || l == null)) {
		var g = d.data, _ = g != null && g.length > 0 ? g : p == null ? void 0 : p.slice(m, h + 1);
		if (_ != null) return wM({
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
}), Ij = ["index"];
function Lj() {
	return Lj = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, Lj.apply(null, arguments);
}
function Rj(e, t) {
	if (e == null) return {};
	var n, r, i = zj(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function zj(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var Bj = /*#__PURE__*/ (0, C.createContext)(void 0), Vj = (e) => {
	var t = (0, C.useContext)(Bj);
	if (t != null) return t.stackId;
	if (e != null) return Js(e);
}, Hj = (e, t) => `recharts-bar-stack-clip-path-${e}-${t}`, Uj = (e) => {
	var t = (0, C.useContext)(Bj);
	if (t != null) {
		var n = t.stackId;
		return `url(#${Hj(n, e)})`;
	}
}, Wj = (e) => {
	var t = e.index, n = Rj(e, Ij), r = Uj(t);
	return /*#__PURE__*/ C.createElement(Ze, Lj({
		className: "recharts-bar-stack-layer",
		clipPath: r
	}, n));
}, Gj = [
	"onMouseEnter",
	"onMouseLeave",
	"onClick"
], Kj = [
	"value",
	"background",
	"tooltipPosition"
], qj = ["id"], Jj = [
	"onMouseEnter",
	"onClick",
	"onMouseLeave"
];
function Yj(e, t) {
	return eM(e) || $j(e, t) || Zj(e, t) || Xj();
}
function Xj() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function Zj(e, t) {
	if (e) {
		if (typeof e == "string") return Qj(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? Qj(e, t) : void 0;
	}
}
function Qj(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function $j(e, t) {
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
function eM(e) {
	if (Array.isArray(e)) return e;
}
function tM() {
	return tM = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, tM.apply(null, arguments);
}
function nM(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function rM(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? nM(Object(n), !0).forEach(function(t) {
			iM(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : nM(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function iM(e, t, n) {
	return (t = aM(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function aM(e) {
	var t = oM(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function oM(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function sM(e, t) {
	if (e == null) return {};
	var n, r, i = cM(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function cM(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var lM = (e) => {
	var t = e.dataKey, n = e.name, r = e.fill, i = e.legendType;
	return [{
		inactive: e.hide,
		dataKey: t,
		type: i,
		color: r,
		value: ic(n, t),
		payload: e
	}];
}, uM = /*#__PURE__*/ C.memo((e) => {
	var t = e.dataKey, n = e.stroke, r = e.strokeWidth, i = e.fill, a = e.name, o = e.hide, s = e.unit, c = e.formatter, l = e.tooltipType, u = e.id, d = {
		dataDefinedOnItem: void 0,
		getPosition: Sn,
		settings: {
			stroke: n,
			strokeWidth: r,
			fill: i,
			dataKey: t,
			nameKey: void 0,
			name: ic(a, t),
			hide: o,
			type: l,
			color: i,
			unit: s,
			formatter: c,
			graphicalItemId: u
		}
	};
	return /*#__PURE__*/ C.createElement(DO, { tooltipEntrySettings: d });
});
function dM(e) {
	var t = R(qC), n = e.data, r = e.dataKey, i = e.background, a = e.allOtherBarProps, o = a.onMouseEnter, s = a.onMouseLeave, c = a.onClick, l = sM(a, Gj), u = wO(o, r, a.id), d = TO(s), f = EO(c, r, a.id);
	if (!i || n == null) return null;
	var p = Be(i);
	return /*#__PURE__*/ C.createElement(Zw, { zIndex: Xk(i, Hp.barBackground) }, n.map((e, n) => {
		e.value;
		var a = e.background;
		e.tooltipPosition;
		var o = sM(e, Kj);
		if (!a) return null;
		var s = u(e, e.originalDataIndex), c = d(e, e.originalDataIndex), m = f(e, e.originalDataIndex), h = rM(rM(rM(rM(rM({
			option: i,
			isActive: String(e.originalDataIndex) === t
		}, o), {}, { fill: "#eee" }, a), p), En(l, e, n)), {}, {
			onMouseEnter: s,
			onMouseLeave: c,
			onClick: m,
			dataKey: r,
			index: n,
			className: "recharts-bar-background-rectangle"
		});
		return /*#__PURE__*/ C.createElement(wj, tM({ key: `background-bar-${n}` }, h));
	}));
}
function fM(e) {
	var t = e.showLabels, n = e.children, r = e.rects, i = r == null ? void 0 : r.map((e) => {
		var t = {
			x: e.x,
			y: e.y,
			width: e.width,
			lowerWidth: e.width,
			upperWidth: e.width,
			height: e.height
		};
		return rM(rM({}, t), {}, {
			value: e.value,
			payload: e.payload,
			parentViewBox: e.parentViewBox,
			viewBox: t,
			fill: e.fill
		});
	});
	return /*#__PURE__*/ C.createElement(XD, { value: t ? i : void 0 }, n);
}
function pM(e) {
	var t = e.shape, n = e.activeBar, r = e.baseProps, i = e.entry, a = e.index, o = e.dataKey, s = R(qC), c = R(YC), l = n && String(i.originalDataIndex) === s && (c == null || o === c), u = Yj((0, C.useState)(!1), 2), d = u[0], f = u[1], p = Yj((0, C.useState)(!1), 2), m = p[0], h = p[1];
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
	}, [l]), _ = l && m, v = l || d, y = l ? n === !0 ? t : n : t, b = /*#__PURE__*/ C.createElement(wj, tM({}, r, { name: String(r.name) }, i, {
		isActive: _,
		option: y,
		index: a,
		dataKey: o,
		animationElapsedTime: e.animationElapsedTime,
		isAnimating: e.isAnimating,
		isEntrance: e.isEntrance,
		onTransitionEnd: g
	}));
	return v ? /*#__PURE__*/ C.createElement(Zw, { zIndex: Hp.activeBar }, /*#__PURE__*/ C.createElement(Wj, { index: i.originalDataIndex }, b)) : b;
}
function mM(e) {
	var t = e.shape, n = e.baseProps, r = e.entry, i = e.index, a = e.dataKey;
	return /*#__PURE__*/ C.createElement(wj, tM({}, n, { name: String(n.name) }, r, {
		isActive: !1,
		option: t,
		index: i,
		dataKey: a,
		animationElapsedTime: e.animationElapsedTime,
		isAnimating: e.isAnimating,
		isEntrance: e.isEntrance
	}));
}
function hM(e) {
	var t, n = e.data, r = e.props, i = e.animationElapsedTime, a = e.isAnimating, o = e.isEntrance, s = (t = ze(r)) == null ? {} : t, c = s.id, l = sM(s, qj), u = r.shape, d = r.dataKey, f = r.activeBar, p = r.onMouseEnter, m = r.onClick, h = r.onMouseLeave, g = sM(r, Jj), _ = wO(p, d, c), v = TO(h), y = EO(m, d, c);
	return n ? /*#__PURE__*/ C.createElement(C.Fragment, null, n.map((e, t) => /*#__PURE__*/ C.createElement(Wj, tM({
		index: e.originalDataIndex,
		key: `rectangle-${e == null ? void 0 : e.x}-${e == null ? void 0 : e.y}-${e == null ? void 0 : e.value}-${t}`,
		className: "recharts-bar-rectangle"
	}, En(g, e, t), {
		onMouseEnter: _(e, e.originalDataIndex),
		onMouseLeave: v(e, e.originalDataIndex),
		onClick: y(e, e.originalDataIndex)
	}), f ? /*#__PURE__*/ C.createElement(pM, {
		shape: u,
		activeBar: f,
		baseProps: l,
		entry: e,
		index: t,
		dataKey: d,
		animationElapsedTime: i,
		isAnimating: a,
		isEntrance: o
	}) : /*#__PURE__*/ C.createElement(mM, {
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
var gM = (e, t, n) => e == null ? [] : t === 1 ? e.flatMap((e) => e.status === "removed" ? [] : [e.next]) : e.flatMap((e) => {
	if (e.status === "removed") return n === "horizontal" ? [rM(rM({}, e.prev), {}, {
		height: _n(e.prev.height, 0, t),
		y: _n(e.prev.y, e.prev.y + e.prev.height, t)
	})] : [rM(rM({}, e.prev), {}, { width: _n(e.prev.width, 0, t) })];
	if (e.status === "matched") return [rM(rM({}, e.next), {}, {
		x: _n(e.prev.x, e.next.x, t),
		y: _n(e.prev.y, e.next.y, t),
		width: _n(e.prev.width, e.next.width, t),
		height: _n(e.prev.height, e.next.height, t)
	})];
	var r = e.next;
	return n === "horizontal" ? [rM(rM({}, r), {}, {
		height: _n(0, r.height, t),
		y: _n(r.stackedBarStart, r.y, t)
	})] : [rM(rM({}, r), {}, {
		width: _n(0, r.width, t),
		x: _n(r.stackedBarStart, r.x, t)
	})];
});
function _M(e) {
	var t = e.props, n = e.previousRectanglesRef, r = t.data, i = t.isAnimationActive, a = t.animationBegin, o = t.animationDuration, s = t.animationEasing, c = t.animationInterpolateFn, l = t.layout, u = XO(t.onAnimationStart, t.onAnimationEnd), d = u.isAnimating, f = u.handleAnimationStart, p = u.handleAnimationEnd;
	return /*#__PURE__*/ C.createElement(fM, {
		showLabels: !d,
		rects: r
	}, /*#__PURE__*/ C.createElement(ZO, {
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
	}, (e, n, r) => /*#__PURE__*/ C.createElement(Ze, null, /*#__PURE__*/ C.createElement(hM, {
		props: t,
		data: e,
		animationElapsedTime: n,
		isAnimating: d || n < 1,
		isEntrance: r
	}))), /*#__PURE__*/ C.createElement(tO, { label: t.label }), t.children);
}
function vM(e) {
	var t = (0, C.useRef)(null);
	return /*#__PURE__*/ C.createElement(_M, {
		previousRectanglesRef: t,
		props: e
	});
}
var yM = 0, bM = (e, t) => {
	var n = Array.isArray(e.value) ? e.value[1] : e.value;
	return {
		x: e.x,
		y: e.y,
		value: n,
		errorVal: Hs(e, t)
	};
}, xM = class extends C.PureComponent {
	render() {
		var e = this.props, t = e.hide, n = e.data, r = e.dataKey, i = e.className, a = e.xAxisId, o = e.yAxisId, s = e.needClip, c = e.background, l = e.id;
		if (t || n == null) return null;
		var u = Ne("recharts-bar", i), d = l;
		return /*#__PURE__*/ C.createElement(Ze, {
			className: u,
			id: l
		}, s && /*#__PURE__*/ C.createElement("defs", null, /*#__PURE__*/ C.createElement(hj, {
			clipPathId: d,
			xAxisId: a,
			yAxisId: o
		})), /*#__PURE__*/ C.createElement(Ze, {
			className: "recharts-bar-rectangles",
			clipPath: s ? `url(#clipPath-${d})` : void 0
		}, /*#__PURE__*/ C.createElement(dM, {
			data: n,
			dataKey: r,
			background: c,
			allOtherBarProps: this.props
		}), /*#__PURE__*/ C.createElement(vM, this.props)));
	}
}, SM = {
	activeBar: !1,
	animationBegin: 0,
	animationDuration: 400,
	animationEasing: "ease",
	animationInterpolateFn: gM,
	animationMatchBy: IO,
	background: !1,
	hide: !1,
	isAnimationActive: "auto",
	label: !1,
	legendType: "rect",
	minPointSize: yM,
	shape: Cj,
	xAxisId: 0,
	yAxisId: 0,
	zIndex: Hp.bar
};
function CM(e) {
	var t = e.xAxisId, n = e.yAxisId, r = e.hide, i = e.legendType, a = e.minPointSize, o = e.activeBar, s = e.animationBegin, c = e.animationDuration, l = e.animationEasing, u = e.isAnimationActive, d = mj(t, n).needClip, f = ml(), p = Dc(), m = fO(e.children, ZT), h = R((t) => Fj(t, e.id, p, m));
	if (f !== "vertical" && f !== "horizontal") return null;
	var g, _ = h == null ? void 0 : h[0];
	return g = _ == null || _.height == null || _.width == null ? 0 : f === "vertical" ? _.height / 2 : _.width / 2, /*#__PURE__*/ C.createElement(pj, {
		xAxisId: t,
		yAxisId: n,
		data: h,
		dataPointFormatter: bM,
		errorBarOffset: g
	}, /*#__PURE__*/ C.createElement(xM, tM({}, e, {
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
function wM(e) {
	var t = e.layout, n = e.barSettings, r = n.dataKey, i = n.minPointSize, a = n.hasCustomShape, o = e.pos, s = e.bandSize, c = e.xAxis, l = e.yAxis, u = e.xAxisTicks, d = e.yAxisTicks, f = e.stackedData, p = e.displayedData, m = e.offset, h = e.cells, g = e.parentViewBox, _ = e.dataStartIndex, v = t === "horizontal" ? l : c, y = f ? v.scale.domain() : null, b = Xs({ numericAxis: v }), x = v.scale.map(b);
	return p.map((e, n) => {
		var p, v, S, C, w, T;
		if (f) {
			var E = f[n + _];
			if (E == null) return null;
			p = Gs(E, y);
		} else p = Hs(e, r), Array.isArray(p) || (p = [b, p]);
		var D = Tj(i, yM)(p[1], n);
		if (t === "horizontal") {
			var O, k = l.scale.map(p[0]), A = l.scale.map(p[1]);
			if (k == null || A == null) return null;
			v = Ys({
				axis: c,
				ticks: u,
				bandSize: s,
				offset: o.offset,
				entry: e,
				index: n
			}), S = (O = A == null ? k : A) == null ? void 0 : O, C = o.size;
			var j = k - A;
			if (w = un(j) ? 0 : j, T = {
				x: v,
				y: m.top,
				width: C,
				height: m.height
			}, Math.abs(D) > 0 && Math.abs(w) < Math.abs(D)) {
				var M = ln(w || D) * (Math.abs(D) - Math.abs(w));
				S -= M, w += M;
			}
		} else {
			var N = c.scale.map(p[0]), P = c.scale.map(p[1]);
			if (N == null || P == null) return null;
			if (v = N, S = Ys({
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
				var F = ln(C || D) * (Math.abs(D) - Math.abs(C));
				C += F;
			}
		}
		return v == null || S == null || C == null || w == null || !a && (C === 0 || w === 0) ? null : rM(rM({}, e), {}, {
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
function TM(e) {
	var t = Mn(e, SM), n = Vj(t.stackId), r = Dc();
	return /*#__PURE__*/ C.createElement(ck, {
		id: t.id,
		type: "bar"
	}, (e) => /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(OO, { legendPayload: lM(t) }), /*#__PURE__*/ C.createElement(uM, {
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
	}), /*#__PURE__*/ C.createElement(hk, {
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
		hasCustomShape: t.shape != null && t.shape !== Cj
	}), /*#__PURE__*/ C.createElement(Zw, { zIndex: t.zIndex }, /*#__PURE__*/ C.createElement(CM, tM({}, t, { id: e })))));
}
var EM = /*#__PURE__*/ C.memo(TM, Ul);
EM.displayName = "Bar";
//#endregion
//#region node_modules/recharts/es6/util/axisPropsAreEqual.js
var DM = ["domain", "range"], OM = ["domain", "range"];
function kM(e, t) {
	if (e == null) return {};
	var n, r, i = AM(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function AM(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function jM(e, t) {
	return e === t ? !0 : Array.isArray(e) && e.length === 2 && Array.isArray(t) && t.length === 2 ? e[0] === t[0] && e[1] === t[1] : !1;
}
function MM(e, t) {
	if (e === t) return !0;
	var n = e.domain, r = e.range, i = kM(e, DM), a = t.domain, o = t.range, s = kM(t, OM);
	return !jM(n, a) || !jM(r, o) ? !1 : Ul(i, s);
}
//#endregion
//#region node_modules/recharts/es6/cartesian/XAxis.js
var NM = ["type"], PM = [
	"dangerouslySetInnerHTML",
	"ticks",
	"scale"
], FM = ["id", "scale"];
function IM() {
	return IM = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, IM.apply(null, arguments);
}
function LM(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function RM(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? LM(Object(n), !0).forEach(function(t) {
			zM(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : LM(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function zM(e, t, n) {
	return (t = BM(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function BM(e) {
	var t = VM(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function VM(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function HM(e, t) {
	if (e == null) return {};
	var n, r, i = UM(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function UM(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function WM(e) {
	var t = qr(), n = (0, C.useRef)(null), r = hl(), i = e.type, a = HM(e, NM), o = Kp(r, "xAxis", i), s = (0, C.useMemo)(() => {
		if (o != null) return RM(RM({}, a), {}, { type: o });
	}, [a, o]);
	return (0, C.useLayoutEffect)(() => {
		s != null && (n.current === null ? t(Ck(s)) : n.current !== s && t(wk({
			prev: n.current,
			next: s
		})), n.current = s);
	}, [s, t]), (0, C.useLayoutEffect)(() => () => {
		n.current && (t(Tk(n.current)), n.current = null);
	}, [t]), null;
}
var GM = (e) => {
	var t = e.xAxisId, n = e.className, r = R(Tc), i = Dc(), a = "xAxis", o = R((e) => SS(e, a, t, i)), s = R((e) => dS(e, t)), c = R((e) => gS(e, t)), l = R((e) => Sb(e, t));
	if (s == null || c == null || l == null) return null;
	e.dangerouslySetInnerHTML, e.ticks, e.scale;
	var u = HM(e, PM);
	l.id, l.scale;
	var d = HM(l, FM);
	return /*#__PURE__*/ C.createElement(aj, IM({}, u, d, {
		x: c.x,
		y: c.y,
		width: s.width,
		height: s.height,
		className: Ne(`recharts-${a} ${a}`, n),
		viewBox: r,
		ticks: o,
		axisType: a,
		axisId: t
	}));
}, KM = {
	allowDataOverflow: xb.allowDataOverflow,
	allowDecimals: xb.allowDecimals,
	allowDuplicatedCategory: xb.allowDuplicatedCategory,
	angle: xb.angle,
	axisLine: XA.axisLine,
	height: xb.height,
	hide: !1,
	includeHidden: xb.includeHidden,
	interval: xb.interval,
	label: !1,
	minTickGap: xb.minTickGap,
	mirror: xb.mirror,
	orientation: xb.orientation,
	padding: xb.padding,
	reversed: xb.reversed,
	scale: xb.scale,
	tick: xb.tick,
	tickCount: xb.tickCount,
	tickLine: XA.tickLine,
	tickSize: XA.tickSize,
	type: xb.type,
	niceTicks: xb.niceTicks,
	xAxisId: 0
}, qM = /*#__PURE__*/ C.memo((e) => {
	var t = Mn(e, KM);
	return /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(WM, {
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
	}), /*#__PURE__*/ C.createElement(GM, t));
}, MM);
qM.displayName = "XAxis";
//#endregion
//#region node_modules/recharts/es6/cartesian/YAxis.js
var JM = ["type"], YM = [
	"dangerouslySetInnerHTML",
	"ticks",
	"scale"
], XM = ["id", "scale"];
function ZM() {
	return ZM = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, ZM.apply(null, arguments);
}
function QM(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function $M(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? QM(Object(n), !0).forEach(function(t) {
			eN(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : QM(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function eN(e, t, n) {
	return (t = tN(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function tN(e) {
	var t = nN(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function nN(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function rN(e, t) {
	if (e == null) return {};
	var n, r, i = iN(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function iN(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function aN(e) {
	var t = qr(), n = (0, C.useRef)(null), r = hl(), i = e.type, a = rN(e, JM), o = Kp(r, "yAxis", i), s = (0, C.useMemo)(() => {
		if (o != null) return $M($M({}, a), {}, { type: o });
	}, [o, a]);
	return (0, C.useLayoutEffect)(() => {
		s != null && (n.current === null ? t(Ek(s)) : n.current !== s && t(Dk({
			prev: n.current,
			next: s
		})), n.current = s);
	}, [s, t]), (0, C.useLayoutEffect)(() => () => {
		n.current && (t(Ok(n.current)), n.current = null);
	}, [t]), null;
}
function oN(e) {
	var t = e.yAxisId, n = e.className, r = e.width, i = e.label, a = (0, C.useRef)(null), o = (0, C.useRef)(null), s = R(Tc), c = Dc(), l = qr(), u = "yAxis", d = R((e) => vS(e, t)), f = R((e) => _S(e, t)), p = R((e) => SS(e, u, t, c)), m = R((e) => Tb(e, t));
	if ((0, C.useLayoutEffect)(() => {
		if (!(r !== "auto" || !d || ND(i) || /*#__PURE__*/ (0, C.isValidElement)(i) || m == null)) {
			var e = a.current;
			if (e) {
				var n = e.getCalculatedWidth();
				Math.round(d.width) !== Math.round(n) && l(kk({
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
	var h = rN(e, YM);
	m.id, m.scale;
	var g = rN(m, XM);
	return /*#__PURE__*/ C.createElement(aj, ZM({}, h, g, {
		ref: a,
		labelRef: o,
		x: f.x,
		y: f.y,
		tickTextProps: r === "auto" ? { width: void 0 } : { width: r },
		width: d.width,
		height: d.height,
		className: Ne(`recharts-${u} ${u}`, n),
		viewBox: s,
		ticks: p,
		axisType: u,
		axisId: t
	}));
}
var sN = {
	allowDataOverflow: wb.allowDataOverflow,
	allowDecimals: wb.allowDecimals,
	allowDuplicatedCategory: wb.allowDuplicatedCategory,
	angle: wb.angle,
	axisLine: XA.axisLine,
	hide: !1,
	includeHidden: wb.includeHidden,
	interval: wb.interval,
	label: !1,
	minTickGap: wb.minTickGap,
	mirror: wb.mirror,
	orientation: wb.orientation,
	padding: wb.padding,
	reversed: wb.reversed,
	scale: wb.scale,
	tick: wb.tick,
	tickCount: wb.tickCount,
	tickLine: XA.tickLine,
	tickSize: XA.tickSize,
	type: wb.type,
	niceTicks: wb.niceTicks,
	width: wb.width,
	yAxisId: 0
}, cN = /*#__PURE__*/ C.memo((e) => {
	var t = Mn(e, sN);
	return /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(aN, {
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
	}), /*#__PURE__*/ C.createElement(oN, t));
}, MM);
cN.displayName = "YAxis";
var lN = z([
	(e, t) => t,
	K,
	cm,
	_m,
	BC,
	HC,
	bw,
	Cc
], Mw);
//#endregion
//#region node_modules/recharts/es6/util/getRelativeCoordinate.js
function uN(e) {
	return "getBBox" in e.currentTarget && typeof e.currentTarget.getBBox == "function";
}
function dN(e) {
	var t = e.currentTarget.getBoundingClientRect(), n, r;
	if (uN(e)) {
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
var fN = vo("mouseClick"), pN = Es();
pN.startListening({
	actionCreator: fN,
	effect: (e, t) => {
		var n = e.payload, r = lN(t.getState(), dN(n));
		(r == null ? void 0 : r.activeIndex) != null && t.dispatch(GS({
			activeIndex: r.activeIndex,
			activeDataKey: void 0,
			activeCoordinate: r.activeCoordinate
		}));
	}
});
var mN = vo("mouseMove"), hN = Es(), gN = null, _N = null, vN = null;
hN.startListening({
	actionCreator: mN,
	effect: (e, t) => {
		var n = e.payload, r = t.getState().eventSettings, i = r.throttleDelay, a = r.throttledEvents, o = a === "all" || (a == null ? void 0 : a.includes("mousemove"));
		gN !== null && (cancelAnimationFrame(gN), gN = null), _N !== null && (typeof i != "number" || !o) && (clearTimeout(_N), _N = null), vN = dN(n);
		var s = () => {
			var e = t.getState(), n = kS(e, e.tooltip.settings.shared);
			if (!vN) {
				gN = null, _N = null;
				return;
			}
			if (n === "axis") {
				var r = lN(e, vN);
				(r == null ? void 0 : r.activeIndex) == null ? t.dispatch(HS()) : t.dispatch(WS({
					activeIndex: r.activeIndex,
					activeDataKey: void 0,
					activeCoordinate: r.activeCoordinate
				}));
			}
			gN = null, _N = null;
		};
		if (!o) {
			s();
			return;
		}
		i === "raf" ? gN = requestAnimationFrame(s) : typeof i == "number" && _N === null && (_N = setTimeout(s, i));
	}
});
//#endregion
//#region node_modules/recharts/es6/state/reduxDevtoolsJsonStringifyReplacer.js
function yN(e, t) {
	return t instanceof HTMLElement ? `HTMLElement <${t.tagName} class="${t.className}">` : t === window ? "global.window" : e === "children" && typeof t == "object" && t ? "<<CHILDREN>>" : t;
}
//#endregion
//#region node_modules/recharts/es6/state/rootPropsSlice.js
var bN = {
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
}, xN = Bo({
	name: "rootProps",
	initialState: bN,
	reducers: { updateOptions: (e, t) => {
		var n;
		e.accessibilityLayer = t.payload.accessibilityLayer, e.barCategoryGap = t.payload.barCategoryGap, e.barGap = (n = t.payload.barGap) == null ? bN.barGap : n, e.barSize = t.payload.barSize, e.maxBarSize = t.payload.maxBarSize, e.stackOffset = t.payload.stackOffset, e.syncId = t.payload.syncId, e.syncMethod = t.payload.syncMethod, e.className = t.payload.className, e.baseValue = t.payload.baseValue, e.reverseStackOrder = t.payload.reverseStackOrder;
	} }
}), SN = xN.reducer, CN = xN.actions.updateOptions, wN = Bo({
	name: "polarOptions",
	initialState: null,
	reducers: { updatePolarOptions: (e, t) => e === null ? t.payload : (e.startAngle = t.payload.startAngle, e.endAngle = t.payload.endAngle, e.cx = t.payload.cx, e.cy = t.payload.cy, e.innerRadius = t.payload.innerRadius, e.outerRadius = t.payload.outerRadius, e) }
});
wN.actions.updatePolarOptions;
var TN = wN.reducer, EN = vo("keyDown"), DN = vo("focus"), ON = vo("blur"), kN = Es(), AN = null, jN = null, MN = null;
kN.startListening({
	actionCreator: EN,
	effect: (e, t) => {
		MN = e.payload, AN !== null && (cancelAnimationFrame(AN), AN = null);
		var n = t.getState().eventSettings, r = n.throttleDelay, i = n.throttledEvents, a = i === "all" || i.includes("keydown");
		jN !== null && (typeof r != "number" || !a) && (clearTimeout(jN), jN = null);
		var o = () => {
			try {
				var e = t.getState();
				if (e.rootProps.accessibilityLayer === !1) return;
				var n = e.tooltip.keyboardInteraction, r = MN;
				if (r !== "ArrowRight" && r !== "ArrowLeft" && r !== "Enter") return;
				var i = oC(n, OC(e), rx(e), LC(e)), a = i == null ? -1 : Number(i), o = !Number.isFinite(a) || a < 0, s = HC(e), c = OC(e), l = kS(e, e.tooltip.settings.shared);
				if (r === "Enter") {
					if (o) return;
					var u = Tw(e, l, "hover", String(n.index));
					t.dispatch(qS({
						active: !n.active,
						activeIndex: n.index,
						activeCoordinate: u
					}));
					return;
				}
				var d = TS(e) === "left-to-right" ? 1 : -1, f = r === "ArrowRight" ? 1 : -1, p;
				if (o) {
					var m = rx(e), h = LC(e), g = f * d, _ = (e) => ({
						active: !1,
						index: String(e),
						dataKey: void 0,
						graphicalItemId: void 0,
						coordinate: void 0
					});
					if (p = -1, g > 0) {
						for (var v = 0; v < c.length; v++) if (oC(_(v), c, m, h) != null) {
							p = v;
							break;
						}
					} else for (var y = c.length - 1; y >= 0; y--) if (oC(_(y), c, m, h) != null) {
						p = y;
						break;
					}
					if (p < 0) return;
				} else {
					p = a + f * d;
					var b = (s == null ? void 0 : s.length) || c.length;
					if (b === 0 || p >= b || p < 0) return;
				}
				var x = Tw(e, l, "hover", String(p));
				t.dispatch(qS({
					active: !0,
					activeIndex: p.toString(),
					activeCoordinate: x
				}));
			} finally {
				AN = null, jN = null;
			}
		};
		if (!a) {
			o();
			return;
		}
		r === "raf" ? AN = requestAnimationFrame(o) : typeof r == "number" && jN === null && (o(), MN = null, jN = setTimeout(() => {
			MN ? o() : (jN = null, AN = null);
		}, r));
	}
}), kN.startListening({
	actionCreator: DN,
	effect: (e, t) => {
		var n = t.getState();
		if (n.rootProps.accessibilityLayer !== !1) {
			var r = n.tooltip.keyboardInteraction;
			if (!r.active && r.index == null) {
				var i = "0", a = Tw(n, kS(n, n.tooltip.settings.shared), "hover", String(i));
				t.dispatch(qS({
					active: !0,
					activeIndex: i,
					activeCoordinate: a
				}));
			}
		}
	}
}), kN.startListening({
	actionCreator: ON,
	effect: (e, t) => {
		var n = t.getState();
		if (n.rootProps.accessibilityLayer !== !1) {
			var r = n.tooltip.keyboardInteraction;
			r.active && t.dispatch(qS({
				active: !1,
				activeIndex: r.index,
				activeCoordinate: r.coordinate
			}));
		}
	}
});
//#endregion
//#region node_modules/recharts/es6/util/createEventProxy.js
function NN(e) {
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
var PN = vo("externalEvent"), FN = Es(), IN = /* @__PURE__ */ new Map(), LN = /* @__PURE__ */ new Map(), RN = /* @__PURE__ */ new Map();
FN.startListening({
	actionCreator: PN,
	effect: (e, t) => {
		var n = e.payload, r = n.handler, i = n.reactEvent;
		if (r != null) {
			var a = i.type, o = NN(i);
			RN.set(a, {
				handler: r,
				reactEvent: o
			});
			var s = IN.get(a);
			s !== void 0 && (cancelAnimationFrame(s), IN.delete(a));
			var c = t.getState().eventSettings, l = c.throttleDelay, u = c.throttledEvents, d = u === "all" || (u == null ? void 0 : u.includes(a)), f = LN.get(a);
			f !== void 0 && (typeof l != "number" || !d) && (clearTimeout(f), LN.delete(a));
			var p = () => {
				var e = RN.get(a);
				try {
					if (!e) return;
					var n = e.handler, r = e.reactEvent, i = t.getState(), o = {
						activeCoordinate: QC(i),
						activeDataKey: YC(i),
						activeIndex: qC(i),
						activeLabel: JC(i),
						activeTooltipIndex: qC(i),
						isTooltipActive: $C(i)
					};
					n && n(o, r);
				} finally {
					IN.delete(a), LN.delete(a), RN.delete(a);
				}
			};
			if (!d) {
				p();
				return;
			}
			if (l === "raf") {
				var m = requestAnimationFrame(p);
				IN.set(a, m);
			} else if (typeof l == "number") {
				if (!LN.has(a)) {
					p();
					var h = setTimeout(p, l);
					LN.set(a, h);
				}
			} else p();
		}
	}
});
var zN = z([
	z([uC], (e) => e.tooltipItemPayloads),
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
}), BN = vo("touchMove"), VN = Es(), HN = null, UN = null, WN = null, GN = null;
VN.startListening({
	actionCreator: BN,
	effect: (e, t) => {
		var n = e.payload;
		if (!(n.touches == null || n.touches.length === 0)) {
			GN = NN(n);
			var r = t.getState().eventSettings, i = r.throttleDelay, a = r.throttledEvents, o = a === "all" || a.includes("touchmove");
			HN !== null && (cancelAnimationFrame(HN), HN = null), UN !== null && (typeof i != "number" || !o) && (clearTimeout(UN), UN = null), WN = Array.from(n.touches).map((e) => dN({
				clientX: e.clientX,
				clientY: e.clientY,
				currentTarget: n.currentTarget
			}));
			var s = () => {
				if (GN != null) {
					var e = t.getState(), n = kS(e, e.tooltip.settings.shared);
					if (n === "axis") {
						var r, i = (r = WN) == null ? void 0 : r[0];
						if (i == null) {
							HN = null, UN = null;
							return;
						}
						var a = lN(e, i);
						(a == null ? void 0 : a.activeIndex) != null && t.dispatch(WS({
							activeIndex: a.activeIndex,
							activeDataKey: void 0,
							activeCoordinate: a.activeCoordinate
						}));
					} else if (n === "item") {
						var o, s = GN.touches[0];
						if (document.elementFromPoint == null || s == null) return;
						var c = document.elementFromPoint(s.clientX, s.clientY);
						if (!c || !c.getAttribute) return;
						var l = c.getAttribute(pc), u = (o = c.getAttribute("data-recharts-item-id")) == null ? void 0 : o, d = wC(e).find((e) => e.id === u);
						if (l == null || d == null || u == null) return;
						var f = d.dataKey, p = zN(e, l, u);
						t.dispatch(BS({
							activeDataKey: f,
							activeIndex: l,
							activeCoordinate: p,
							activeGraphicalItemId: u
						}));
					}
					HN = null, UN = null;
				}
			};
			if (!o) {
				s();
				return;
			}
			i === "raf" ? HN = requestAnimationFrame(s) : typeof i == "number" && UN === null && (s(), GN = null, UN = setTimeout(() => {
				GN ? s() : (UN = null, HN = null);
			}, i));
		}
	}
});
//#endregion
//#region node_modules/recharts/es6/state/eventSettingsSlice.js
var KN = {
	throttleDelay: "raf",
	throttledEvents: [
		"mousemove",
		"touchmove",
		"pointermove",
		"scroll",
		"wheel"
	]
}, qN = Bo({
	name: "eventSettings",
	initialState: KN,
	reducers: { setEventSettings: (e, t) => {
		t.payload.throttleDelay != null && (e.throttleDelay = t.payload.throttleDelay), t.payload.throttledEvents != null && (e.throttledEvents = H(t.payload.throttledEvents));
	} }
}), JN = qN.actions.setEventSettings, YN = qN.reducer, XN = Ui({
	brush: eA,
	cartesianAxis: Ak,
	chartData: ST,
	errorBars: cj,
	eventSettings: YN,
	graphicalItems: mk,
	layout: Ps,
	legend: wl,
	options: hT,
	polarAxis: iO,
	polarOptions: TN,
	referenceElements: aA,
	renderedTicks: PA,
	rootProps: SN,
	tooltip: JS,
	zIndex: Yw
}), ZN = function(e) {
	var t = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : "Chart";
	return Ao({
		reducer: XN,
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
				pN.middleware,
				hN.middleware,
				kN.middleware,
				FN.middleware,
				VN.middleware
			]);
		},
		enhancers: (e) => {
			var t = e;
			return typeof e == "function" && (t = e()), t.concat(Oo({ type: "raf" }));
		},
		devTools: fu.devToolsEnabled && {
			serialize: { replacer: yN },
			name: `recharts-${t}`
		}
	});
};
//#endregion
//#region node_modules/recharts/es6/state/RechartsStoreProvider.js
function QN(e) {
	var t = e.preloadedState, n = e.children, r = e.reduxStoreName, i = Dc(), a = (0, C.useRef)(null);
	if (i) return n;
	a.current == null && (a.current = ZN(t, r));
	var o = Wr;
	return /*#__PURE__*/ C.createElement(Bl, {
		context: o,
		store: a.current
	}, n);
}
//#endregion
//#region node_modules/recharts/es6/state/ReportMainChartProps.js
function $N(e) {
	var t = e.layout, n = e.margin, r = qr(), i = Dc();
	return (0, C.useEffect)(() => {
		i || (r(js(t)), r(As(n)));
	}, [
		r,
		i,
		t,
		n
	]), null;
}
var eP = /*#__PURE__*/ (0, C.memo)($N, Ul);
//#endregion
//#region node_modules/recharts/es6/state/ReportChartProps.js
function tP(e) {
	var t = qr();
	return (0, C.useEffect)(() => {
		t(CN(e));
	}, [t, e]), null;
}
var nP = /*#__PURE__*/ (0, C.memo)((e) => {
	var t = qr();
	return (0, C.useEffect)(() => {
		t(JN(e));
	}, [t, e]), null;
}, Ul);
//#endregion
//#region node_modules/recharts/es6/zIndex/ZIndexPortal.js
function rP(e) {
	var t = e.zIndex, n = e.isPanorama, r = (0, C.useRef)(null), i = qr();
	return (0, C.useLayoutEffect)(() => (r.current && i(qw({
		zIndex: t,
		element: r.current,
		isPanorama: n
	})), () => {
		i(Jw({
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
function iP(e) {
	var t = e.children, n = e.isPanorama, r = R(Pw);
	if (!r || r.length === 0) return t;
	var i = r.filter((e) => e < 0), a = r.filter((e) => e > 0);
	return /*#__PURE__*/ C.createElement(C.Fragment, null, i.map((e) => /*#__PURE__*/ C.createElement(rP, {
		key: e,
		zIndex: e,
		isPanorama: n
	})), t, a.map((e) => /*#__PURE__*/ C.createElement(rP, {
		key: e,
		zIndex: e,
		isPanorama: n
	})));
}
//#endregion
//#region node_modules/recharts/es6/container/RootSurface.js
var aP = ["children"];
function oP(e, t) {
	if (e == null) return {};
	var n, r, i = sP(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function sP(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function cP() {
	return cP = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, cP.apply(null, arguments);
}
var lP = {
	width: "100%",
	height: "100%",
	display: "block"
}, uP = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = fl(), r = pl(), i = Pu();
	if (!Is(n) || !Is(r)) return null;
	var a = e.children, o = e.otherAttributes, s = e.title, c = e.desc, l, u;
	return o != null && (l = typeof o.tabIndex == "number" ? o.tabIndex : i ? 0 : void 0, u = typeof o.role == "string" ? o.role : i ? "application" : void 0), /*#__PURE__*/ C.createElement(Ke, cP({}, o, {
		title: s,
		desc: c,
		role: u,
		tabIndex: l,
		width: n,
		height: r,
		style: lP,
		ref: t
	}), a);
}), dP = (e) => {
	var t = e.children, n = R(kc);
	if (!n) return null;
	var r = n.width, i = n.height, a = n.y, o = n.x;
	return /*#__PURE__*/ C.createElement(Ke, {
		width: r,
		height: i,
		x: o,
		y: a
	}, t);
}, fP = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.children, r = oP(e, aP);
	return Dc() ? /*#__PURE__*/ C.createElement(dP, null, /*#__PURE__*/ C.createElement(iP, { isPanorama: !0 }, n)) : /*#__PURE__*/ C.createElement(uP, cP({ ref: t }, r), /*#__PURE__*/ C.createElement(iP, { isPanorama: !1 }, n));
});
//#endregion
//#region node_modules/recharts/es6/util/useReportScale.js
function pP(e, t) {
	return vP(e) || _P(e, t) || hP(e, t) || mP();
}
function mP() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function hP(e, t) {
	if (e) {
		if (typeof e == "string") return gP(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? gP(e, t) : void 0;
	}
}
function gP(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function _P(e, t) {
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
function vP(e) {
	if (Array.isArray(e)) return e;
}
function yP() {
	var e = qr(), t = pP((0, C.useState)(null), 2), n = t[0], r = t[1], i = R(lc);
	return (0, C.useEffect)(() => {
		if (n != null) {
			var t = n.getBoundingClientRect().width / n.offsetWidth;
			U(t) && t !== i && e(Ns(t));
		}
	}, [
		n,
		e,
		i
	]), r;
}
//#endregion
//#region node_modules/recharts/es6/chart/RechartsWrapper.js
function bP(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function xP(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? bP(Object(n), !0).forEach(function(t) {
			SP(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : bP(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function SP(e, t, n) {
	return (t = CP(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function CP(e) {
	var t = wP(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function wP(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function TP() {
	return TP = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, TP.apply(null, arguments);
}
function EP(e, t) {
	return jP(e) || AP(e, t) || OP(e, t) || DP();
}
function DP() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function OP(e, t) {
	if (e) {
		if (typeof e == "string") return kP(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? kP(e, t) : void 0;
	}
}
function kP(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function AP(e, t) {
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
function jP(e) {
	if (Array.isArray(e)) return e;
}
var MP = () => (NT(), null);
function NP(e) {
	if (typeof e == "number") return e;
	if (typeof e == "string") {
		var t = parseFloat(e);
		if (!Number.isNaN(t)) return t;
	}
	return 0;
}
var PP = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n, r, i = (0, C.useRef)(null), a = EP((0, C.useState)({
		containerWidth: NP((n = e.style) == null ? void 0 : n.width),
		containerHeight: NP((r = e.style) == null ? void 0 : r.height)
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
	}, [c]), /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(vl, {
		width: o.containerWidth,
		height: o.containerHeight
	}), /*#__PURE__*/ C.createElement("div", TP({ ref: l }, e)));
}), FP = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.width, r = e.height, i = EP((0, C.useState)({
		containerWidth: NP(n),
		containerHeight: NP(r)
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
	return /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(vl, {
		width: a.containerWidth,
		height: a.containerHeight
	}), /*#__PURE__*/ C.createElement("div", TP({ ref: c }, e)));
}), IP = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.width, r = e.height;
	return /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(vl, {
		width: n,
		height: r
	}), /*#__PURE__*/ C.createElement("div", TP({ ref: t }, e)));
}), LP = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.width, r = e.height;
	return typeof n == "string" || typeof r == "string" ? /*#__PURE__*/ C.createElement(FP, TP({}, e, { ref: t })) : typeof n == "number" && typeof r == "number" ? /*#__PURE__*/ C.createElement(IP, TP({}, e, {
		width: n,
		height: r,
		ref: t
	})) : /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(vl, {
		width: n,
		height: r
	}), /*#__PURE__*/ C.createElement("div", TP({ ref: t }, e)));
});
function RP(e) {
	return e ? PP : LP;
}
var zP = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.children, r = e.className, i = e.height, a = e.onClick, o = e.onContextMenu, s = e.onDoubleClick, c = e.onMouseDown, l = e.onMouseEnter, u = e.onMouseLeave, d = e.onMouseMove, f = e.onMouseUp, p = e.onTouchEnd, m = e.onTouchMove, h = e.onTouchStart, g = e.style, _ = e.width, v = e.responsive, y = e.dispatchTouchEvents, b = y === void 0 || y, x = (0, C.useRef)(null), S = qr(), w = EP((0, C.useState)(null), 2), T = w[0], E = w[1], D = EP((0, C.useState)(null), 2), O = D[0], k = D[1], A = yP(), j = al(), M = (j == null ? void 0 : j.width) > 0 ? j.width : _, N = (j == null ? void 0 : j.height) > 0 ? j.height : i, P = (0, C.useCallback)((e) => {
		A(e), typeof t == "function" && t(e), E(e), k(e), e != null && (x.current = e);
	}, [
		A,
		t,
		E,
		k
	]), F = (0, C.useCallback)((e) => {
		S(fN(e)), S(PN({
			handler: a,
			reactEvent: e
		}));
	}, [S, a]), ee = (0, C.useCallback)((e) => {
		S(mN(e)), S(PN({
			handler: l,
			reactEvent: e
		}));
	}, [S, l]), te = (0, C.useCallback)((e) => {
		S(HS()), S(PN({
			handler: u,
			reactEvent: e
		}));
	}, [S, u]), ne = (0, C.useCallback)((e) => {
		S(mN(e)), S(PN({
			handler: d,
			reactEvent: e
		}));
	}, [S, d]), re = (0, C.useCallback)(() => {
		S(DN());
	}, [S]), ie = (0, C.useCallback)(() => {
		S(ON());
	}, [S]), ae = (0, C.useCallback)((e) => {
		S(EN(e.key));
	}, [S]), oe = (0, C.useCallback)((e) => {
		S(PN({
			handler: o,
			reactEvent: e
		}));
	}, [S, o]), se = (0, C.useCallback)((e) => {
		S(PN({
			handler: s,
			reactEvent: e
		}));
	}, [S, s]), ce = (0, C.useCallback)((e) => {
		S(PN({
			handler: c,
			reactEvent: e
		}));
	}, [S, c]), le = (0, C.useCallback)((e) => {
		S(PN({
			handler: f,
			reactEvent: e
		}));
	}, [S, f]), ue = (0, C.useCallback)((e) => {
		S(PN({
			handler: h,
			reactEvent: e
		}));
	}, [S, h]), de = (0, C.useCallback)((e) => {
		b && S(BN(e)), S(PN({
			handler: m,
			reactEvent: e
		}));
	}, [
		S,
		b,
		m
	]), fe = (0, C.useCallback)((e) => {
		S(PN({
			handler: p,
			reactEvent: e
		}));
	}, [S, p]), pe = RP(v);
	return /*#__PURE__*/ C.createElement(sT.Provider, { value: T }, /*#__PURE__*/ C.createElement(Qe.Provider, { value: O }, /*#__PURE__*/ C.createElement(pe, {
		width: M == null ? g == null ? void 0 : g.width : M,
		height: N == null ? g == null ? void 0 : g.height : N,
		className: Ne("recharts-wrapper", r),
		style: xP({
			position: "relative",
			cursor: "default",
			width: M,
			height: N
		}, g),
		onClick: F,
		onContextMenu: oe,
		onDoubleClick: se,
		onFocus: re,
		onBlur: ie,
		onKeyDown: ae,
		onMouseDown: ce,
		onMouseEnter: ee,
		onMouseLeave: te,
		onMouseMove: ne,
		onMouseUp: le,
		onTouchEnd: fe,
		onTouchMove: de,
		onTouchStart: ue,
		ref: P
	}, /*#__PURE__*/ C.createElement(MP, null), n)));
}), BP = [
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
function VP(e, t) {
	if (e == null) return {};
	var n, r, i = HP(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function HP(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var UP = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.width, r = e.height, i = e.responsive, a = e.children, o = e.className, s = e.style, c = e.compact, l = e.title, u = e.desc, d = ze(VP(e, BP));
	return c ? /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(vl, {
		width: n,
		height: r
	}), /*#__PURE__*/ C.createElement(fP, {
		otherAttributes: d,
		title: l,
		desc: u
	}, a)) : /*#__PURE__*/ C.createElement(zP, {
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
	}, /*#__PURE__*/ C.createElement(fP, {
		otherAttributes: d,
		title: l,
		desc: u,
		ref: t
	}, /*#__PURE__*/ C.createElement(pA, null, a)));
});
//#endregion
//#region node_modules/recharts/es6/chart/CartesianChart.js
function WP() {
	return WP = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, WP.apply(null, arguments);
}
function GP(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function KP(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? GP(Object(n), !0).forEach(function(t) {
			qP(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : GP(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function qP(e, t, n) {
	return (t = JP(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function JP(e) {
	var t = YP(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function YP(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var XP = KP({
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
}, KN), ZP = /*#__PURE__*/ (0, C.forwardRef)(function(e, t) {
	var n, r = Mn(e.categoricalChartProps, XP), i = e.chartName, a = e.defaultTooltipEventType, o = e.validateTooltipEventTypes, s = e.tooltipPayloadSearcher, c = e.categoricalChartProps, l = {
		chartName: i,
		defaultTooltipEventType: a,
		validateTooltipEventTypes: o,
		tooltipPayloadSearcher: s,
		eventEmitter: void 0
	};
	return /*#__PURE__*/ C.createElement(QN, {
		preloadedState: { options: l },
		reduxStoreName: (n = c.id) == null ? i : n
	}, /*#__PURE__*/ C.createElement(Zk, { chartData: c.data }), /*#__PURE__*/ C.createElement(eP, {
		layout: r.layout,
		margin: r.margin
	}), /*#__PURE__*/ C.createElement(nP, {
		throttleDelay: r.throttleDelay,
		throttledEvents: r.throttledEvents
	}), /*#__PURE__*/ C.createElement(tP, {
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
	}), /*#__PURE__*/ C.createElement(UP, WP({}, r, { ref: t })));
}), QP = ["axis", "item"], $P = /*#__PURE__*/ (0, C.forwardRef)((e, t) => /*#__PURE__*/ C.createElement(ZP, {
	chartName: "BarChart",
	defaultTooltipEventType: "axis",
	validateTooltipEventTypes: QP,
	tooltipPayloadSearcher: pT,
	categoricalChartProps: e,
	ref: t
})), eF = /* @__PURE__ */ o(((e) => {
	var t = d(), n = Symbol.for("react.element"), r = Symbol.for("react.fragment"), i = Object.prototype.hasOwnProperty, a = t.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED.ReactCurrentOwner, o = {
		key: !0,
		ref: !0,
		__self: !0,
		__source: !0
	};
	function s(e, t, r) {
		var s, c = {}, l = null, u = null;
		for (s in r !== void 0 && (l = "" + r), t.key !== void 0 && (l = "" + t.key), t.ref !== void 0 && (u = t.ref), t) i.call(t, s) && !o.hasOwnProperty(s) && (c[s] = t[s]);
		if (e && e.defaultProps) for (s in t = e.defaultProps, t) c[s] === void 0 && (c[s] = t[s]);
		return {
			$$typeof: n,
			type: e,
			key: l,
			ref: u,
			props: c,
			_owner: a.current
		};
	}
	e.Fragment = r, e.jsx = s, e.jsxs = s;
})), tF = /* @__PURE__ */ o(((e, t) => {
	t.exports = eF();
})), nF = g(), Y = tF(), rF = [
	{
		key: "queueRows",
		label: "Queue Rows",
		icon: Se,
		tone: "blue"
	},
	{
		key: "nextSteps",
		label: "Next Steps",
		icon: he,
		tone: "green"
	},
	{
		key: "undecidedJobReviews",
		label: "Undecided Job Reviews",
		icon: ge,
		tone: "violet"
	},
	{
		key: "undecidedMaybeTailor",
		label: "Undecided Maybe Tailor",
		icon: ke,
		tone: "cyan"
	}
], iF = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
function aF(e) {
	return Number.isFinite(e) ? Math.max(0, Number(e)) : 0;
}
function oF(e) {
	return Number.isFinite(e) ? iF.format(Number(e)) : "—";
}
function sF({ active: e, payload: t }) {
	var n;
	if (!e || !(t != null && t.length)) return null;
	let r = (n = t[0]) == null ? void 0 : n.payload;
	return r ? /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "executive-kpi-tooltip",
		children: [
			/* @__PURE__ */ (0, Y.jsx)("span", { children: "Current" }),
			/* @__PURE__ */ (0, Y.jsx)("strong", { children: oF(r.current) }),
			Number(r.baseline) > 0 ? /* @__PURE__ */ (0, Y.jsxs)("small", { children: ["Queue baseline: ", oF(r.baseline)] }) : null
		]
	}) : null;
}
function cF({ value: e, queueRows: t, label: n }) {
	let r = Math.max(t, e, 1), i = [{
		name: "Current snapshot",
		current: e,
		remaining: Math.max(0, r - e),
		baseline: t
	}];
	return /* @__PURE__ */ (0, Y.jsx)("div", {
		className: "executive-kpi-chart",
		role: "img",
		"aria-label": t > 0 ? `${n}: ${oF(e)} against a current queue baseline of ${oF(t)}` : `${n}: ${oF(e)} in the current snapshot`,
		children: /* @__PURE__ */ (0, Y.jsx)(sl, {
			width: "100%",
			height: "100%",
			children: /* @__PURE__ */ (0, Y.jsxs)($P, {
				data: i,
				layout: "vertical",
				margin: {
					top: 6,
					right: 0,
					bottom: 6,
					left: 0
				},
				children: [
					/* @__PURE__ */ (0, Y.jsx)(qM, {
						type: "number",
						domain: [0, r],
						hide: !0
					}),
					/* @__PURE__ */ (0, Y.jsx)(cN, {
						type: "category",
						dataKey: "name",
						hide: !0
					}),
					/* @__PURE__ */ (0, Y.jsx)(XT, {
						allowEscapeViewBox: {
							x: !1,
							y: !0
						},
						content: /* @__PURE__ */ (0, Y.jsx)(sF, {}),
						cursor: !1,
						wrapperStyle: {
							zIndex: 30,
							pointerEvents: "none"
						}
					}),
					/* @__PURE__ */ (0, Y.jsx)(EM, {
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
					/* @__PURE__ */ (0, Y.jsx)(EM, {
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
function lF({ metric: e }) {
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
function uF({ state: e }) {
	if (e.status === "loading") return /* @__PURE__ */ (0, Y.jsx)("div", {
		className: "executive-kpi-dashboard kpi-grid kpi-grid-cols-1 sm:kpi-grid-cols-2 xl:kpi-grid-cols-4 kpi-gap-3",
		"aria-label": "Loading executive queue metrics",
		children: rF.map((e) => /* @__PURE__ */ (0, Y.jsx)(lF, { metric: e }, e.key))
	});
	let t = e.status === "error", n = t ? {
		queueRows: null,
		nextSteps: null,
		undecidedJobReviews: null,
		undecidedMaybeTailor: null
	} : e.metrics, r = aF(n.queueRows);
	return /* @__PURE__ */ (0, Y.jsx)("div", {
		className: "executive-kpi-dashboard kpi-grid kpi-grid-cols-1 sm:kpi-grid-cols-2 xl:kpi-grid-cols-4 kpi-gap-3",
		"aria-label": "Executive queue metrics",
		children: rF.map((e) => {
			let i = e.icon, a = n[e.key], o = aF(a);
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
						children: t ? "Unavailable" : oF(a)
					}),
					/* @__PURE__ */ (0, Y.jsx)("span", {
						className: "executive-kpi-caption",
						children: t ? "Status data could not be loaded" : "Current snapshot"
					}),
					t ? /* @__PURE__ */ (0, Y.jsx)("div", {
						className: "executive-kpi-error",
						role: "status",
						children: "Refresh Status to try again."
					}) : /* @__PURE__ */ (0, Y.jsx)(cF, {
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
//#region src/SourceYield.tsx
var dF = "applylens:source-yield-state", fF = { status: "loading" }, pF = new Intl.NumberFormat("en-US"), mF = (e) => pF.format(Number.isFinite(e) && e || 0);
function hF(e) {
	return e.split(/[\s_-]+/).filter(Boolean).map((e) => e.charAt(0).toUpperCase() + e.slice(1)).join(" ") || "Unknown source";
}
var gF = "Company boards, ATS tenants, global feeds, or configured query profiles contacted during this run.";
function _F(e) {
	let t = e.acquisition_status_counts;
	return t.SUCCESS > 0 ? t.FAILED > 0 || t.PARTIAL > 0 ? {
		label: "Degraded",
		tone: "degraded"
	} : {
		label: "Healthy",
		tone: "healthy"
	} : t.FAILED > 0 ? {
		label: "Failed",
		tone: "failed"
	} : t.PARTIAL > 0 ? {
		label: "Partial",
		tone: "partial"
	} : t.EMPTY > 0 ? {
		label: "Empty",
		tone: "empty"
	} : {
		label: "Unavailable",
		tone: "unavailable"
	};
}
function vF(e) {
	return `Successful targets: ${mF(e.SUCCESS)}; partial targets: ${mF(e.PARTIAL)}; empty targets: ${mF(e.EMPTY)}; failed targets: ${mF(e.FAILED)}.`;
}
function yF({ row: e }) {
	let t = e.scraped_jobs || e.raw_job_count, n = [
		["Acquired", t],
		["Title", e.title_pass_jobs],
		["U.S.", e.location_pass_jobs],
		["Fresh", e.freshness_pass_jobs],
		["Final", e.final_display_jobs]
	];
	return /* @__PURE__ */ (0, Y.jsx)("div", {
		className: "source-yield-funnel",
		"aria-label": n.map(([e, t]) => `${e} ${mF(t)}`).join(", "),
		children: n.map(([e, n]) => /* @__PURE__ */ (0, Y.jsx)("span", {
			className: "source-yield-funnel__step",
			title: `${e}: ${mF(n)}`,
			children: /* @__PURE__ */ (0, Y.jsx)("span", { style: { width: `${t ? Math.max(8, n / t * 100) : 0}%` } })
		}, e))
	});
}
function bF({ label: e, value: t }) {
	return /* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: e }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: mF(t) })] });
}
function xF({ row: e }) {
	let [t, n] = (0, C.useState)(!1), r = `source-yield-detail-${e.source.replace(/[^a-z0-9_-]/gi, "-")}`, i = _F(e), a = vF(e.acquisition_status_counts), o = e.scraped_jobs || e.raw_job_count;
	return /* @__PURE__ */ (0, Y.jsxs)(Y.Fragment, { children: [/* @__PURE__ */ (0, Y.jsxs)("tr", { children: [
		/* @__PURE__ */ (0, Y.jsx)("th", {
			scope: "row",
			children: /* @__PURE__ */ (0, Y.jsxs)("button", {
				type: "button",
				className: "source-yield-source-button",
				"aria-expanded": t,
				"aria-controls": r,
				onClick: () => n((e) => !e),
				children: [/* @__PURE__ */ (0, Y.jsx)(N, {
					"aria-hidden": "true",
					className: t ? "is-expanded" : "",
					size: 16
				}), /* @__PURE__ */ (0, Y.jsx)("span", { children: hF(e.source) })]
			})
		}),
		/* @__PURE__ */ (0, Y.jsx)("td", { children: mF(e.accounts_queried) }),
		/* @__PURE__ */ (0, Y.jsx)("td", { children: /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "source-yield-acquired",
			children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: mF(o) }), /* @__PURE__ */ (0, Y.jsx)(yF, { row: e })]
		}) }),
		/* @__PURE__ */ (0, Y.jsx)("td", { children: mF(e.title_pass_jobs) }),
		/* @__PURE__ */ (0, Y.jsx)("td", { children: mF(e.location_pass_jobs) }),
		/* @__PURE__ */ (0, Y.jsx)("td", { children: mF(e.freshness_pass_jobs) }),
		/* @__PURE__ */ (0, Y.jsx)("td", { children: /* @__PURE__ */ (0, Y.jsx)("strong", { children: mF(e.final_display_jobs) }) }),
		/* @__PURE__ */ (0, Y.jsx)("td", { children: /* @__PURE__ */ (0, Y.jsxs)("span", {
			className: "source-yield-percent",
			children: [e.yield_percent.toFixed(1), "%"]
		}) }),
		/* @__PURE__ */ (0, Y.jsx)("td", { children: /* @__PURE__ */ (0, Y.jsx)("span", {
			className: `source-yield-health source-yield-health--${i.tone}`,
			title: a,
			children: i.label
		}) })
	] }), t && /* @__PURE__ */ (0, Y.jsx)("tr", {
		className: "source-yield-detail-row",
		children: /* @__PURE__ */ (0, Y.jsx)("td", {
			colSpan: 9,
			id: r,
			children: /* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "source-yield-detail",
				children: [
					/* @__PURE__ */ (0, Y.jsxs)("div", {
						className: "source-yield-detail__funnel",
						children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Conversion funnel" }), /* @__PURE__ */ (0, Y.jsx)(yF, { row: e })]
					}),
					/* @__PURE__ */ (0, Y.jsxs)("div", {
						className: "source-yield-detail__metrics",
						children: [
							/* @__PURE__ */ (0, Y.jsx)(bF, {
								label: "Raw provider jobs",
								value: e.raw_job_count
							}),
							/* @__PURE__ */ (0, Y.jsx)(bF, {
								label: "Normalized jobs",
								value: e.normalized_job_count
							}),
							/* @__PURE__ */ (0, Y.jsx)(bF, {
								label: "Final corpus jobs",
								value: e.final_corpus_jobs
							}),
							/* @__PURE__ */ (0, Y.jsx)(bF, {
								label: "Final displayed jobs",
								value: e.final_display_jobs
							}),
							/* @__PURE__ */ (0, Y.jsx)(bF, {
								label: "Title rejects",
								value: e.title_reject_jobs
							}),
							/* @__PURE__ */ (0, Y.jsx)(bF, {
								label: "Location rejects",
								value: e.location_reject_jobs
							}),
							/* @__PURE__ */ (0, Y.jsx)(bF, {
								label: "Not recent",
								value: e.not_recent_jobs
							}),
							/* @__PURE__ */ (0, Y.jsx)(bF, {
								label: "Missing timestamps",
								value: e.missing_timestamp_jobs
							}),
							/* @__PURE__ */ (0, Y.jsx)(bF, {
								label: "Pages",
								value: e.page_count
							}),
							/* @__PURE__ */ (0, Y.jsx)(bF, {
								label: "Requests",
								value: e.request_count
							}),
							/* @__PURE__ */ (0, Y.jsx)(bF, {
								label: "Retries",
								value: e.retry_count
							}),
							/* @__PURE__ */ (0, Y.jsx)(bF, {
								label: "Partial results",
								value: e.partial_result_count
							})
						]
					}),
					/* @__PURE__ */ (0, Y.jsxs)("p", {
						className: "source-yield-detail__evidence",
						children: [
							"Targets · ",
							mF(e.acquisition_status_counts.SUCCESS),
							" successful / ",
							mF(e.acquisition_status_counts.PARTIAL),
							" partial / ",
							mF(e.acquisition_status_counts.EMPTY),
							" empty / ",
							mF(e.acquisition_status_counts.FAILED),
							" failed · Completeness · timestamp ",
							mF(e.timestamp_present_count),
							" present / ",
							mF(e.timestamp_missing_count),
							" missing · description ",
							mF(e.description_present_count),
							" present / ",
							mF(e.description_missing_count),
							" missing · canonical URL ",
							mF(e.canonical_url_present_count),
							" present / ",
							mF(e.canonical_url_missing_count),
							" missing"
						]
					})
				]
			})
		})
	})] });
}
function SF({ icon: e, title: t, body: n }) {
	return /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "source-yield-state",
		children: [/* @__PURE__ */ (0, Y.jsx)(e === "activity" ? O : se, {
			"aria-hidden": "true",
			size: 22
		}), /* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: t }), /* @__PURE__ */ (0, Y.jsx)("span", { children: n })] })]
	});
}
function CF({ state: e }) {
	if (e.status === "loading") return /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "source-yield-card",
		"aria-label": "Loading source yield",
		children: [/* @__PURE__ */ (0, Y.jsx)("div", { className: "source-yield-skeleton source-yield-skeleton--heading" }), /* @__PURE__ */ (0, Y.jsx)("div", { className: "source-yield-skeleton source-yield-skeleton--table" })]
	});
	if (e.status === "error") return /* @__PURE__ */ (0, Y.jsx)("div", {
		className: "source-yield-card",
		children: /* @__PURE__ */ (0, Y.jsx)(SF, {
			icon: "activity",
			title: "Source yield unavailable",
			body: e.message || "Status could not be loaded."
		})
	});
	let t = e.data;
	return t != null && t.available ? t.sources.length ? /* @__PURE__ */ (0, Y.jsxs)("section", {
		className: "source-yield-card",
		"aria-labelledby": "sourceYieldHeading",
		children: [/* @__PURE__ */ (0, Y.jsxs)("header", {
			className: "source-yield-header",
			children: [/* @__PURE__ */ (0, Y.jsxs)("div", { children: [
				/* @__PURE__ */ (0, Y.jsx)("span", {
					className: "source-yield-eyebrow",
					children: "Acquisition intelligence"
				}),
				/* @__PURE__ */ (0, Y.jsx)("h2", {
					id: "sourceYieldHeading",
					children: "Source Yield"
				}),
				/* @__PURE__ */ (0, Y.jsxs)("p", { children: ["Latest completed pipeline run", t.run_id ? ` · ${t.run_id}` : ""] }),
				/* @__PURE__ */ (0, Y.jsx)("p", {
					className: "source-yield-coverage-note",
					children: "Sources shown reflect the latest completed pipeline run."
				}),
				/* @__PURE__ */ (0, Y.jsx)("span", {
					className: "sr-only",
					id: "sourceYieldTargetsHelp",
					children: gF
				})
			] }), /* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "source-yield-chips",
				"aria-label": "Source yield summary",
				children: [
					/* @__PURE__ */ (0, Y.jsxs)("span", { children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: mF(t.totals.source_count) }), " sources contributing"] }),
					/* @__PURE__ */ (0, Y.jsxs)("span", {
						title: gF,
						"aria-describedby": "sourceYieldTargetsHelp",
						children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: mF(t.totals.accounts_queried) }), " targets queried"]
					}),
					/* @__PURE__ */ (0, Y.jsxs)("span", { children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: mF(t.totals.scraped_jobs) }), " acquired"] }),
					/* @__PURE__ */ (0, Y.jsxs)("span", {
						className: "is-accent",
						children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: mF(t.totals.final_display_jobs) }), " final jobs"]
					})
				]
			})]
		}), /* @__PURE__ */ (0, Y.jsx)("div", {
			className: "source-yield-table-wrap",
			children: /* @__PURE__ */ (0, Y.jsxs)("table", {
				className: "source-yield-table",
				children: [
					/* @__PURE__ */ (0, Y.jsx)("caption", {
						className: "sr-only",
						children: "Source yield funnel metrics for the latest successful pipeline run"
					}),
					/* @__PURE__ */ (0, Y.jsx)("thead", { children: /* @__PURE__ */ (0, Y.jsxs)("tr", { children: [
						/* @__PURE__ */ (0, Y.jsx)("th", {
							scope: "col",
							children: "Source"
						}),
						/* @__PURE__ */ (0, Y.jsx)("th", {
							scope: "col",
							children: /* @__PURE__ */ (0, Y.jsx)("span", {
								className: "source-yield-target-label",
								title: gF,
								"aria-describedby": "sourceYieldTargetsHelp",
								children: "Targets queried"
							})
						}),
						/* @__PURE__ */ (0, Y.jsx)("th", {
							scope: "col",
							children: "Acquired"
						}),
						/* @__PURE__ */ (0, Y.jsx)("th", {
							scope: "col",
							children: "Title pass"
						}),
						/* @__PURE__ */ (0, Y.jsx)("th", {
							scope: "col",
							children: "U.S. pass"
						}),
						/* @__PURE__ */ (0, Y.jsx)("th", {
							scope: "col",
							children: "Fresh 24h"
						}),
						/* @__PURE__ */ (0, Y.jsx)("th", {
							scope: "col",
							children: "Final jobs"
						}),
						/* @__PURE__ */ (0, Y.jsx)("th", {
							scope: "col",
							children: "Yield"
						}),
						/* @__PURE__ */ (0, Y.jsx)("th", {
							scope: "col",
							children: "Health"
						})
					] }) }),
					/* @__PURE__ */ (0, Y.jsx)("tbody", { children: t.sources.map((e) => /* @__PURE__ */ (0, Y.jsx)(xF, { row: e }, e.source)) })
				]
			})
		})]
	}) : /* @__PURE__ */ (0, Y.jsx)("div", {
		className: "source-yield-card",
		children: /* @__PURE__ */ (0, Y.jsx)(SF, {
			icon: "database",
			title: "No source activity",
			body: "The latest completed run produced no source-yield rows."
		})
	}) : /* @__PURE__ */ (0, Y.jsx)("div", {
		className: "source-yield-card",
		children: /* @__PURE__ */ (0, Y.jsx)(SF, {
			icon: "database",
			title: "Source evidence unavailable",
			body: "Source yield data is unavailable for this run."
		})
	});
}
//#endregion
//#region node_modules/@tanstack/table-core/build/lib/index.mjs
function wF(e, t) {
	return typeof e == "function" ? e(t) : e;
}
function TF(e, t) {
	return (n) => {
		t.setState((t) => ({
			...t,
			[e]: wF(n, t[e])
		}));
	};
}
function EF(e) {
	return e instanceof Function;
}
function DF(e) {
	return Array.isArray(e) && e.every((e) => typeof e == "number");
}
function OF(e, t) {
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
function kF(e, t, n, r) {
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
function AF(e, t, n, r) {
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
var jF = "debugHeaders";
function MF(e, t, n) {
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
var NF = { createTable: (e) => {
	e.getHeaderGroups = X(() => [
		e.getAllColumns(),
		e.getVisibleLeafColumns(),
		e.getState().columnPinning.left,
		e.getState().columnPinning.right
	], (t, n, r, i) => {
		var a, o;
		let s = (a = r == null ? void 0 : r.map((e) => n.find((t) => t.id === e)).filter(Boolean)) == null ? [] : a, c = (o = i == null ? void 0 : i.map((e) => n.find((t) => t.id === e)).filter(Boolean)) == null ? [] : o, l = n.filter((e) => !(r != null && r.includes(e.id)) && !(i != null && i.includes(e.id)));
		return PF(t, [
			...s,
			...l,
			...c
		], e);
	}, Z(e.options, jF, "getHeaderGroups")), e.getCenterHeaderGroups = X(() => [
		e.getAllColumns(),
		e.getVisibleLeafColumns(),
		e.getState().columnPinning.left,
		e.getState().columnPinning.right
	], (t, n, r, i) => (n = n.filter((e) => !(r != null && r.includes(e.id)) && !(i != null && i.includes(e.id))), PF(t, n, e, "center")), Z(e.options, jF, "getCenterHeaderGroups")), e.getLeftHeaderGroups = X(() => [
		e.getAllColumns(),
		e.getVisibleLeafColumns(),
		e.getState().columnPinning.left
	], (t, n, r) => {
		var i;
		return PF(t, (i = r == null ? void 0 : r.map((e) => n.find((t) => t.id === e)).filter(Boolean)) == null ? [] : i, e, "left");
	}, Z(e.options, jF, "getLeftHeaderGroups")), e.getRightHeaderGroups = X(() => [
		e.getAllColumns(),
		e.getVisibleLeafColumns(),
		e.getState().columnPinning.right
	], (t, n, r) => {
		var i;
		return PF(t, (i = r == null ? void 0 : r.map((e) => n.find((t) => t.id === e)).filter(Boolean)) == null ? [] : i, e, "right");
	}, Z(e.options, jF, "getRightHeaderGroups")), e.getFooterGroups = X(() => [e.getHeaderGroups()], (e) => [...e].reverse(), Z(e.options, jF, "getFooterGroups")), e.getLeftFooterGroups = X(() => [e.getLeftHeaderGroups()], (e) => [...e].reverse(), Z(e.options, jF, "getLeftFooterGroups")), e.getCenterFooterGroups = X(() => [e.getCenterHeaderGroups()], (e) => [...e].reverse(), Z(e.options, jF, "getCenterFooterGroups")), e.getRightFooterGroups = X(() => [e.getRightHeaderGroups()], (e) => [...e].reverse(), Z(e.options, jF, "getRightFooterGroups")), e.getFlatHeaders = X(() => [e.getHeaderGroups()], (e) => e.map((e) => e.headers).flat(), Z(e.options, jF, "getFlatHeaders")), e.getLeftFlatHeaders = X(() => [e.getLeftHeaderGroups()], (e) => e.map((e) => e.headers).flat(), Z(e.options, jF, "getLeftFlatHeaders")), e.getCenterFlatHeaders = X(() => [e.getCenterHeaderGroups()], (e) => e.map((e) => e.headers).flat(), Z(e.options, jF, "getCenterFlatHeaders")), e.getRightFlatHeaders = X(() => [e.getRightHeaderGroups()], (e) => e.map((e) => e.headers).flat(), Z(e.options, jF, "getRightFlatHeaders")), e.getCenterLeafHeaders = X(() => [e.getCenterFlatHeaders()], (e) => e.filter((e) => {
		var t;
		return !((t = e.subHeaders) != null && t.length);
	}), Z(e.options, jF, "getCenterLeafHeaders")), e.getLeftLeafHeaders = X(() => [e.getLeftFlatHeaders()], (e) => e.filter((e) => {
		var t;
		return !((t = e.subHeaders) != null && t.length);
	}), Z(e.options, jF, "getLeftLeafHeaders")), e.getRightLeafHeaders = X(() => [e.getRightFlatHeaders()], (e) => e.filter((e) => {
		var t;
		return !((t = e.subHeaders) != null && t.length);
	}), Z(e.options, jF, "getRightLeafHeaders")), e.getLeafHeaders = X(() => [
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
	}, Z(e.options, jF, "getLeafHeaders"));
} };
function PF(e, t, n, r) {
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
				let i = MF(n, c, {
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
	l(t.map((e, t) => MF(n, e, {
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
var FF = (e, t, n, r, i, a, o) => {
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
		getLeafRows: () => OF(s.subRows, (e) => e.subRows),
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
		getAllCells: X(() => [e.getAllLeafColumns()], (t) => t.map((t) => kF(e, s, t, t.id)), Z(e.options, "debugRows", "getAllCells")),
		_getAllCellsByColumnId: X(() => [s.getAllCells()], (e) => e.reduce((e, t) => (e[t.column.id] = t, e), {}), Z(e.options, "debugRows", "getAllCellsByColumnId"))
	};
	for (let t = 0; t < e._features.length; t++) {
		let n = e._features[t];
		n == null || n.createRow == null || n.createRow(s, e);
	}
	return s;
}, IF = { createColumn: (e, t) => {
	e._getFacetedRowModel = t.options.getFacetedRowModel && t.options.getFacetedRowModel(t, e.id), e.getFacetedRowModel = () => e._getFacetedRowModel ? e._getFacetedRowModel() : t.getPreFilteredRowModel(), e._getFacetedUniqueValues = t.options.getFacetedUniqueValues && t.options.getFacetedUniqueValues(t, e.id), e.getFacetedUniqueValues = () => e._getFacetedUniqueValues ? e._getFacetedUniqueValues() : /* @__PURE__ */ new Map(), e._getFacetedMinMaxValues = t.options.getFacetedMinMaxValues && t.options.getFacetedMinMaxValues(t, e.id), e.getFacetedMinMaxValues = () => {
		if (e._getFacetedMinMaxValues) return e._getFacetedMinMaxValues();
	};
} }, LF = (e, t, n) => {
	var r, i;
	let a = n == null || (r = n.toString()) == null ? void 0 : r.toLowerCase();
	return !!(!((i = e.getValue(t)) == null || (i = i.toString()) == null || (i = i.toLowerCase()) == null) && i.includes(a));
};
LF.autoRemove = (e) => qF(e);
var RF = (e, t, n) => {
	var r;
	return !!(!((r = e.getValue(t)) == null || (r = r.toString()) == null) && r.includes(n));
};
RF.autoRemove = (e) => qF(e);
var zF = (e, t, n) => {
	var r;
	return ((r = e.getValue(t)) == null || (r = r.toString()) == null ? void 0 : r.toLowerCase()) === (n == null ? void 0 : n.toLowerCase());
};
zF.autoRemove = (e) => qF(e);
var BF = (e, t, n) => {
	var r;
	return (r = e.getValue(t)) == null ? void 0 : r.includes(n);
};
BF.autoRemove = (e) => qF(e);
var VF = (e, t, n) => !n.some((n) => {
	var r;
	return !((r = e.getValue(t)) != null && r.includes(n));
});
VF.autoRemove = (e) => qF(e) || !(e != null && e.length);
var HF = (e, t, n) => n.some((n) => {
	var r;
	return (r = e.getValue(t)) == null ? void 0 : r.includes(n);
});
HF.autoRemove = (e) => qF(e) || !(e != null && e.length);
var UF = (e, t, n) => e.getValue(t) === n;
UF.autoRemove = (e) => qF(e);
var WF = (e, t, n) => e.getValue(t) == n;
WF.autoRemove = (e) => qF(e);
var GF = (e, t, n) => {
	let [r, i] = n, a = e.getValue(t);
	return a >= r && a <= i;
};
GF.resolveFilterValue = (e) => {
	let [t, n] = e, r = typeof t == "number" ? t : parseFloat(t), i = typeof n == "number" ? n : parseFloat(n), a = t === null || Number.isNaN(r) ? -Infinity : r, o = n === null || Number.isNaN(i) ? Infinity : i;
	if (a > o) {
		let e = a;
		a = o, o = e;
	}
	return [a, o];
}, GF.autoRemove = (e) => qF(e) || qF(e[0]) && qF(e[1]);
var KF = {
	includesString: LF,
	includesStringSensitive: RF,
	equalsString: zF,
	arrIncludes: BF,
	arrIncludesAll: VF,
	arrIncludesSome: HF,
	equals: UF,
	weakEquals: WF,
	inNumberRange: GF
};
function qF(e) {
	return e == null || e === "";
}
var JF = {
	getDefaultColumnDef: () => ({ filterFn: "auto" }),
	getInitialState: (e) => ({
		columnFilters: [],
		...e
	}),
	getDefaultOptions: (e) => ({
		onColumnFiltersChange: TF("columnFilters", e),
		filterFromLeafRows: !1,
		maxLeafRowFilterDepth: 100
	}),
	createColumn: (e, t) => {
		e.getAutoFilterFn = () => {
			let n = t.getCoreRowModel().flatRows[0], r = n == null ? void 0 : n.getValue(e.id);
			return typeof r == "string" ? KF.includesString : typeof r == "number" ? KF.inNumberRange : typeof r == "boolean" || typeof r == "object" && r ? KF.equals : Array.isArray(r) ? KF.arrIncludes : KF.weakEquals;
		}, e.getFilterFn = () => {
			var n, r;
			return EF(e.columnDef.filterFn) ? e.columnDef.filterFn : e.columnDef.filterFn === "auto" ? e.getAutoFilterFn() : (n = (r = t.options.filterFns) == null ? void 0 : r[e.columnDef.filterFn]) == null ? KF[e.columnDef.filterFn] : n;
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
				let r = e.getFilterFn(), i = t == null ? void 0 : t.find((t) => t.id === e.id), a = wF(n, i ? i.value : void 0);
				if (YF(r, a, e)) {
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
				return (r = wF(t, e)) == null ? void 0 : r.filter((e) => {
					let t = n.find((t) => t.id === e.id);
					return !(t && YF(t.getFilterFn(), e.value, t));
				});
			});
		}, e.resetColumnFilters = (t) => {
			var n, r;
			e.setColumnFilters(t || (n = (r = e.initialState) == null ? void 0 : r.columnFilters) == null ? [] : n);
		}, e.getPreFilteredRowModel = () => e.getCoreRowModel(), e.getFilteredRowModel = () => (!e._getFilteredRowModel && e.options.getFilteredRowModel && (e._getFilteredRowModel = e.options.getFilteredRowModel(e)), e.options.manualFiltering || !e._getFilteredRowModel ? e.getPreFilteredRowModel() : e._getFilteredRowModel());
	}
};
function YF(e, t, n) {
	return (e && e.autoRemove ? e.autoRemove(t, n) : !1) || t === void 0 || typeof t == "string" && !t;
}
var XF = {
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
		if (!DF(n)) return;
		if (n.length === 1) return n[0];
		let r = Math.floor(n.length / 2), i = n.sort((e, t) => e - t);
		return n.length % 2 == 0 ? (i[r - 1] + i[r]) / 2 : i[r];
	},
	unique: (e, t) => Array.from(new Set(t.map((t) => t.getValue(e))).values()),
	uniqueCount: (e, t) => new Set(t.map((t) => t.getValue(e))).size,
	count: (e, t) => t.length
}, ZF = {
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
		onGroupingChange: TF("grouping", e),
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
			if (typeof r == "number") return XF.sum;
			if (Object.prototype.toString.call(r) === "[object Date]") return XF.extent;
		}, e.getAggregationFn = () => {
			var n, r;
			if (!e) throw Error();
			return EF(e.columnDef.aggregationFn) ? e.columnDef.aggregationFn : e.columnDef.aggregationFn === "auto" ? e.getAutoAggregationFn() : (n = (r = t.options.aggregationFns) == null ? void 0 : r[e.columnDef.aggregationFn]) == null ? XF[e.columnDef.aggregationFn] : n;
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
function QF(e, t, n) {
	if (!(t != null && t.length) || !n) return e;
	let r = e.filter((e) => !t.includes(e.id));
	return n === "remove" ? r : [...t.map((t) => e.find((e) => e.id === t)).filter(Boolean), ...r];
}
var $F = {
	getInitialState: (e) => ({
		columnOrder: [],
		...e
	}),
	getDefaultOptions: (e) => ({ onColumnOrderChange: TF("columnOrder", e) }),
	createColumn: (e, t) => {
		e.getIndex = X((e) => [uI(t, e)], (t) => t.findIndex((t) => t.id === e.id), Z(t.options, "debugColumns", "getIndex")), e.getIsFirstColumn = (n) => {
			var r;
			return ((r = uI(t, n)[0]) == null ? void 0 : r.id) === e.id;
		}, e.getIsLastColumn = (n) => {
			var r;
			let i = uI(t, n);
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
			return QF(i, t, n);
		}, Z(e.options, "debugTable", "_getOrderColumnsFn"));
	}
}, eI = () => ({
	left: [],
	right: []
}), tI = {
	getInitialState: (e) => ({
		columnPinning: eI(),
		...e
	}),
	getDefaultOptions: (e) => ({ onColumnPinningChange: TF("columnPinning", e) }),
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
			return e.setColumnPinning(t || (n = (r = e.initialState) == null ? void 0 : r.columnPinning) == null ? eI() : n);
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
function nI(e) {
	return e || (typeof document < "u" ? document : null);
}
var rI = {
	size: 150,
	minSize: 20,
	maxSize: 2 ** 53 - 1
}, iI = () => ({
	startOffset: null,
	startSize: null,
	deltaOffset: null,
	deltaPercentage: null,
	isResizingColumn: !1,
	columnSizingStart: []
}), aI = {
	getDefaultColumnDef: () => rI,
	getInitialState: (e) => ({
		columnSizing: {},
		columnSizingInfo: iI(),
		...e
	}),
	getDefaultOptions: (e) => ({
		columnResizeMode: "onEnd",
		columnResizeDirection: "ltr",
		onColumnSizingChange: TF("columnSizing", e),
		onColumnSizingInfoChange: TF("columnSizingInfo", e)
	}),
	createColumn: (e, t) => {
		e.getSize = () => {
			var n, r, i;
			let a = t.getState().columnSizing[e.id];
			return Math.min(Math.max((n = e.columnDef.minSize) == null ? rI.minSize : n, (r = a == null ? e.columnDef.size : a) == null ? rI.size : r), (i = e.columnDef.maxSize) == null ? rI.maxSize : i);
		}, e.getStart = X((e) => [
			e,
			uI(t, e),
			t.getState().columnSizing
		], (t, n) => n.slice(0, e.getIndex(t)).reduce((e, t) => e + t.getSize(), 0), Z(t.options, "debugColumns", "getStart")), e.getAfter = X((e) => [
			e,
			uI(t, e),
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
				if (!r || !i || (a.persist == null || a.persist(), cI(a) && a.touches && a.touches.length > 1)) return;
				let o = e.getSize(), s = e ? e.getLeafHeaders().map((e) => [e.column.id, e.column.getSize()]) : [[r.id, r.getSize()]], c = cI(a) ? Math.round(a.touches[0].clientX) : a.clientX, l = {}, u = (e, n) => {
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
				}, p = nI(n), m = {
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
				}, g = sI() ? { passive: !1 } : !1;
				cI(a) ? (p == null || p.addEventListener("touchmove", h.moveHandler, g), p == null || p.addEventListener("touchend", h.upHandler, g)) : (p == null || p.addEventListener("mousemove", m.moveHandler, g), p == null || p.addEventListener("mouseup", m.upHandler, g)), t.setColumnSizingInfo((e) => ({
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
			e.setColumnSizingInfo(t || (n = e.initialState.columnSizingInfo) == null ? iI() : n);
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
}, oI = null;
function sI() {
	if (typeof oI == "boolean") return oI;
	let e = !1;
	try {
		let t = { get passive() {
			return e = !0, !1;
		} }, n = () => {};
		window.addEventListener("test", n, t), window.removeEventListener("test", n);
	} catch (t) {
		e = !1;
	}
	return oI = e, oI;
}
function cI(e) {
	return e.type === "touchstart";
}
var lI = {
	getInitialState: (e) => ({
		columnVisibility: {},
		...e
	}),
	getDefaultOptions: (e) => ({ onColumnVisibilityChange: TF("columnVisibility", e) }),
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
function uI(e, t) {
	return t ? t === "center" ? e.getCenterVisibleLeafColumns() : t === "left" ? e.getLeftVisibleLeafColumns() : e.getRightVisibleLeafColumns() : e.getVisibleLeafColumns();
}
var dI = { createTable: (e) => {
	e._getGlobalFacetedRowModel = e.options.getFacetedRowModel && e.options.getFacetedRowModel(e, "__global__"), e.getGlobalFacetedRowModel = () => e.options.manualFiltering || !e._getGlobalFacetedRowModel ? e.getPreFilteredRowModel() : e._getGlobalFacetedRowModel(), e._getGlobalFacetedUniqueValues = e.options.getFacetedUniqueValues && e.options.getFacetedUniqueValues(e, "__global__"), e.getGlobalFacetedUniqueValues = () => e._getGlobalFacetedUniqueValues ? e._getGlobalFacetedUniqueValues() : /* @__PURE__ */ new Map(), e._getGlobalFacetedMinMaxValues = e.options.getFacetedMinMaxValues && e.options.getFacetedMinMaxValues(e, "__global__"), e.getGlobalFacetedMinMaxValues = () => {
		if (e._getGlobalFacetedMinMaxValues) return e._getGlobalFacetedMinMaxValues();
	};
} }, fI = {
	getInitialState: (e) => ({
		globalFilter: void 0,
		...e
	}),
	getDefaultOptions: (e) => ({
		onGlobalFilterChange: TF("globalFilter", e),
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
		e.getGlobalAutoFilterFn = () => KF.includesString, e.getGlobalFilterFn = () => {
			var t, n;
			let { globalFilterFn: r } = e.options;
			return EF(r) ? r : r === "auto" ? e.getGlobalAutoFilterFn() : (t = (n = e.options.filterFns) == null ? void 0 : n[r]) == null ? KF[r] : t;
		}, e.setGlobalFilter = (t) => {
			e.options.onGlobalFilterChange == null || e.options.onGlobalFilterChange(t);
		}, e.resetGlobalFilter = (t) => {
			e.setGlobalFilter(t ? void 0 : e.initialState.globalFilter);
		};
	}
}, pI = {
	getInitialState: (e) => ({
		expanded: {},
		...e
	}),
	getDefaultOptions: (e) => ({
		onExpandedChange: TF("expanded", e),
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
}, mI = 0, hI = 10, gI = () => ({
	pageIndex: mI,
	pageSize: hI
}), _I = {
	getInitialState: (e) => ({
		...e,
		pagination: {
			...gI(),
			...e == null ? void 0 : e.pagination
		}
	}),
	getDefaultOptions: (e) => ({ onPaginationChange: TF("pagination", e) }),
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
		}, e.setPagination = (t) => e.options.onPaginationChange == null ? void 0 : e.options.onPaginationChange((e) => wF(t, e)), e.resetPagination = (t) => {
			var n;
			e.setPagination(t || (n = e.initialState.pagination) == null ? gI() : n);
		}, e.setPageIndex = (t) => {
			e.setPagination((n) => {
				let r = wF(t, n.pageIndex), i = e.options.pageCount === void 0 || e.options.pageCount === -1 ? 2 ** 53 - 1 : e.options.pageCount - 1;
				return r = Math.max(0, Math.min(r, i)), {
					...n,
					pageIndex: r
				};
			});
		}, e.resetPageIndex = (t) => {
			var n, r;
			e.setPageIndex(t || (n = (r = e.initialState) == null || (r = r.pagination) == null ? void 0 : r.pageIndex) == null ? mI : n);
		}, e.resetPageSize = (t) => {
			var n, r;
			e.setPageSize(t || (n = (r = e.initialState) == null || (r = r.pagination) == null ? void 0 : r.pageSize) == null ? hI : n);
		}, e.setPageSize = (t) => {
			e.setPagination((e) => {
				let n = Math.max(1, wF(t, e.pageSize)), r = e.pageSize * e.pageIndex, i = Math.floor(r / n);
				return {
					...e,
					pageIndex: i,
					pageSize: n
				};
			});
		}, e.setPageCount = (t) => e.setPagination((n) => {
			var r;
			let i = wF(t, (r = e.options.pageCount) == null ? -1 : r);
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
}, vI = () => ({
	top: [],
	bottom: []
}), yI = {
	getInitialState: (e) => ({
		rowPinning: vI(),
		...e
	}),
	getDefaultOptions: (e) => ({ onRowPinningChange: TF("rowPinning", e) }),
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
			return e.setRowPinning(t || (n = (r = e.initialState) == null ? void 0 : r.rowPinning) == null ? vI() : n);
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
}, bI = {
	getInitialState: (e) => ({
		rowSelection: {},
		...e
	}),
	getDefaultOptions: (e) => ({
		onRowSelectionChange: TF("rowSelection", e),
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
				xI(i, t.id, r, !0, e);
			}), i;
		}), e.getPreSelectedRowModel = () => e.getCoreRowModel(), e.getSelectedRowModel = X(() => [e.getState().rowSelection, e.getCoreRowModel()], (t, n) => Object.keys(t).length ? SI(e, n) : {
			rows: [],
			flatRows: [],
			rowsById: {}
		}, Z(e.options, "debugTable", "getSelectedRowModel")), e.getFilteredSelectedRowModel = X(() => [e.getState().rowSelection, e.getFilteredRowModel()], (t, n) => Object.keys(t).length ? SI(e, n) : {
			rows: [],
			flatRows: [],
			rowsById: {}
		}, Z(e.options, "debugTable", "getFilteredSelectedRowModel")), e.getGroupedSelectedRowModel = X(() => [e.getState().rowSelection, e.getSortedRowModel()], (t, n) => Object.keys(t).length ? SI(e, n) : {
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
				return xI(s, e.id, n, (o = r == null ? void 0 : r.selectChildren) == null || o, t), s;
			});
		}, e.getIsSelected = () => {
			let { rowSelection: n } = t.getState();
			return CI(e, n);
		}, e.getIsSomeSelected = () => {
			let { rowSelection: n } = t.getState();
			return wI(e, n) === "some";
		}, e.getIsAllSubRowsSelected = () => {
			let { rowSelection: n } = t.getState();
			return wI(e, n) === "all";
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
}, xI = (e, t, n, r, i) => {
	var a;
	let o = i.getRow(t, !0);
	n ? (o.getCanMultiSelect() || Object.keys(e).forEach((t) => delete e[t]), o.getCanSelect() && (e[t] = !0)) : delete e[t], r && (a = o.subRows) != null && a.length && o.getCanSelectSubRows() && o.subRows.forEach((t) => xI(e, t.id, n, r, i));
};
function SI(e, t) {
	let n = e.getState().rowSelection, r = [], i = {}, a = function(e, t) {
		return e.map((e) => {
			var t;
			let o = CI(e, n);
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
function CI(e, t) {
	var n;
	return (n = t[e.id]) != null && n;
}
function wI(e, t, n) {
	var r;
	if (!((r = e.subRows) != null && r.length)) return !1;
	let i = !0, a = !1;
	return e.subRows.forEach((e) => {
		if (!(a && !i) && (e.getCanSelect() && (CI(e, t) ? a = !0 : i = !1), e.subRows && e.subRows.length)) {
			let n = wI(e, t);
			n === "all" ? a = !0 : (n === "some" && (a = !0), i = !1);
		}
	}), i ? "all" : a ? "some" : !1;
}
var TI = /([0-9]+)/gm, EI = (e, t, n) => PI(NI(e.getValue(n)).toLowerCase(), NI(t.getValue(n)).toLowerCase()), DI = (e, t, n) => PI(NI(e.getValue(n)), NI(t.getValue(n))), OI = (e, t, n) => MI(NI(e.getValue(n)).toLowerCase(), NI(t.getValue(n)).toLowerCase()), kI = (e, t, n) => MI(NI(e.getValue(n)), NI(t.getValue(n))), AI = (e, t, n) => {
	let r = e.getValue(n), i = t.getValue(n);
	return r > i ? 1 : r < i ? -1 : 0;
}, jI = (e, t, n) => MI(e.getValue(n), t.getValue(n));
function MI(e, t) {
	return e === t ? 0 : e > t ? 1 : -1;
}
function NI(e) {
	return typeof e == "number" ? isNaN(e) || e === Infinity || e === -Infinity ? "" : String(e) : typeof e == "string" ? e : "";
}
function PI(e, t) {
	let n = e.split(TI).filter(Boolean), r = t.split(TI).filter(Boolean);
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
var FI = {
	alphanumeric: EI,
	alphanumericCaseSensitive: DI,
	text: OI,
	textCaseSensitive: kI,
	datetime: AI,
	basic: jI
}, II = [
	NF,
	lI,
	$F,
	tI,
	IF,
	JF,
	dI,
	fI,
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
			onSortingChange: TF("sorting", e),
			isMultiSortEvent: (e) => e.shiftKey
		}),
		createColumn: (e, t) => {
			e.getAutoSortingFn = () => {
				let n = t.getFilteredRowModel().flatRows.slice(10), r = !1;
				for (let t of n) {
					let n = t == null ? void 0 : t.getValue(e.id);
					if (Object.prototype.toString.call(n) === "[object Date]") return FI.datetime;
					if (typeof n == "string" && (r = !0, n.split(TI).length > 1)) return FI.alphanumeric;
				}
				return r ? FI.text : FI.basic;
			}, e.getAutoSortDir = () => {
				let n = t.getFilteredRowModel().flatRows[0];
				return typeof (n == null ? void 0 : n.getValue(e.id)) == "string" ? "asc" : "desc";
			}, e.getSortingFn = () => {
				var n, r;
				if (!e) throw Error();
				return EF(e.columnDef.sortingFn) ? e.columnDef.sortingFn : e.columnDef.sortingFn === "auto" ? e.getAutoSortingFn() : (n = (r = t.options.sortingFns) == null ? void 0 : r[e.columnDef.sortingFn]) == null ? FI[e.columnDef.sortingFn] : n;
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
	ZF,
	pI,
	_I,
	yI,
	bI,
	aI
];
function LI(e) {
	var t, n;
	let r = [...II, ...(t = e._features) == null ? [] : t], i = { _features: r }, a = i._features.reduce((e, t) => Object.assign(e, t.getDefaultOptions == null ? void 0 : t.getDefaultOptions(i)), {}), o = (e) => i.options.mergeOptions ? i.options.mergeOptions(a, e) : {
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
			let t = wF(e, i.options);
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
					let a = AF(i, e, r, n), o = e;
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
function RI() {
	return (e) => X(() => [e.options.data], (t) => {
		let n = {
			rows: [],
			flatRows: [],
			rowsById: {}
		}, r = function(t, i, a) {
			i === void 0 && (i = 0);
			let o = [];
			for (let c = 0; c < t.length; c++) {
				let l = FF(e, e._getRowId(t[c], c, a), t[c], c, i, void 0, a == null ? void 0 : a.id);
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
function zI() {
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
function BI(e, t) {
	return e ? VI(e) ? /*#__PURE__*/ C.createElement(e, t) : e : null;
}
function VI(e) {
	return HI(e) || typeof e == "function" || UI(e);
}
function HI(e) {
	return typeof e == "function" && (() => {
		let t = Object.getPrototypeOf(e);
		return t.prototype && t.prototype.isReactComponent;
	})();
}
function UI(e) {
	return typeof e == "object" && typeof e.$$typeof == "symbol" && ["react.memo", "react.forward_ref"].includes(e.$$typeof.description);
}
function WI(e) {
	let t = {
		state: {},
		onStateChange: () => {},
		renderFallbackValue: null,
		...e
	}, [n] = C.useState(() => ({ current: LI(t) })), [r, i] = C.useState(() => n.current.initialState);
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
var GI = "applylens:shared-filter-select-open";
function KI(e) {
	return e.toLowerCase().replace(/[\/_-]+/g, " ").trim().replace(/\s+/g, " ");
}
function qI({ id: e, label: t, options: n, values: r, onChange: i, placeholder: a, allLabel: o, mode: s, searchable: c = !1, disabled: l = !1, portalClassName: u }) {
	let [d, f] = (0, C.useState)(!1), [p, m] = (0, C.useState)(""), [h, g] = (0, C.useState)(0), [_, v] = (0, C.useState)(null), y = (0, C.useId)(), b = (0, C.useRef)(null), x = (0, C.useRef)(null), S = (0, C.useRef)([]), w = `${e}-label`, T = `${e}-menu`, E = KI(p), D = (0, C.useMemo)(() => n.filter((e) => KI(e.label).includes(E)), [E, n]), O = !!(o && (!E || KI(o).includes(E))), k = (0, C.useMemo)(() => [...O ? [{
		value: "__all__",
		label: o || a,
		isAll: !0
	}] : [], ...D.map((e) => ({
		...e,
		isAll: !1
	}))], [
		o,
		O,
		a,
		D
	]), A = r.map((e) => {
		var t;
		return (t = n.find((t) => t.value === e)) == null ? void 0 : t.label;
	}).filter(Boolean), j = A.length === 0 ? a : A.length === 1 ? A[0] : `${A.length} selected`, P = () => {
		let e = b.current;
		if (!e) return;
		let t = e.getBoundingClientRect(), n = Math.max(220, window.innerWidth - 24), r = Math.min(Math.max(t.width, 240), n), i = Math.min(Math.max(t.left, 12), window.innerWidth - r - 12), a = window.innerHeight - t.bottom - 12, o = t.top - 12, s = a < 190 && o > a ? "top" : "bottom", c = Math.max(150, Math.min(320, (s === "top" ? o : a) - 8));
		v({
			left: i,
			width: r,
			maxHeight: c,
			placement: s,
			...s === "top" ? { bottom: window.innerHeight - t.top + 6 } : { top: t.bottom + 6 }
		});
	}, F = (e = !1) => {
		f(!1), m(""), g(0), e && window.requestAnimationFrame(() => {
			var e;
			return (e = b.current) == null ? void 0 : e.focus();
		});
	}, ee = () => {
		l || (window.dispatchEvent(new CustomEvent(GI, { detail: { instanceId: y } })), f(!0), g(0));
	};
	(0, C.useLayoutEffect)(() => {
		d && P();
	}, [d, k.length]), (0, C.useEffect)(() => {
		if (!d) return;
		let e = (e) => {
			var t;
			((t = e.detail) == null ? void 0 : t.instanceId) !== y && F(!1);
		}, t = (e) => {
			var t, n;
			let r = e.target;
			!((t = b.current) != null && t.contains(r)) && !((n = x.current) != null && n.contains(r)) && F(!1);
		}, n = (e) => {
			e.key === "Escape" && (e.preventDefault(), F(!0));
		}, r = () => P();
		return window.addEventListener(GI, e), document.addEventListener("pointerdown", t), document.addEventListener("keydown", n), window.addEventListener("resize", r), window.addEventListener("scroll", r, !0), () => {
			window.removeEventListener(GI, e), document.removeEventListener("pointerdown", t), document.removeEventListener("keydown", n), window.removeEventListener("resize", r), window.removeEventListener("scroll", r, !0);
		};
	}, [y, d]), (0, C.useEffect)(() => {
		!d || c || window.requestAnimationFrame(() => {
			var e;
			return (e = S.current[h]) == null ? void 0 : e.focus();
		});
	}, [
		h,
		d,
		c
	]);
	let te = (e, t) => {
		i(t ? [] : s === "single" ? [e] : r.includes(e) ? r.filter((t) => t !== e) : [...r, e]), s === "single" && F(!0);
	}, ne = (e) => {
		if (!k.length) return;
		let t = (e + k.length) % k.length;
		g(t), window.requestAnimationFrame(() => {
			var e;
			return (e = S.current[t]) == null ? void 0 : e.focus();
		});
	}, re = (e, t) => {
		if (e.key === "Enter" || e.key === " ") {
			e.preventDefault();
			let n = k[t];
			n && te(n.value, n.isAll);
		} else e.key === "ArrowDown" ? (e.preventDefault(), ne(t + 1)) : e.key === "ArrowUp" ? (e.preventDefault(), ne(t - 1)) : e.key === "Home" ? (e.preventDefault(), ne(0)) : e.key === "End" ? (e.preventDefault(), ne(k.length - 1)) : e.key === "Tab" && F(!1);
	}, ie = _ ? {
		left: _.left,
		top: _.top,
		bottom: _.bottom,
		width: _.width,
		maxHeight: _.maxHeight
	} : void 0, ae = d && _ ? (0, Xw.createPortal)(/* @__PURE__ */ (0, Y.jsxs)("div", {
		className: `shared-filter-select__menu ${u || ""}`.trim(),
		id: T,
		ref: x,
		role: "listbox",
		"aria-labelledby": w,
		"aria-multiselectable": s === "multiple",
		"data-placement": _.placement,
		style: ie,
		children: [c ? /* @__PURE__ */ (0, Y.jsxs)("label", {
			className: "shared-filter-select__search",
			children: [
				/* @__PURE__ */ (0, Y.jsxs)("span", {
					className: "sr-only",
					children: ["Search ", t.toLowerCase()]
				}),
				/* @__PURE__ */ (0, Y.jsx)(Ce, {
					size: 15,
					"aria-hidden": "true"
				}),
				/* @__PURE__ */ (0, Y.jsx)("input", {
					autoFocus: !0,
					type: "search",
					value: p,
					onChange: (e) => {
						m(e.target.value), g(0);
					},
					onKeyDown: (e) => {
						if (e.key === "ArrowDown" && k.length) {
							var t;
							e.preventDefault(), (t = S.current[0]) == null || t.focus();
						} else e.key === "Tab" && F(!1);
					},
					placeholder: `Search ${t.toLowerCase()}`
				})
			]
		}) : null, /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "shared-filter-select__options",
			children: [k.map((e, t) => {
				let n = e.isAll ? r.length === 0 : r.includes(e.value);
				return /* @__PURE__ */ (0, Y.jsxs)("button", {
					type: "button",
					className: `shared-filter-select__option ${n ? "is-selected" : ""} ${"tone" in e && e.tone ? "has-tone" : ""}`,
					ref: (e) => {
						S.current[t] = e;
					},
					role: "option",
					"aria-selected": n,
					tabIndex: t === h ? 0 : -1,
					onFocus: () => g(t),
					onKeyDown: (e) => re(e, t),
					onClick: () => te(e.value, e.isAll),
					title: e.label,
					children: [
						/* @__PURE__ */ (0, Y.jsx)(M, {
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
			}), k.length ? null : /* @__PURE__ */ (0, Y.jsx)("div", {
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
				id: w,
				children: t
			}),
			/* @__PURE__ */ (0, Y.jsxs)("button", {
				type: "button",
				className: "shared-filter-select__trigger",
				id: e,
				ref: b,
				"aria-labelledby": `${w} ${e}-value`,
				"aria-haspopup": "listbox",
				"aria-controls": T,
				"aria-expanded": d,
				disabled: l,
				onClick: () => d ? F(!1) : ee(),
				onKeyDown: (e) => {
					[
						"Enter",
						" ",
						"ArrowDown",
						"ArrowUp"
					].includes(e.key) && (e.preventDefault(), d || ee());
				},
				children: [/* @__PURE__ */ (0, Y.jsx)("span", {
					id: `${e}-value`,
					title: j,
					children: j
				}), /* @__PURE__ */ (0, Y.jsx)(N, {
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
var JI = "preferences-secondary-action";
function YI({ expanded: e, label: t, controls: n, className: r = "", onClick: i }) {
	return /* @__PURE__ */ (0, Y.jsx)("button", {
		type: "button",
		className: `${JI} shared-table-expand-btn ${r}`.trim(),
		"aria-label": t,
		"aria-expanded": e,
		"aria-controls": e ? n : void 0,
		onClick: i,
		children: e ? /* @__PURE__ */ (0, Y.jsx)(N, {
			size: 15,
			"aria-hidden": "true"
		}) : /* @__PURE__ */ (0, Y.jsx)(P, {
			size: 15,
			"aria-hidden": "true"
		})
	});
}
function XI({ value: e, strength: t, label: n = "Match score", unavailableLabel: r = "Unavailable", className: i = "" }) {
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
function ZI({ label: e, children: t }) {
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
			className: `${JI} shared-info-popover__trigger`,
			"aria-label": e,
			"aria-expanded": n,
			"aria-controls": o,
			onClick: () => r((e) => !e),
			children: /* @__PURE__ */ (0, Y.jsx)(me, {
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
function QI({ title: e, location: t, children: n }) {
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
function $I({ children: e }) {
	return /* @__PURE__ */ (0, Y.jsx)("div", {
		className: "shared-table-details",
		children: e
	});
}
function eL({ pagination: e, visibleCount: t, noun: n = "jobs", ariaLabel: r, onPageChange: i }) {
	let { page: a, pageSize: o, totalCount: s, totalPages: c, hasPrevPage: l, hasNextPage: u } = e, d = s ? (a - 1) * o + 1 : 0, f = s ? Math.min(d + Math.max(t - 1, 0), s) : 0;
	return /* @__PURE__ */ (0, Y.jsxs)("nav", {
		className: "shared-table-pagination",
		"aria-label": r,
		children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: s ? `Showing ${d}-${f} of ${s} ${n}` : `0 ${n}` }), /* @__PURE__ */ (0, Y.jsxs)("div", { children: [
			/* @__PURE__ */ (0, Y.jsx)("button", {
				type: "button",
				className: JI,
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
				className: JI,
				disabled: !u,
				"aria-label": `Next ${r.toLowerCase()}`,
				onClick: () => i(a + 1),
				children: "Next"
			})
		] })]
	});
}
function tL(e) {
	let t = e.column.columnDef.header;
	return typeof t == "string" ? t : e.column.id.replace(/_/g, " ");
}
function nL({ header: e, sticky: t }) {
	let n = e.column.getIsSorted(), r = tL(e);
	return /* @__PURE__ */ (0, Y.jsxs)("th", {
		style: { width: e.getSize() },
		className: `shared-table-column--${e.column.id} ${t ? "is-sticky-action" : ""} ${n ? "is-sorted" : ""}`.trim(),
		"aria-sort": n === "asc" ? "ascending" : n === "desc" ? "descending" : e.column.getCanSort() ? "none" : void 0,
		children: [e.isPlaceholder ? null : /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "shared-table-header-content",
			children: [BI(e.column.columnDef.header, e.getContext()), e.column.getCanSort() ? /* @__PURE__ */ (0, Y.jsx)("button", {
				type: "button",
				className: `${JI} shared-table-sort-btn ${n ? "is-sorted" : ""}`,
				"aria-label": r,
				onClick: e.column.getToggleSortingHandler(),
				children: n === "asc" ? /* @__PURE__ */ (0, Y.jsx)(F, {
					size: 14,
					"aria-hidden": "true"
				}) : n === "desc" ? /* @__PURE__ */ (0, Y.jsx)(N, {
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
			"aria-label": `Resize ${tL(e)} column`
		}) : null]
	}, e.id);
}
function rL({ className: e, ariaLabel: t, title: n, subtitle: r, count: i, table: a, columns: o, status: s, error: c, headingActions: l, headerActions: u, pagination: d, paginationNoun: f = "jobs", paginationLabel: p, stickyColumnId: m, rowClassName: h, detailId: g, renderDetails: _, empty: v, onPageChange: y, onRetry: b, fillAvailableWidth: x = !1, deferPaginationWhileLoading: S = !1 }) {
	let C = (e) => S && s === "loading" ? /* @__PURE__ */ (0, Y.jsx)("div", {
		className: "shared-table-pagination shared-table-pagination--loading",
		role: "status",
		children: /* @__PURE__ */ (0, Y.jsxs)("span", { children: [
			"Loading ",
			f,
			"..."
		] })
	}) : /* @__PURE__ */ (0, Y.jsx)(eL, {
		pagination: d,
		visibleCount: a.getRowModel().rows.length,
		noun: f,
		ariaLabel: `${p} ${e} pagination`,
		onPageChange: y
	});
	return /* @__PURE__ */ (0, Y.jsxs)("section", {
		className: `shared-table-card ${e}`,
		"aria-label": t,
		children: [
			/* @__PURE__ */ (0, Y.jsxs)("header", {
				className: "shared-table-header",
				children: [/* @__PURE__ */ (0, Y.jsx)("div", {
					className: "shared-table-heading",
					children: l ? /* @__PURE__ */ (0, Y.jsxs)("div", {
						className: "shared-table-heading-with-actions",
						children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
							className: "shared-table-heading-copy",
							children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
								className: "shared-table-title-line",
								children: [/* @__PURE__ */ (0, Y.jsx)("h2", { children: n }), /* @__PURE__ */ (0, Y.jsx)("span", { children: S && s === "loading" ? "-" : i })]
							}), /* @__PURE__ */ (0, Y.jsx)("p", { children: S && s === "loading" ? `Loading ${f}...` : r })]
						}), /* @__PURE__ */ (0, Y.jsx)("div", {
							className: "shared-table-heading-actions",
							children: l
						})]
					}) : /* @__PURE__ */ (0, Y.jsxs)(Y.Fragment, { children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
						className: "shared-table-title-line",
						children: [/* @__PURE__ */ (0, Y.jsx)("h2", { children: n }), /* @__PURE__ */ (0, Y.jsx)("span", { children: S && s === "loading" ? "-" : i })]
					}), /* @__PURE__ */ (0, Y.jsx)("p", { children: S && s === "loading" ? `Loading ${f}...` : r })] })
				}), /* @__PURE__ */ (0, Y.jsxs)("div", {
					className: "shared-table-header-actions",
					children: [u, C("top")]
				})]
			}),
			s === "error" ? /* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "shared-table-error",
				role: "alert",
				children: [/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: "Table data is unavailable" }), /* @__PURE__ */ (0, Y.jsx)("span", { children: c || "Try the request again." })] }), /* @__PURE__ */ (0, Y.jsx)("button", {
					type: "button",
					className: JI,
					onClick: b,
					children: "Retry"
				})]
			}) : /* @__PURE__ */ (0, Y.jsx)("div", {
				className: "shared-table-viewport",
				"aria-busy": s === "loading",
				children: /* @__PURE__ */ (0, Y.jsxs)("table", {
					style: {
						width: x ? "100%" : a.getTotalSize(),
						minWidth: a.getTotalSize()
					},
					children: [/* @__PURE__ */ (0, Y.jsx)("thead", { children: a.getHeaderGroups().map((e) => /* @__PURE__ */ (0, Y.jsx)("tr", { children: e.headers.map((e) => /* @__PURE__ */ (0, Y.jsx)(nL, {
						header: e,
						sticky: e.column.id === m
					}, e.id)) }, e.id)) }), /* @__PURE__ */ (0, Y.jsx)("tbody", { children: s === "loading" ? Array.from({ length: 5 }, (e, t) => /* @__PURE__ */ (0, Y.jsx)("tr", {
						className: "shared-table-skeleton-row",
						children: /* @__PURE__ */ (0, Y.jsx)("td", {
							colSpan: o.length,
							children: /* @__PURE__ */ (0, Y.jsx)("span", {})
						})
					}, `skeleton-${t}`)) : a.getRowModel().rows.length ? a.getRowModel().rows.flatMap((e, t) => [/* @__PURE__ */ (0, Y.jsx)("tr", {
						className: h(e, t),
						children: e.getVisibleCells().map((e) => /* @__PURE__ */ (0, Y.jsx)("td", {
							style: { width: e.column.getSize() },
							className: `shared-table-column--${e.column.id} ${e.column.id === m ? "is-sticky-action" : ""}`.trim(),
							children: BI(e.column.columnDef.cell, e.getContext())
						}, e.id))
					}, e.id), e.getIsExpanded() ? /* @__PURE__ */ (0, Y.jsx)("tr", {
						className: "shared-table-detail-row",
						id: g(e),
						children: /* @__PURE__ */ (0, Y.jsx)("td", {
							colSpan: e.getVisibleCells().length,
							children: _(e)
						})
					}, `${e.id}-details`) : null]) : /* @__PURE__ */ (0, Y.jsx)("tr", { children: /* @__PURE__ */ (0, Y.jsx)("td", {
						colSpan: o.length,
						children: v
					}) }) })]
				})
			}),
			C("bottom")
		]
	});
}
//#endregion
//#region src/ExecutiveQueue.tsx
var iL = "applylens:executive-queue-state", aL = "applylens:executive-queue-action", oL = "queueTableColumnWidths", sL = JI, cL = {
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
}, lL = [
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
], uL = "A packet is a review bundle for this job. It includes the job, selected resume, match signals, gaps, and tailoring guidance. It does not apply to the job.";
function dL(e) {
	window.dispatchEvent(new CustomEvent(aL, { detail: e }));
}
function fL(e) {
	return String(e == null ? "" : e).trim();
}
function pL(e) {
	return {
		APPLY: "Ready for review",
		APPLY_REVIEW_VARIANTS: "Review resume choice",
		MAYBE_TAILOR: "Tailor first",
		SKIP_FOR_NOW: "Review later"
	}[fL(e).toUpperCase()] || fL(e) || "Unavailable";
}
function mL(e) {
	return {
		APPLY: "ready",
		APPLY_REVIEW_VARIANTS: "choice",
		MAYBE_TAILOR: "tailor",
		SKIP_FOR_NOW: "later"
	}[fL(e).toUpperCase()] || "unavailable";
}
function hL(e) {
	let t = fL(e).toLowerCase();
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
function gL(e) {
	return {
		no_deterministic_winner: "No clear resume match",
		borderline_deterministic_score: "Borderline match",
		tailoring_signal: "Tailoring may improve fit",
		tailoring_likely_worthwhile: "Tailoring may improve fit",
		packet_generation_blocked: "Packet unavailable",
		deterministic_equivalent_variants: "Close resume match",
		fallback_only_no_deterministic_match: "No credible resume match"
	}[fL(e).toLowerCase()] || fL(e).replace(/_/g, " ");
}
function _L(e) {
	return {
		SELECT_RESUME: "Choose resume",
		MAYBE_TAILOR: "Tailor first",
		SKIP_FOR_NOW: "Review later",
		APPLY: "Ready for review",
		APPLY_REVIEW_VARIANTS: "Review resume choice"
	}[fL(e.operator_decision).toUpperCase()] || {
		ready_to_apply: "Ready for review",
		tailor_then_apply: "Tailor then apply",
		review_before_action: "Review first",
		hold_or_skip: "Skip for now",
		source_watch: "Source watch"
	}[fL(e.operator_review_lane).toLowerCase()] || "—";
}
function vL(e) {
	let t = fL(e);
	return t ? t.replace(/\.pdf$/i, "").replace(/_/g, " ") : "—";
}
function yL(e) {
	if (e == null || fL(e) === "") return null;
	let t = Number(fL(e).replace(/,/g, ""));
	return Number.isFinite(t) ? Math.abs(t) <= 1 ? t * 100 : t : null;
}
function bL(e, t) {
	let n = fL(e);
	if (!n) return t === "unknown_timestamp_allowed" ? "Timestamp unavailable" : "—";
	let r = new Date(n);
	return Number.isNaN(r.getTime()) ? n : new Intl.DateTimeFormat(void 0, {
		month: "short",
		day: "numeric",
		year: "numeric"
	}).format(r);
}
function xL(e, t) {
	return fL(e.job_doc_id) || `${fL(e.queue_rank) || "row"}-${t}`;
}
function SL() {
	try {
		let e = JSON.parse(localStorage.getItem("queueTableColumnWidths") || "{}");
		return e && typeof e == "object" ? e : {};
	} catch (e) {
		return {};
	}
}
function CL({ state: e }) {
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
				/* @__PURE__ */ (0, Y.jsx)(qI, {
					id: "executiveActionFilter",
					label: "Action",
					options: lL,
					values: t.actions,
					onChange: (e) => n((t) => ({
						...t,
						actions: e
					})),
					placeholder: "All actions",
					mode: "single"
				}),
				/* @__PURE__ */ (0, Y.jsx)(qI, {
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
						children: /* @__PURE__ */ (0, Y.jsx)(me, {
							size: 14,
							"aria-label": "Shows only browse rows without an operator decision."
						})
					})] }), /* @__PURE__ */ (0, Y.jsxs)("div", {
						className: "executive-queue-segmented",
						children: [/* @__PURE__ */ (0, Y.jsx)("button", {
							type: "button",
							className: `${sL} ${t.undecidedOnly ? "" : "is-active"}`,
							"aria-pressed": !t.undecidedOnly,
							onClick: () => n((e) => ({
								...e,
								undecidedOnly: !1
							})),
							children: "No"
						}), /* @__PURE__ */ (0, Y.jsx)("button", {
							type: "button",
							className: `${sL} ${t.undecidedOnly ? "is-active" : ""}`,
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
				className: `${sL} executive-queue-clear-btn`,
				onClick: () => dL({ type: "clear_filters" }),
				children: [/* @__PURE__ */ (0, Y.jsx)(xe, {
					size: 15,
					"aria-hidden": "true"
				}), " Clear"]
			}), /* @__PURE__ */ (0, Y.jsx)("button", {
				type: "button",
				className: "executive-queue-apply-btn",
				onClick: () => dL({
					type: "apply_filters",
					filters: t
				}),
				children: "Apply Filters"
			})]
		})]
	});
}
function wL({ row: e }) {
	return /* @__PURE__ */ (0, Y.jsx)($I, { children: /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "executive-queue-details executive-queue-details--neutral",
		children: [
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Priority reason" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: gL(e.queue_priority_reason) || "—" })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Next step" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: _L(e) })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Selected resume" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: vL(e.operator_selected_resume || e.winner_resume) })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Runner-up" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: vL(e.runner_up_resume) })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Score gap" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: fL(e.score_gap) || "—" })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Missing requirements" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: fL(e.missing_requirement_count) || "0" })] }),
			/* @__PURE__ */ (0, Y.jsxs)("p", { children: [
				/* @__PURE__ */ (0, Y.jsx)(me, {
					size: 14,
					"aria-hidden": "true"
				}),
				" ",
				uL
			] })
		]
	}) });
}
function TL(e) {
	let t = {
		id: "expand",
		header: "",
		size: 42,
		minSize: 42,
		maxSize: 42,
		enableSorting: !1,
		enableResizing: !1,
		cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)(YI, {
			expanded: e.getIsExpanded(),
			label: `${e.getIsExpanded() ? "Collapse" : "Expand"} details for ${fL(e.original.job_title) || "job"}`,
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
			"aria-label": `Review ${fL(e.original.job_title) || "job"}`,
			onClick: () => dL({
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
			accessorFn: (e) => `${fL(e.job_title)} ${fL(e.job_company)}`,
			cell: ({ row: t }) => /* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "executive-queue-job-cell",
				children: [
					/* @__PURE__ */ (0, Y.jsx)("a", {
						href: fL(t.original.job_url || t.original.job_doc_id) || void 0,
						target: "_blank",
						rel: "noreferrer",
						children: fL(t.original.job_title) || "Untitled job"
					}),
					e === "simple" ? /* @__PURE__ */ (0, Y.jsx)("span", { children: fL(t.original.job_company) || "—" }) : null,
					/* @__PURE__ */ (0, Y.jsx)("small", { children: fL(t.original.job_location) || "Location unavailable" })
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
			cell: ({ row: e }) => bL(e.original.posted_at, e.original.freshness_status)
		},
		{
			id: "recommendation",
			header: "Recommendation",
			size: 180,
			minSize: 150,
			accessorFn: (e) => pL(e.action),
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)("span", {
				className: `executive-queue-badge executive-queue-badge--${mL(e.original.action)}`,
				children: pL(e.original.action)
			})
		},
		{
			id: "packet_status",
			header: () => /* @__PURE__ */ (0, Y.jsxs)("span", {
				className: "executive-queue-packet-head",
				children: ["Packet ", /* @__PURE__ */ (0, Y.jsx)(ZI, {
					label: "About review packets",
					children: uL
				})]
			}),
			size: 138,
			minSize: 120,
			accessorFn: (e) => hL(e.packet_generation_allowed),
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)("span", {
				className: `executive-queue-badge executive-queue-badge--packet ${hL(e.original.packet_generation_allowed) === "Packet ready" ? "is-ready" : ""}`,
				children: hL(e.original.packet_generation_allowed)
			})
		},
		{
			id: "winner_score",
			header: "Match",
			size: 132,
			minSize: 112,
			accessorFn: (e) => yL(e.winner_score),
			sortUndefined: "last",
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)(XI, {
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
			accessorFn: (e) => fL(e.operator_selected_resume || e.winner_resume),
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)("span", {
				className: "executive-queue-selected-resume-value",
				title: fL(e.original.operator_selected_resume || e.original.winner_resume),
				children: vL(e.original.operator_selected_resume || e.original.winner_resume)
			})
		},
		...e === "detailed" ? [
			{
				id: "runner_up_resume",
				header: "Runner-up resume",
				size: 210,
				minSize: 170,
				accessorFn: (e) => fL(e.runner_up_resume),
				cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)("span", {
					title: fL(e.original.runner_up_resume),
					children: vL(e.original.runner_up_resume)
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
				accessorFn: (e) => _L(e),
				enableSorting: !1
			},
			{
				id: "queue_priority_reason",
				header: "Priority reason",
				size: 180,
				minSize: 150,
				accessorFn: (e) => gL(e.queue_priority_reason) || "—",
				enableSorting: !1
			}
		] : [],
		n
	];
}
function EL({ state: e }) {
	let [t, n] = (0, C.useState)(SL), [r, i] = (0, C.useState)(""), a = (0, C.useMemo)(() => TL(e.viewMode), [e.viewMode]), o = (0, C.useMemo)(() => e.rows.slice(), [e.rows]), s = (0, C.useMemo)(() => e.sort.key ? [{
		id: e.sort.key,
		desc: e.sort.direction === "desc"
	}] : [], [e.sort]);
	(0, C.useEffect)(() => i(""), [
		e.rows,
		e.pagination.page,
		e.viewMode
	]);
	let c = WI({
		data: o,
		columns: a,
		state: {
			sorting: s,
			columnSizing: t,
			expanded: r ? { [r]: !0 } : {}
		},
		getRowId: (e, t) => xL(e, t),
		onSortingChange: (e) => {
			let t = (typeof e == "function" ? e(s) : e)[0];
			t && (i(""), dL({
				type: "sort_change",
				key: t.id,
				direction: t.desc ? "desc" : "asc"
			}));
		},
		onColumnSizingChange: (e) => {
			n((t) => {
				let n = typeof e == "function" ? e(t) : e;
				return localStorage.setItem(oL, JSON.stringify(n)), n;
			});
		},
		onExpandedChange: (e) => {
			let t = r ? { [r]: !0 } : {}, n = typeof e == "function" ? e(t) : e, a = n === !0 ? t : n, o = Object.keys(a).find((e) => a[e] && !t[e]);
			i(o || Object.keys(a).find((e) => a[e]) || "");
		},
		getRowCanExpand: () => !0,
		getCoreRowModel: RI(),
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
			className: `${sL} ${e.viewMode === t ? "is-active" : ""}`,
			onClick: () => dL({
				type: "view_mode_change",
				viewMode: t
			}),
			children: t === "detailed" ? "Detailed" : "Simple"
		}, t))
	});
	return /* @__PURE__ */ (0, Y.jsx)(rL, {
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
		renderDetails: (e) => /* @__PURE__ */ (0, Y.jsx)(wL, { row: e.original }),
		empty: /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "executive-queue-empty",
			children: [
				/* @__PURE__ */ (0, Y.jsx)("strong", { children: "No jobs match these filters" }),
				/* @__PURE__ */ (0, Y.jsx)("span", { children: "Clear filters to return to the complete Executive queue." }),
				/* @__PURE__ */ (0, Y.jsx)("button", {
					type: "button",
					className: sL,
					onClick: () => dL({ type: "clear_filters" }),
					children: "Clear Filters"
				})
			]
		}),
		onPageChange: (e) => dL({
			type: "page_change",
			page: e
		}),
		onRetry: () => dL({ type: "retry" })
	});
}
function DL({ state: e }) {
	return /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: `executive-queue-dashboard executive-queue-dashboard--${e.viewMode}`,
		children: [/* @__PURE__ */ (0, Y.jsx)(CL, { state: e }), /* @__PURE__ */ (0, Y.jsx)(EL, { state: e })]
	});
}
//#endregion
//#region src/pipeline/pipelineModel.ts
var OL = 2e3;
OL * 15;
var kL = [
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
], AL = {
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
}, jL = [
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
], ML = [
	["scraped_jobs", "Collected"],
	["filtered_jobs", "Filtered"],
	["deduped_jobs", "Deduplicated"],
	["ranked_jobs", "Ranked"],
	["ai_jobs", "Evaluated"],
	["resume_matched_jobs", "Resume matched"],
	["final_jobs", "Final"]
];
function NL(e) {
	let t = String(e || "idle").trim().toLowerCase();
	return t === "idle" ? "idle" : t === "queued" || t === "starting" ? "starting" : t === "running" ? "running" : t === "succeeded" ? "succeeded" : [
		"failed",
		"cancelled",
		"canceled",
		"stopped"
	].includes(t) ? "failed" : "unavailable";
}
function PL(e) {
	let t = Array.isArray(e.stage_order) ? e.stage_order.filter((e) => typeof e == "string" && e.length > 0) : [];
	return t.length ? t : [...kL];
}
function FL(e) {
	if (e === "" || e == null || typeof e == "boolean") return null;
	let t = typeof e == "number" ? e : Number(e);
	return Number.isFinite(t) && t >= 0 ? t : null;
}
function IL(e) {
	return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(e);
}
function LL(e) {
	if (!e) return "";
	let t = new Date(String(e));
	return Number.isNaN(t.getTime()) ? "" : new Intl.DateTimeFormat("en-US", {
		month: "short",
		day: "numeric",
		hour: "numeric",
		minute: "2-digit"
	}).format(t);
}
function RL(e, t, n = Date.now()) {
	let r = new Date(String(e || ""));
	if (Number.isNaN(r.getTime())) return "";
	let i = t ? new Date(String(t)) : null, a = i && !Number.isNaN(i.getTime()) ? i.getTime() : n, o = Math.max(0, Math.floor((a - r.getTime()) / 1e3)), s = Math.floor(o / 3600), c = Math.floor(o % 3600 / 60), l = o % 60;
	return s ? `${s}h ${c}m` : c ? `${c}m ${l}s` : `${l}s`;
}
function zL(e) {
	return String(e.updated_at_utc || e.updated_at || "").trim();
}
function BL(e, t = Date.now()) {
	if (NL(e.status) !== "running") return !1;
	let n = zL(e);
	if (!n) return !1;
	let r = new Date(n);
	return !Number.isNaN(r.getTime()) && t - r.getTime() > 3e4;
}
//#endregion
//#region src/pipeline/PipelineDashboard.tsx
var VL = "applylens:pipeline-run-accepted", HL = "applylens_pipeline_accepted_run_id", UL = [
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
function WL(e) {
	return AL[e] || e.replace(/_/g, " ").replace(/\b\w/g, (e) => e.toUpperCase());
}
function GL(e) {
	return e === "unavailable" ? "Unavailable" : e.charAt(0).toUpperCase() + e.slice(1);
}
function KL(e, t, n) {
	return new Set(Array.isArray(e.completed_stages) ? e.completed_stages : []).has(t) ? "complete" : t === e.current_stage && n === "failed" ? "failed" : t === e.current_stage && (n === "running" || n === "starting") ? "active" : "pending";
}
function qL(e) {
	if (typeof e == "boolean") return e ? "Enabled" : "Disabled";
	if (typeof e == "number" && Number.isFinite(e)) return IL(e);
	if (typeof e == "string") {
		let t = e.trim();
		return t ? t.toLowerCase() === "yes" ? "Enabled" : t.toLowerCase() === "no" ? "Disabled" : t : "";
	}
	return "";
}
async function JL() {
	let e = await fetch("/pipeline/status", {
		method: "GET",
		credentials: "same-origin",
		headers: { Accept: "application/json" }
	});
	if (!e.ok) throw Error(`Pipeline status request failed (${e.status})`);
	return e.json();
}
function YL() {
	if (typeof window.openApplyLensPipelineConfig == "function") {
		window.openApplyLensPipelineConfig();
		return;
	}
	console.error("The reviewed Pipeline launch flow is unavailable on this page.");
}
function XL() {
	try {
		return String(window.sessionStorage.getItem("applylens_pipeline_accepted_run_id") || "").trim();
	} catch (e) {
		return "";
	}
}
function ZL(e) {
	try {
		window.sessionStorage.getItem("applylens_pipeline_accepted_run_id") === e && window.sessionStorage.removeItem(HL);
	} catch (e) {}
}
function QL(e, t = {}) {
	return { pipeline: {
		...t,
		status: t.status || "starting",
		run_id: e || t.run_id,
		current_stage: t.current_stage || "startup",
		stage_message: t.stage_message || "Synchronizing the accepted pipeline run."
	} };
}
function $L() {
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
function eR({ onRefresh: e, onRun: t, refreshing: n, runActive: r, runBlocked: i }) {
	return /* @__PURE__ */ (0, Y.jsxs)("header", {
		className: "pipeline-dashboard-header app-page-header",
		children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "app-page-header__main",
			children: [
				/* @__PURE__ */ (0, Y.jsx)("p", {
					className: "pipeline-dashboard-eyebrow app-page-header__eyebrow",
					children: "Operations"
				}),
				/* @__PURE__ */ (0, Y.jsx)("div", {
					className: "app-page-header__title-row",
					children: /* @__PURE__ */ (0, Y.jsx)("h1", {
						className: "app-page-header__title",
						children: "Pipeline"
					})
				}),
				/* @__PURE__ */ (0, Y.jsx)("p", {
					className: "app-page-header__description",
					children: "Monitor job collection, filtering, evaluation, resume matching, and planning."
				})
			]
		}), /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "pipeline-dashboard-actions app-page-header__actions",
			children: [/* @__PURE__ */ (0, Y.jsxs)("button", {
				className: "pipeline-dashboard-btn pipeline-dashboard-btn--secondary",
				type: "button",
				onClick: e,
				disabled: n,
				children: [/* @__PURE__ */ (0, Y.jsx)(be, {
					size: 17,
					"aria-hidden": "true"
				}), n ? "Refreshing" : "Refresh Status"]
			}), /* @__PURE__ */ (0, Y.jsxs)("button", {
				className: "pipeline-dashboard-btn pipeline-dashboard-btn--primary",
				type: "button",
				onClick: t,
				disabled: r || i,
				children: [r ? /* @__PURE__ */ (0, Y.jsx)(O, {
					size: 17,
					"aria-hidden": "true"
				}) : /* @__PURE__ */ (0, Y.jsx)(ve, {
					size: 17,
					"aria-hidden": "true"
				}), r ? "Pipeline Running..." : "Run Pipeline"]
			})]
		})]
	});
}
function tR({ pipeline: e, checkedAt: t }) {
	let n = NL(e.status), r = n === "starting" || n === "running", i = PL(e), a = new Set(Array.isArray(e.completed_stages) ? e.completed_stages : []), o = i.filter((e) => a.has(e)).length, s = i.length ? Math.min(o, i.length) : 0, c = String(e.current_stage || "").trim(), l = c && c.toLowerCase() !== "unknown" ? WL(c) : n === "failed" ? "Pipeline failed" : "Not active", u = RL(e.started_at, e.finished_at, t), d = zL(e), f = BL(e, t), p = n === "failed" ? e.error || e.summary_message || e.stage_message || "The latest pipeline run did not complete." : e.summary_message || e.stage_message || (n === "idle" ? "No pipeline run is active." : n === "succeeded" ? "The latest pipeline run completed successfully." : "Waiting for pipeline status details."), m = [
		["Run ID", e.run_id],
		["Started", LL(e.started_at)],
		["Last updated", LL(d)],
		["Completed", LL(e.finished_at)],
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
					children: [/* @__PURE__ */ (0, Y.jsx)("span", { "aria-hidden": "true" }), GL(n)]
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
				children: [/* @__PURE__ */ (0, Y.jsx)(Ee, {
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
					/* @__PURE__ */ (0, Y.jsx)(se, {
						size: 18,
						"aria-hidden": "true"
					}),
					/* @__PURE__ */ (0, Y.jsx)("span", { children: "Final jobs" }),
					/* @__PURE__ */ (0, Y.jsx)("strong", { children: IL(Number(e.final_job_count)) })
				]
			}) : null
		]
	});
}
function nR({ pipeline: e }) {
	let t = NL(e.status);
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
			children: PL(e).map((n, r) => {
				let i = KL(e, n, t);
				return /* @__PURE__ */ (0, Y.jsxs)("li", {
					className: `pipeline-stage pipeline-stage--${i}`,
					"aria-current": i === "active" ? "step" : void 0,
					"data-stage-index": r + 1,
					children: [
						/* @__PURE__ */ (0, Y.jsx)("span", {
							className: "pipeline-stage-marker",
							"aria-hidden": "true",
							children: i === "complete" ? /* @__PURE__ */ (0, Y.jsx)(M, { size: 13 }) : i === "failed" ? /* @__PURE__ */ (0, Y.jsx)(Ee, { size: 13 }) : /* @__PURE__ */ (0, Y.jsx)(ne, { size: 9 })
						}),
						/* @__PURE__ */ (0, Y.jsxs)("span", {
							className: "pipeline-stage-name",
							title: WL(n),
							children: [/* @__PURE__ */ (0, Y.jsx)("span", {
								"aria-hidden": "true",
								children: String(r + 1).padStart(2, "0")
							}), WL(n)]
						}),
						/* @__PURE__ */ (0, Y.jsx)("small", { children: i === "complete" ? "Complete" : i === "active" ? "Active" : i === "failed" ? "Failed" : "Pending" })
					]
				}, n);
			})
		})]
	});
}
function rR({ pipeline: e }) {
	let t = e.counts || {}, n = jL.map((e) => ({
		label: e.label,
		values: e.keys.flatMap(([e, n]) => {
			let r = FL(t[e]);
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
						children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: e.label }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: IL(e.value) })]
					}, e.key))
				})]
			}, e.label))
		}) : /* @__PURE__ */ (0, Y.jsx)("div", {
			className: "pipeline-empty-panel pipeline-empty-panel--compact",
			children: "Stage counts are not available for this run yet."
		})]
	});
}
function iR({ pipeline: e }) {
	let t = e.counts || {}, n = ML.flatMap(([n, r]) => {
		var i;
		let a = n === "final_jobs" ? e.final_job_count : void 0, o = FL((i = t[n]) == null ? a : i);
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
			"aria-label": n.map((e) => `${e.label}: ${IL(e.value)}`).join(", "),
			children: n.map((e, t) => {
				let i = r > 0 ? Math.max(e.value / r * 100, e.value > 0 ? 3 : 0) : 0;
				return /* @__PURE__ */ (0, Y.jsxs)("div", {
					className: "pipeline-flow-step",
					children: [
						/* @__PURE__ */ (0, Y.jsxs)("div", {
							className: "pipeline-flow-meta",
							children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: e.label }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: IL(e.value) })]
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
function aR({ pipeline: e }) {
	let t = e.config || {}, n = UL.flatMap(([e, n]) => {
		let r = qL(t[e]);
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
			})] }), /* @__PURE__ */ (0, Y.jsx)(we, {
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
function oR({ pipeline: e }) {
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
			})] }), /* @__PURE__ */ (0, Y.jsx)(Te, {
				size: 20,
				"aria-hidden": "true"
			})]
		}), t.length ? /* @__PURE__ */ (0, Y.jsx)("ul", {
			className: "pipeline-health-list",
			children: t.map((e) => /* @__PURE__ */ (0, Y.jsxs)("li", { children: [
				/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: e.source }), /* @__PURE__ */ (0, Y.jsx)("span", { children: e.status || "Status unavailable" })] }),
				FL(e.jobs_returned) === null ? null : /* @__PURE__ */ (0, Y.jsxs)("span", { children: [IL(Number(e.jobs_returned)), " jobs"] }),
				e.last_success ? /* @__PURE__ */ (0, Y.jsx)("time", {
					dateTime: e.last_success,
					children: LL(e.last_success)
				}) : null
			] }, e.source))
		}) : /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "pipeline-source-unavailable",
			role: "status",
			children: [/* @__PURE__ */ (0, Y.jsx)(Te, {
				size: 18,
				"aria-hidden": "true"
			}), /* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: "Source health data is not available yet" }), /* @__PURE__ */ (0, Y.jsx)("span", { children: "No source status is inferred from missing job counts." })] })]
		})]
	});
}
function sR({ readStatus: e = JL, launchPipeline: t = YL, pollIntervalMs: n = OL }) {
	let r = XL(), i = (0, C.useRef)(r), [a, o] = (0, C.useState)(() => r ? {
		kind: "ready",
		payload: QL(r),
		checkedAt: Date.now()
	} : { kind: "loading" }), [s, c] = (0, C.useState)(!1), l = (0, C.useCallback)(async (t = !1) => {
		t && c(!0);
		try {
			var n, r;
			let t = await e(), a = i.current, s = String(((n = t.pipeline) == null ? void 0 : n.run_id) || "").trim();
			if (a && s !== a) {
				o({
					kind: "ready",
					payload: QL(a),
					checkedAt: Date.now()
				});
				return;
			}
			a && s === a && (i.current = "", ZL(a)), o({
				kind: "ready",
				payload: t,
				checkedAt: Date.now()
			});
			let c = (r = t.pipeline) == null ? void 0 : r.status;
			NL(c) === "unavailable" && console.warn(`Unsupported pipeline status: ${String(c || "")}`);
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
				payload: QL(r, n.pipeline),
				checkedAt: Date.now()
			}), l());
		};
		return window.addEventListener(VL, e), () => window.removeEventListener(VL, e);
	}, [l]);
	let u = a.kind === "ready" && a.payload.pipeline || {}, d = NL(u.status), f = a.kind === "ready" && (d === "starting" || d === "running");
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
	if (a.kind === "loading") return /* @__PURE__ */ (0, Y.jsx)($L, {});
	if (a.kind === "error") return /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "pipeline-dashboard pipeline-dashboard--error",
		children: [/* @__PURE__ */ (0, Y.jsx)(eR, {
			onRefresh: () => void l(!0),
			onRun: t,
			refreshing: s,
			runActive: !1,
			runBlocked: !0
		}), /* @__PURE__ */ (0, Y.jsxs)("section", {
			className: "pipeline-status-error",
			role: "alert",
			children: [
				/* @__PURE__ */ (0, Y.jsx)(Ee, {
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
	});
	let h = a.payload.pipeline_gate, g = (h == null ? void 0 : h.can_run_live_pipeline) === !1, _ = !!(h != null && h.requires_resume_upload), v = _ ? (h == null ? void 0 : h.profile_resume_upload_url) || "/profile?onboarding=resume_upload" : (h == null ? void 0 : h.profile_ai_settings_url) || "/profile/ai-settings", y = _ ? "Upload resume" : "Go to AI Settings";
	return /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: m,
		"data-theme-surface": "pipeline",
		"aria-busy": f,
		children: [
			/* @__PURE__ */ (0, Y.jsx)(eR, {
				onRefresh: () => void l(!0),
				onRun: t,
				refreshing: s,
				runActive: d === "starting" || d === "running",
				runBlocked: g
			}),
			g ? /* @__PURE__ */ (0, Y.jsxs)("section", {
				className: "pipeline-readiness-warning",
				role: "alert",
				children: [
					/* @__PURE__ */ (0, Y.jsx)(Ee, {
						size: 20,
						"aria-hidden": "true"
					}),
					/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: _ ? "Resume required" : "AI provider setup required" }), /* @__PURE__ */ (0, Y.jsx)("span", { children: (h == null ? void 0 : h.live_pipeline_block_reason) || "Live Pipeline prerequisites are not satisfied." })] }),
					/* @__PURE__ */ (0, Y.jsx)("a", {
						className: "pipeline-dashboard-btn pipeline-dashboard-btn--primary",
						href: v,
						children: y
					})
				]
			}) : null,
			d === "idle" ? /* @__PURE__ */ (0, Y.jsxs)("section", {
				className: "pipeline-idle-banner",
				role: "status",
				children: [/* @__PURE__ */ (0, Y.jsx)(ae, {
					size: 20,
					"aria-hidden": "true"
				}), /* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: "Pipeline is idle" }), /* @__PURE__ */ (0, Y.jsx)("span", { children: "Start a run through the existing reviewed launch flow." })] })]
			}) : null,
			/* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "pipeline-dashboard-top-grid",
				children: [/* @__PURE__ */ (0, Y.jsx)(tR, {
					pipeline: u,
					checkedAt: p
				}), /* @__PURE__ */ (0, Y.jsx)(nR, { pipeline: u })]
			}),
			/* @__PURE__ */ (0, Y.jsx)(rR, { pipeline: u }),
			/* @__PURE__ */ (0, Y.jsx)(iR, { pipeline: u }),
			/* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "pipeline-dashboard-bottom-grid",
				children: [/* @__PURE__ */ (0, Y.jsx)(aR, { pipeline: u }), /* @__PURE__ */ (0, Y.jsx)(oR, { pipeline: u })]
			})
		]
	});
}
//#endregion
//#region src/scheduler/schedulerModel.ts
var cR = class extends Error {};
async function lR() {
	let e = await fetch("/scheduler/summary?limit=25", {
		method: "GET",
		credentials: "same-origin",
		headers: { Accept: "application/json" }
	}), t = await e.json().catch(() => ({}));
	if (!e.ok) throw Error((t == null ? void 0 : t.detail) || `Scheduler summary request failed (${e.status})`);
	return t;
}
async function uR() {
	let e = await fetch("/scheduler/jobs/agent_discovery/run-now", {
		method: "POST",
		credentials: "same-origin",
		headers: { Accept: "application/json" }
	}), t = await e.json().catch(() => ({}));
	if (!e.ok) {
		var n;
		let r = typeof t.detail == "string" ? t.detail : Q((n = t.detail) == null ? void 0 : n.error_category).replace(/_/g, " ");
		throw Error(r || `Manual Agent Discovery request failed (${e.status})`);
	}
	return t;
}
async function dR(e) {
	let t = await fetch(`/scheduler/runs/${encodeURIComponent(Q(e))}/agent-discovery-summary`, {
		method: "GET",
		credentials: "same-origin",
		headers: { Accept: "application/json" }
	}), n = await t.json().catch(() => ({}));
	if (t.status === 404) throw new cR("Discovery summary unavailable");
	if (!t.ok) {
		var r;
		let e = typeof n.detail == "string" ? n.detail : (r = n.detail) == null ? void 0 : r.message;
		throw Error(e || `Discovery summary request failed (${t.status})`);
	}
	return n;
}
function Q(e) {
	return String(e == null ? "" : e).trim();
}
function fR(e, t = "Unavailable") {
	return Q(e) || t;
}
function pR(e) {
	return Q(e).toLowerCase().replace(/[^a-z0-9]+/g, "-") || "unknown";
}
var mR = new Intl.DateTimeFormat(void 0, {
	month: "short",
	day: "numeric",
	year: "numeric"
}), hR = new Intl.DateTimeFormat(void 0, {
	hour: "numeric",
	minute: "2-digit"
}), gR = new Intl.DateTimeFormat(void 0, {
	hour: "numeric",
	minute: "2-digit"
});
function _R(e) {
	let t = Q(e);
	if (!t) return "Unavailable";
	let n = new Date(t);
	return Number.isNaN(n.getTime()) ? t : `${mR.format(n)}, ${hR.format(n)}`;
}
function vR(e) {
	let t = Q(e);
	if (!t) return "Unavailable";
	let n = new Date(t);
	return Number.isNaN(n.getTime()) ? "Unavailable" : `${mR.format(n)} · ${hR.format(n)}`;
}
function yR(e, t) {
	if (e.manual_run_active === !0 || e.runtime_state === "running") return {
		tone: "running",
		label: "RUNNING NOW"
	};
	if (e.runtime_state === "unavailable") return {
		tone: "unknown",
		label: "SCHEDULE UNKNOWN"
	};
	if (e.installed === !1 || e.loaded === !1 || e.enabled === !1 || e.armed === !1 || e.runtime_state === "not_installed" || e.runtime_state === "unloaded") return {
		tone: "unavailable",
		label: "NEXT RUN UNAVAILABLE"
	};
	if (e.installed === null || e.loaded === null || e.enabled === null || e.armed === null || e.running === null) return {
		tone: "unknown",
		label: "SCHEDULE UNKNOWN"
	};
	let n = new Date(Q(e.expected_next_run_at));
	if (!e.expected_next_run_at || Number.isNaN(n.getTime())) return {
		tone: "awaiting",
		label: "SCHEDULED · AWAITING FIRST RUN"
	};
	let r = vR(e.expected_next_run_at);
	return t.getTime() > n.getTime() ? {
		tone: "overdue",
		label: `EXPECTED RUN OVERDUE · ${r}`
	} : {
		tone: "scheduled",
		label: `EXPECTED NEXT · ${r}`
	};
}
function bR(e) {
	let t = Q(e).toLowerCase();
	return t === "external_scheduler_wrapper" ? "Scheduled" : t === "manual_admin" ? "Manual" : "Unknown";
}
function xR(e) {
	return gR.format(e);
}
function SR(e) {
	return Q(e).toLowerCase() === "failed";
}
function CR(e) {
	let t = Number(e);
	if (!Number.isFinite(t) || t <= 0) return "Unavailable";
	if (t % 3600 == 0) {
		let e = t / 3600;
		return `Every ${e} ${e === 1 ? "hour" : "hours"}`;
	}
	return `Every ${t} seconds`;
}
function wR(e) {
	return [...e].sort((e, t) => {
		let n = +!SR(e.status), r = +!SR(t.status);
		if (n !== r) return n - r;
		let i = Date.parse(Q(e.started_at)) || 0;
		return (Date.parse(Q(t.started_at)) || 0) - i;
	});
}
function TR(e, t) {
	return Q(e.run_id) || [
		Q(e.job_name),
		Q(e.started_at),
		t
	].join("|");
}
//#endregion
//#region src/scheduler/SchedulerHealthDashboard.tsx
function ER(e) {
	let t = fR(e, "Unknown");
	return /* @__PURE__ */ (0, Y.jsx)("span", {
		className: `scheduler-badge scheduler-badge--${pR(e)}`,
		children: t
	});
}
function DR(e) {
	return Q(e).split("_").filter(Boolean).map((e) => `${e.charAt(0).toUpperCase()}${e.slice(1)}`).join(" ") || "Unnamed job";
}
function OR(e) {
	return e.manual_run_active === !0 ? "Running" : e.runtime_state === "not_installed" ? "Not installed" : e.runtime_state === "unloaded" ? "Unloaded" : e.runtime_state === "unavailable" ? "Unavailable" : e.runtime_state === "running" ? "Running" : "Idle";
}
function kR(e) {
	return e.armed === !0 ? "Armed" : e.enabled === !1 ? "Disabled" : e.loaded === !1 ? "Unloaded" : "Armed unknown";
}
function AR(e) {
	return e.manual_run_active === !0 || e.runtime_state === "running" ? "running" : e.runtime_state === "idle" && e.armed === !0 ? "succeeded" : e.runtime_state === "unavailable" || e.armed === null ? "unknown" : "failed";
}
function jR(e) {
	return e === !0 ? "Yes" : e === !1 ? "No" : "Unknown";
}
function MR(e) {
	if (e.manual_run_active === !0) return {
		enabled: !1,
		reason: "Agent Discovery is already running."
	};
	if (e.running === !0 || e.runtime_state === "running") return {
		enabled: !1,
		reason: "Scheduled Agent Discovery is already running."
	};
	let t = e.installed === !0 && e.loaded === !0 && e.enabled === !0 && e.armed === !0 && e.running === !1 && e.runtime_state === "idle";
	return {
		enabled: t,
		reason: t ? "Run Agent Discovery once without changing its schedule." : "Agent Discovery is unavailable until its scheduler is installed, loaded, enabled, armed, and idle."
	};
}
function NR({ onRefresh: e, refreshing: t, lastRefreshedAt: n }) {
	return /* @__PURE__ */ (0, Y.jsxs)("header", {
		className: "scheduler-health-header app-page-header",
		children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "scheduler-health-header-copy app-page-header__main",
			children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "scheduler-health-title-row app-page-header__title-row",
				children: [/* @__PURE__ */ (0, Y.jsx)("h1", {
					className: "app-page-header__title",
					children: "Scheduler Health"
				}), /* @__PURE__ */ (0, Y.jsx)("span", {
					className: "scheduler-badge scheduler-badge--muted scheduler-admin-badge app-page-header__badge",
					children: "Admin only"
				})]
			}), /* @__PURE__ */ (0, Y.jsx)("p", {
				className: "app-page-header__description",
				children: "Monitor scheduled jobs, run outcomes, persistence consistency, and configuration integrity."
			})]
		}), /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "scheduler-health-header-actions app-page-header__actions",
			children: [/* @__PURE__ */ (0, Y.jsx)("span", {
				className: "scheduler-last-refreshed",
				children: n ? `Last refreshed at ${xR(new Date(n))}` : "Not refreshed yet"
			}), /* @__PURE__ */ (0, Y.jsxs)("button", {
				type: "button",
				className: "scheduler-refresh-btn",
				onClick: e,
				disabled: t,
				"aria-label": "Refresh scheduler health",
				children: [/* @__PURE__ */ (0, Y.jsx)(be, {
					size: 15,
					"aria-hidden": "true",
					className: t ? "is-spinning" : ""
				}), "Refresh"]
			})]
		})]
	});
}
function PR({ payload: e, loading: t, onOpenDiagnostics: n, diagnosticsTriggerRef: r }) {
	var i, a, o, s, c, l, u, d, f;
	let p = !!(!(e == null || (i = e.contract_health) == null) && i.all_checks_pass), m = (e == null ? void 0 : e.runtime_jobs) || [], h = m.length === 2 && m.every((e) => e.installed !== null && e.loaded !== null && e.armed !== null && e.running !== null && e.runtime_state !== "unavailable"), g = h && m.every((e) => e.installed === !0 && e.loaded === !0 && e.armed === !0 && (e.runtime_state === "idle" || e.runtime_state === "running")), _ = !!e && p && g, v = !!e && p && !h, y = [];
	e && !p && y.push("configuration integrity"), e && h && !g && y.push("scheduler runtime");
	let b = t ? "Loading scheduler status..." : e ? _ ? "Configuration and launchd runtime are healthy." : v ? "Launchd runtime inspection is unavailable." : `Needs attention: ${y.join(" and ")}.` : "Scheduler status is unavailable.", x = [
		{
			label: "Active jobs",
			value: t || !e ? "-" : String((a = (o = e.postgres_summary) == null ? void 0 : o.active_job_count) == null ? 0 : a)
		},
		{
			label: "Successful runs",
			value: t || !e ? "-" : String((s = (c = e.postgres_summary) == null ? void 0 : c.success_count) == null ? 0 : s)
		},
		{
			label: "Failed runs",
			value: t || !e ? "-" : String((l = (u = e.postgres_summary) == null ? void 0 : u.failure_count) == null ? 0 : l)
		},
		{
			label: "Recorded runs",
			value: t || !e ? "-" : String((d = (f = e.postgres_summary) == null ? void 0 : f.run_history_count) == null ? 0 : d)
		}
	];
	return /* @__PURE__ */ (0, Y.jsxs)("section", {
		className: "scheduler-overview-panel",
		"aria-label": "Operations overview",
		children: [
			/* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "scheduler-overview-primary",
				children: [/* @__PURE__ */ (0, Y.jsx)("span", {
					className: `scheduler-overview-icon ${_ ? "is-success" : v || !e ? "is-muted" : "is-danger"}`,
					"aria-hidden": "true",
					children: t ? /* @__PURE__ */ (0, Y.jsx)(Te, { size: 22 }) : _ ? /* @__PURE__ */ (0, Y.jsx)(ee, { size: 22 }) : v ? /* @__PURE__ */ (0, Y.jsx)(O, { size: 22 }) : /* @__PURE__ */ (0, Y.jsx)(Ee, { size: 22 })
				}), /* @__PURE__ */ (0, Y.jsxs)("div", { children: [
					/* @__PURE__ */ (0, Y.jsx)("p", {
						className: "scheduler-overview-kicker",
						children: "Overall scheduler state"
					}),
					/* @__PURE__ */ (0, Y.jsx)("h2", { children: t ? "Checking..." : _ ? "Healthy" : v || !e ? "Unavailable" : "Attention" }),
					/* @__PURE__ */ (0, Y.jsx)("p", {
						className: "scheduler-overview-explanation",
						children: b
					})
				] })]
			}),
			/* @__PURE__ */ (0, Y.jsx)("div", {
				className: "scheduler-overview-divider",
				"aria-hidden": "true"
			}),
			/* @__PURE__ */ (0, Y.jsx)("div", {
				className: "scheduler-overview-metrics",
				children: x.map((e) => /* @__PURE__ */ (0, Y.jsxs)("div", {
					className: "scheduler-overview-metric",
					children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: e.label }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: e.value })]
				}, e.label))
			}),
			/* @__PURE__ */ (0, Y.jsxs)("button", {
				type: "button",
				className: "scheduler-diagnostics-link",
				onClick: n,
				ref: r,
				children: [/* @__PURE__ */ (0, Y.jsx)(ue, {
					size: 14,
					"aria-hidden": "true"
				}), "View diagnostics"]
			})
		]
	});
}
function FR({ payload: e, loading: t, manualSubmitting: n, onRequestManualDiscovery: r, manualDiscoveryTriggerRef: i }) {
	let a = (e == null ? void 0 : e.runtime_jobs) || [];
	return /* @__PURE__ */ (0, Y.jsxs)("section", {
		className: "scheduler-runtime-section",
		"aria-label": "Scheduler runtime jobs",
		children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "scheduler-runtime-section-heading",
			children: [/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("p", {
				className: "scheduler-overview-kicker",
				children: "Launchd runtime"
			}), /* @__PURE__ */ (0, Y.jsx)("h2", { children: "Scheduled jobs" })] }), /* @__PURE__ */ (0, Y.jsx)("span", { children: t ? "Inspecting runtime..." : `${a.length} external jobs` })]
		}), a.length ? /* @__PURE__ */ (0, Y.jsx)("div", {
			className: "scheduler-runtime-grid",
			children: a.map((e) => {
				let t = e.last_run, a = Q(t == null ? void 0 : t.status) || "Never run", o = AR(e), s = yR(e, new Date(Date.now())), c = MR(e);
				return /* @__PURE__ */ (0, Y.jsxs)("article", {
					className: `scheduler-runtime-card ${o === "failed" || SR(a) ? "is-attention" : ""}`,
					"data-job-name": e.job_name,
					children: [
						/* @__PURE__ */ (0, Y.jsxs)("div", {
							className: "scheduler-runtime-card-heading",
							children: [/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
								className: "scheduler-runtime-card-title-row",
								children: [/* @__PURE__ */ (0, Y.jsx)("h3", { children: DR(e.job_name) }), e.job_name === "agent_discovery" ? /* @__PURE__ */ (0, Y.jsxs)("button", {
									type: "button",
									className: "scheduler-manual-discovery-btn",
									disabled: !c.enabled || n,
									onClick: r,
									ref: i,
									title: c.reason,
									children: [/* @__PURE__ */ (0, Y.jsx)(ve, {
										size: 12,
										"aria-hidden": "true"
									}), e.manual_run_active === !0 || n ? "Discovery running…" : "Run discovery now"]
								}) : null]
							}), /* @__PURE__ */ (0, Y.jsx)("p", { children: e.description })] }), /* @__PURE__ */ (0, Y.jsxs)("div", {
								className: "scheduler-runtime-card-badges",
								children: [/* @__PURE__ */ (0, Y.jsx)("span", {
									className: `scheduler-badge scheduler-badge--${o}`,
									children: OR(e)
								}), /* @__PURE__ */ (0, Y.jsx)("span", {
									className: `scheduler-badge scheduler-badge--${e.armed === !0 ? "succeeded" : e.armed === null ? "unknown" : "failed"}`,
									children: kR(e)
								})]
							})]
						}),
						/* @__PURE__ */ (0, Y.jsxs)("dl", {
							className: "scheduler-runtime-details",
							children: [
								/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("dt", { children: "Schedule" }), /* @__PURE__ */ (0, Y.jsx)("dd", { children: CR(e.cadence_seconds) })] }),
								/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("dt", { children: "Last run" }), /* @__PURE__ */ (0, Y.jsx)("dd", {
									className: "scheduler-runtime-last-run",
									title: t ? _R(t.started_at) : void 0,
									children: t ? _R(t.started_at) : "Never run"
								})] }),
								/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("dt", { children: "Last result" }), /* @__PURE__ */ (0, Y.jsx)("dd", { children: ER(a) })] }),
								/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("dt", { children: "Return code" }), /* @__PURE__ */ (0, Y.jsx)("dd", { children: t ? fR(t.return_code, "-") : "-" })] })
							]
						}),
						/* @__PURE__ */ (0, Y.jsxs)("div", {
							className: "scheduler-runtime-card-footer",
							children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
								className: "scheduler-runtime-card-footer-state",
								children: [/* @__PURE__ */ (0, Y.jsxs)("span", { children: [/* @__PURE__ */ (0, Y.jsx)(ee, {
									size: 13,
									"aria-hidden": "true"
								}), e.installed === !0 ? "Installed" : e.installed === !1 ? "Not installed" : "Install unknown"] }), /* @__PURE__ */ (0, Y.jsxs)("span", { children: [/* @__PURE__ */ (0, Y.jsx)(ye, {
									size: 13,
									"aria-hidden": "true"
								}), e.loaded === !0 ? "Loaded" : e.loaded === !1 ? "Unloaded" : "Load unknown"] })]
							}), /* @__PURE__ */ (0, Y.jsxs)("span", {
								className: `scheduler-next-run-pill is-${s.tone}`,
								"aria-label": s.tone === "awaiting" ? "No scheduled run has been recorded yet." : void 0,
								title: s.tone === "awaiting" ? "No scheduled run has been recorded yet." : void 0,
								children: [/* @__PURE__ */ (0, Y.jsx)(oe, {
									size: 13,
									"aria-hidden": "true"
								}), s.label]
							})]
						})
					]
				}, e.job_name);
			})
		}) : /* @__PURE__ */ (0, Y.jsx)("div", {
			className: "scheduler-runtime-empty",
			children: t ? "Loading scheduler runtime..." : "Scheduler runtime is unavailable."
		})]
	});
}
function IR(e, t) {
	return /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "scheduler-run-history-job",
		children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: fR(e.job_name, "Unnamed job") }), Q(e.job_name) === "agent_discovery" && Q(e.run_id) ? /* @__PURE__ */ (0, Y.jsxs)("button", {
			type: "button",
			className: "scheduler-run-summary-view-btn",
			onClick: (n) => t(e, n.currentTarget),
			"aria-label": `View discovery summary for ${Q(e.run_id)}`,
			children: [/* @__PURE__ */ (0, Y.jsx)(ue, {
				size: 13,
				"aria-hidden": "true"
			}), "View"]
		}) : null]
	});
}
function LR(e) {
	return [
		{
			id: "job_name",
			header: "Job",
			accessorFn: (e) => Q(e.job_name),
			size: 220,
			enableSorting: !1,
			cell: ({ row: t }) => IR(t.original, e)
		},
		{
			id: "status",
			header: "Status",
			accessorFn: (e) => Q(e.status),
			size: 130,
			enableSorting: !1,
			cell: ({ row: e }) => ER(e.original.status)
		},
		{
			id: "started_at",
			header: "Last run",
			accessorFn: (e) => Q(e.started_at),
			size: 190,
			enableSorting: !1,
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)("span", { children: _R(e.original.started_at) })
		},
		{
			id: "finished_at",
			header: "Finished",
			accessorFn: (e) => Q(e.finished_at),
			size: 190,
			enableSorting: !1,
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)("span", { children: _R(e.original.finished_at) })
		},
		{
			id: "return_code",
			header: "Return code",
			accessorFn: (e) => Q(e.return_code),
			size: 110,
			enableSorting: !1,
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)("span", { children: fR(e.original.return_code, "-") })
		},
		{
			id: "run_id",
			header: "Run ID",
			accessorFn: (e) => Q(e.run_id),
			size: 160,
			enableSorting: !1,
			cell: ({ row: e }) => {
				let t = fR(e.original.run_id, "-");
				return /* @__PURE__ */ (0, Y.jsx)("span", {
					className: "scheduler-run-id-cell",
					title: t,
					children: t
				});
			}
		}
	];
}
function RR(e) {
	return [
		{
			id: "job_name",
			header: "Job",
			accessorFn: (e) => Q(e.job_name),
			size: 200,
			enableSorting: !1,
			cell: ({ row: t }) => IR(t.original, e)
		},
		{
			id: "status",
			header: "Status",
			accessorFn: (e) => Q(e.status),
			size: 130,
			enableSorting: !1,
			cell: ({ row: e }) => ER(e.original.status)
		},
		{
			id: "trigger_source",
			header: "Trigger",
			accessorFn: (e) => Q(e.trigger_source),
			size: 110,
			enableSorting: !1,
			cell: ({ row: e }) => {
				let t = bR(e.original.trigger_source);
				return /* @__PURE__ */ (0, Y.jsx)("span", {
					className: `scheduler-trigger-badge is-${t.toLowerCase()}`,
					children: t
				});
			}
		},
		{
			id: "started_at",
			header: "Started",
			accessorFn: (e) => Q(e.started_at),
			size: 190,
			enableSorting: !0,
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)("span", { children: _R(e.original.started_at) })
		},
		{
			id: "finished_at",
			header: "Finished",
			accessorFn: (e) => Q(e.finished_at),
			size: 190,
			enableSorting: !1,
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)("span", { children: _R(e.original.finished_at) })
		},
		{
			id: "return_code",
			header: "Return code",
			accessorFn: (e) => Q(e.return_code),
			size: 110,
			enableSorting: !1,
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)("span", { children: fR(e.original.return_code, "-") })
		},
		{
			id: "run_id",
			header: "Run ID",
			accessorFn: (e) => Q(e.run_id),
			size: 160,
			enableSorting: !1,
			cell: ({ row: e }) => {
				let t = fR(e.original.run_id, "-");
				return /* @__PURE__ */ (0, Y.jsx)("span", {
					className: "scheduler-run-id-cell",
					title: t,
					children: t
				});
			}
		}
	];
}
function zR({ status: e, errorMessage: t, payload: n, onRetry: r, readDiscoverySummary: i }) {
	let [a, o] = (0, C.useState)("job_status"), [s, c] = (0, C.useState)([]), [l, u] = (0, C.useState)([]), [d, f] = (0, C.useState)(null), [p, m] = (0, C.useState)(null), h = (0, C.useRef)(null), g = (0, C.useRef)(0), _ = (0, C.useMemo)(() => wR((n == null ? void 0 : n.latest_runs_by_job) || []), [n]), v = (0, C.useMemo)(() => (n == null ? void 0 : n.recent_postgres_runs) || [], [n]), y = (0, C.useMemo)(() => Array.from(new Set(v.map((e) => Q(e.job_name)).filter(Boolean))).sort().map((e) => ({
		value: e,
		label: e
	})), [v]), b = (0, C.useMemo)(() => Array.from(new Set(v.map((e) => Q(e.status)).filter(Boolean))).sort().map((e) => ({
		value: e,
		label: e
	})), [v]), x = (0, C.useMemo)(() => v.filter((e) => !(s.length && !s.includes(Q(e.job_name)) || l.length && !l.includes(Q(e.status)))), [
		v,
		s,
		l
	]), S = (0, C.useCallback)((e, t) => {
		let n = Q(e.run_id);
		if (!n) return;
		h.current = t, f(e), m({ kind: "loading" });
		let r = g.current + 1;
		g.current = r, i(n).then((e) => {
			g.current === r && m({
				kind: "ready",
				summary: e
			});
		}).catch((e) => {
			g.current === r && (e instanceof cR ? m({ kind: "unavailable" }) : m({
				kind: "error",
				message: e instanceof Error ? e.message : "Discovery summary could not be loaded."
			}));
		});
	}, [i]), w = (0, C.useCallback)(() => {
		g.current += 1, f(null), m(null);
	}, []), T = (0, C.useMemo)(() => LR(S), [S]), E = (0, C.useMemo)(() => RR(S), [S]), [D, O] = (0, C.useState)([{
		id: "started_at",
		desc: !0
	}]), k = WI({
		data: _,
		columns: T,
		getRowId: TR,
		getCoreRowModel: RI()
	}), A = WI({
		data: x,
		columns: E,
		state: { sorting: D },
		getRowId: TR,
		getCoreRowModel: RI(),
		getSortedRowModel: zI(),
		enableSortingRemoval: !1,
		onSortingChange: O
	}), j = (e) => o(e), M = (e, t) => {
		e.key !== "ArrowLeft" && e.key !== "ArrowRight" || (e.preventDefault(), j(t === "job_status" ? "run_history" : "job_status"));
	}, N = (e) => `${JI} scheduler-runs-tab ${e ? "is-active" : "is-inactive"}`, P = {
		page: 1,
		pageSize: Math.max(_.length, 1),
		totalCount: _.length,
		totalPages: 1,
		hasPrevPage: !1,
		hasNextPage: !1
	}, F = {
		page: 1,
		pageSize: Math.max(x.length, 1),
		totalCount: x.length,
		totalPages: 1,
		hasPrevPage: !1,
		hasNextPage: !1
	}, ee = /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "scheduler-runs-tabs",
		role: "tablist",
		"aria-label": "Scheduler runs view",
		children: [/* @__PURE__ */ (0, Y.jsx)("button", {
			role: "tab",
			"aria-selected": a === "job_status",
			tabIndex: a === "job_status" ? 0 : -1,
			className: N(a === "job_status"),
			onKeyDown: (e) => M(e, "job_status"),
			onClick: () => j("job_status"),
			children: "Job Status"
		}), /* @__PURE__ */ (0, Y.jsx)("button", {
			role: "tab",
			"aria-selected": a === "run_history",
			tabIndex: a === "run_history" ? 0 : -1,
			className: N(a === "run_history"),
			onKeyDown: (e) => M(e, "run_history"),
			onClick: () => j("run_history"),
			children: "Run History"
		})]
	});
	return a === "job_status" ? /* @__PURE__ */ (0, Y.jsxs)(Y.Fragment, { children: [/* @__PURE__ */ (0, Y.jsx)(rL, {
		className: "scheduler-shared-table-card",
		ariaLabel: "Job status table",
		title: "Scheduler Runs",
		subtitle: "Latest recorded result for each scheduled job.",
		count: _.length,
		table: k,
		columns: T,
		status: e,
		error: t,
		headerActions: ee,
		pagination: P,
		paginationNoun: "jobs",
		paginationLabel: "Job status",
		stickyColumnId: "run_id",
		rowClassName: (e) => `scheduler-run-row ${SR(e.original.status) ? "is-attention" : ""}`,
		detailId: () => "",
		renderDetails: () => null,
		empty: /* @__PURE__ */ (0, Y.jsx)("div", {
			className: "scheduler-empty",
			children: /* @__PURE__ */ (0, Y.jsx)("strong", { children: "No scheduler jobs recorded yet." })
		}),
		onPageChange: () => void 0,
		onRetry: r,
		fillAvailableWidth: !0
	}), /* @__PURE__ */ (0, Y.jsx)(WR, {
		run: d,
		state: p,
		onClose: w,
		triggerRef: h
	})] }) : /* @__PURE__ */ (0, Y.jsxs)(Y.Fragment, { children: [/* @__PURE__ */ (0, Y.jsx)(rL, {
		className: "scheduler-shared-table-card",
		ariaLabel: "Run history table",
		title: "Scheduler Runs",
		subtitle: "Persisted scheduler run history from Postgres.",
		count: x.length,
		table: A,
		columns: E,
		status: e,
		error: t,
		headingActions: /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "scheduler-runs-filters",
			children: [/* @__PURE__ */ (0, Y.jsx)(qI, {
				id: "schedulerRunHistoryJobFilter",
				label: "Job",
				options: y,
				values: s,
				onChange: c,
				placeholder: "All jobs",
				allLabel: "All jobs",
				mode: "single"
			}), /* @__PURE__ */ (0, Y.jsx)(qI, {
				id: "schedulerRunHistoryStatusFilter",
				label: "Status",
				options: b,
				values: l,
				onChange: u,
				placeholder: "All statuses",
				allLabel: "All statuses",
				mode: "single"
			})]
		}),
		headerActions: ee,
		pagination: F,
		paginationNoun: "runs",
		paginationLabel: "Run history",
		stickyColumnId: "run_id",
		rowClassName: (e) => `scheduler-run-row ${SR(e.original.status) ? "is-attention" : ""}`,
		detailId: () => "",
		renderDetails: () => null,
		empty: /* @__PURE__ */ (0, Y.jsx)("div", {
			className: "scheduler-empty",
			children: /* @__PURE__ */ (0, Y.jsx)("strong", { children: v.length ? "No runs match the selected filters." : "No run history recorded yet." })
		}),
		onPageChange: () => void 0,
		onRetry: r,
		fillAvailableWidth: !0
	}), /* @__PURE__ */ (0, Y.jsx)(WR, {
		run: d,
		state: p,
		onClose: w,
		triggerRef: h
	})] });
}
var BR = {
	domain_discovered: "Domain detection",
	career_discovered: "Career pages",
	network_discovered: "ATS network",
	greenhouse_embed_discovered: "Greenhouse embed",
	smartrecruiters_global_discovered: "SmartRecruiters global",
	github_discovered: "GitHub",
	sitemap_discovered: "Sitemap"
};
function VR(e) {
	let t = Q(e);
	return !t || Number.isNaN(new Date(t).getTime()) ? "—" : _R(t);
}
function HR(e, t) {
	let n = new Date(Q(e)), r = new Date(Q(t)).getTime() - n.getTime();
	if (!Number.isFinite(r) || r < 0) return "—";
	let i = Math.floor(r / 1e3), a = Math.floor(i / 60), o = i % 60;
	return a ? `${a}m ${o}s` : `${o}s`;
}
function UR(e) {
	return typeof e == "number" && Number.isFinite(e) ? e.toLocaleString() : "—";
}
function WR({ run: e, state: t, onClose: n, triggerRef: r }) {
	var i;
	let a = (0, C.useRef)(null), o = (0, C.useRef)(null);
	if ((0, C.useEffect)(() => {
		if (!e) return;
		let t = document.body.style.overflow;
		document.body.style.overflow = "hidden", window.requestAnimationFrame(() => {
			var e;
			return (e = o.current) == null ? void 0 : e.focus();
		});
		let i = (e) => {
			if (e.key === "Escape") {
				e.preventDefault(), n();
				return;
			}
			if (e.key !== "Tab" || !a.current) return;
			let t = Array.from(a.current.querySelectorAll("button:not([disabled]), [href], [tabindex]:not([tabindex='-1'])"));
			if (!t.length) return;
			let r = t[0], i = t[t.length - 1];
			e.shiftKey && document.activeElement === r ? (e.preventDefault(), i.focus()) : !e.shiftKey && document.activeElement === i && (e.preventDefault(), r.focus());
		};
		return document.addEventListener("keydown", i), () => {
			var e;
			document.removeEventListener("keydown", i), document.body.style.overflow = t, (e = r.current) == null || e.focus();
		};
	}, [
		n,
		e,
		r
	]), !e || !t) return null;
	let s = t.kind === "ready" ? t.summary : null, c = Object.entries((s == null ? void 0 : s.discovery.run_unique_discovered_by_ats) || {}), l = Object.entries((s == null ? void 0 : s.company_discovery.candidate_counts_by_ats) || {}), u = Object.entries((s == null ? void 0 : s.discovery.sources) || {}), d = c.length ? c.reduce((e, [, t]) => e + t, 0) : null, f = s == null ? void 0 : s.company_discovery.queries_failed, p = (s == null ? void 0 : s.trigger) === "manual" ? "Manual" : (s == null ? void 0 : s.trigger) === "scheduled" ? "Scheduled" : "Unknown", m = VR(s == null ? void 0 : s.started_at), h = VR(s == null ? void 0 : s.finished_at);
	return /* @__PURE__ */ (0, Y.jsx)("div", {
		className: "modal-backdrop scheduler-discovery-summary-backdrop",
		onClick: (e) => {
			e.target === e.currentTarget && n();
		},
		children: /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "modal-card scheduler-discovery-summary-modal",
			ref: a,
			role: "dialog",
			"aria-modal": "true",
			"aria-labelledby": "schedulerDiscoverySummaryTitle",
			children: [/* @__PURE__ */ (0, Y.jsxs)("header", {
				className: "scheduler-discovery-summary-header",
				children: [/* @__PURE__ */ (0, Y.jsxs)("div", { children: [
					/* @__PURE__ */ (0, Y.jsxs)("div", {
						className: "scheduler-discovery-summary-kicker",
						children: [/* @__PURE__ */ (0, Y.jsx)(ue, {
							size: 15,
							"aria-hidden": "true"
						}), " Run analytics"]
					}),
					/* @__PURE__ */ (0, Y.jsx)("h3", {
						id: "schedulerDiscoverySummaryTitle",
						children: "Discovery Run Summary"
					}),
					/* @__PURE__ */ (0, Y.jsxs)("div", {
						className: "scheduler-discovery-summary-subtitle",
						children: [
							/* @__PURE__ */ (0, Y.jsx)("span", { children: p }),
							/* @__PURE__ */ (0, Y.jsx)("span", {
								"aria-hidden": "true",
								children: "•"
							}),
							/* @__PURE__ */ (0, Y.jsx)("span", { children: VR((s == null ? void 0 : s.started_at) || e.started_at) })
						]
					})
				] }), /* @__PURE__ */ (0, Y.jsxs)("div", {
					className: "scheduler-discovery-summary-header-actions",
					children: [s ? ER(s.status) : null, /* @__PURE__ */ (0, Y.jsx)("button", {
						type: "button",
						className: "scheduler-discovery-summary-close",
						onClick: n,
						ref: o,
						"aria-label": "Close discovery run summary",
						children: /* @__PURE__ */ (0, Y.jsx)(je, {
							size: 20,
							strokeWidth: 3,
							color: "#ffffff",
							className: "scheduler-discovery-summary-close-icon",
							style: {
								width: 20,
								height: 20,
								color: "#ffffff",
								stroke: "#ffffff",
								display: "block",
								visibility: "visible",
								opacity: 1
							},
							"aria-hidden": "true"
						})
					})]
				})]
			}), /* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "scheduler-discovery-summary-body",
				children: [
					t.kind === "loading" ? /* @__PURE__ */ (0, Y.jsxs)("div", {
						className: "scheduler-discovery-summary-state",
						role: "status",
						children: [
							/* @__PURE__ */ (0, Y.jsx)(be, {
								size: 24,
								className: "is-spinning",
								"aria-hidden": "true"
							}),
							/* @__PURE__ */ (0, Y.jsx)("strong", { children: "Loading discovery summary…" }),
							/* @__PURE__ */ (0, Y.jsx)("span", { children: "Reading the persisted artifact for this exact run." })
						]
					}) : null,
					t.kind === "unavailable" ? /* @__PURE__ */ (0, Y.jsxs)("div", {
						className: "scheduler-discovery-summary-state is-unavailable",
						children: [
							/* @__PURE__ */ (0, Y.jsx)(ue, {
								size: 28,
								"aria-hidden": "true"
							}),
							/* @__PURE__ */ (0, Y.jsx)("strong", { children: "Discovery summary unavailable" }),
							/* @__PURE__ */ (0, Y.jsx)("span", { children: "This run does not have a persisted discovery summary." })
						]
					}) : null,
					t.kind === "error" ? /* @__PURE__ */ (0, Y.jsxs)("div", {
						className: "scheduler-discovery-summary-state is-error",
						role: "alert",
						children: [
							/* @__PURE__ */ (0, Y.jsx)(Ee, {
								size: 28,
								"aria-hidden": "true"
							}),
							/* @__PURE__ */ (0, Y.jsx)("strong", { children: "Discovery summary could not be loaded" }),
							/* @__PURE__ */ (0, Y.jsx)("span", { children: t.message })
						]
					}) : null,
					s ? /* @__PURE__ */ (0, Y.jsxs)(Y.Fragment, { children: [
						/* @__PURE__ */ (0, Y.jsx)("div", {
							className: "scheduler-discovery-kpi-grid",
							children: [
								[
									"Agent candidates",
									s.company_discovery.total_candidate_count,
									"blue",
									se
								],
								[
									"Unique ATS discoveries",
									d,
									"violet",
									O
								],
								[
									"Search queries",
									s.company_discovery.queries_attempted,
									"cyan",
									ue
								],
								[
									"Failed queries",
									f,
									f == null ? "neutral" : f === 0 ? "emerald" : "amber",
									Ee
								]
							].map(([e, t, n, r]) => /* @__PURE__ */ (0, Y.jsxs)("div", {
								className: `scheduler-discovery-kpi is-${n}`,
								children: [
									/* @__PURE__ */ (0, Y.jsx)("span", {
										className: "scheduler-discovery-kpi-icon",
										children: /* @__PURE__ */ (0, Y.jsx)(r, {
											size: 16,
											"aria-hidden": "true"
										})
									}),
									/* @__PURE__ */ (0, Y.jsx)("span", { children: e }),
									/* @__PURE__ */ (0, Y.jsx)("strong", { children: UR(t) })
								]
							}, e))
						}),
						/* @__PURE__ */ (0, Y.jsxs)("div", {
							className: "scheduler-discovery-summary-columns",
							children: [/* @__PURE__ */ (0, Y.jsxs)("section", {
								className: "scheduler-discovery-section",
								"aria-labelledby": "schedulerDiscoveryAtsTitle",
								children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
									className: "scheduler-discovery-section-heading",
									children: [/* @__PURE__ */ (0, Y.jsx)("h4", {
										id: "schedulerDiscoveryAtsTitle",
										children: "Discovery by ATS"
									}), /* @__PURE__ */ (0, Y.jsx)("span", { children: "Run-unique discoveries" })]
								}), c.length ? /* @__PURE__ */ (0, Y.jsx)("div", {
									className: "scheduler-discovery-ats-grid",
									children: c.map(([e, t], n) => /* @__PURE__ */ (0, Y.jsxs)("div", {
										className: `scheduler-discovery-ats-tile is-accent-${n % 4}`,
										children: [
											/* @__PURE__ */ (0, Y.jsx)("span", {
												className: "scheduler-discovery-dot",
												"aria-hidden": "true"
											}),
											/* @__PURE__ */ (0, Y.jsx)("span", { children: DR(e) }),
											/* @__PURE__ */ (0, Y.jsx)("strong", { children: t.toLocaleString() })
										]
									}, e))
								}) : /* @__PURE__ */ (0, Y.jsx)("div", {
									className: "scheduler-discovery-inline-empty",
									children: "—"
								})]
							}), /* @__PURE__ */ (0, Y.jsxs)("section", {
								className: "scheduler-discovery-section",
								"aria-labelledby": "schedulerDiscoverySourcesTitle",
								children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
									className: "scheduler-discovery-section-heading",
									children: [/* @__PURE__ */ (0, Y.jsx)("h4", {
										id: "schedulerDiscoverySourcesTitle",
										children: "Discovery sources"
									}), /* @__PURE__ */ (0, Y.jsx)("span", { children: "Candidate origins" })]
								}), u.length ? /* @__PURE__ */ (0, Y.jsx)("div", {
									className: "scheduler-discovery-source-list",
									children: u.map(([e, t], n) => {
										let r = Object.entries(t).map(([e, t]) => `${DR(e)} ${t}`).join(" · ");
										return /* @__PURE__ */ (0, Y.jsxs)("div", {
											className: `scheduler-discovery-source-row is-accent-${n % 4}`,
											children: [
												/* @__PURE__ */ (0, Y.jsx)("span", { children: BR[e] || "Discovery source" }),
												/* @__PURE__ */ (0, Y.jsx)("small", {
													title: r,
													children: r
												}),
												/* @__PURE__ */ (0, Y.jsx)("strong", { children: Object.values(t).reduce((e, t) => e + t, 0).toLocaleString() })
											]
										}, e);
									})
								}) : /* @__PURE__ */ (0, Y.jsx)("div", {
									className: "scheduler-discovery-inline-empty",
									children: "—"
								})]
							})]
						}),
						l.length ? /* @__PURE__ */ (0, Y.jsxs)("section", {
							className: "scheduler-discovery-section scheduler-discovery-candidates",
							"aria-labelledby": "schedulerDiscoveryCandidatesTitle",
							children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
								className: "scheduler-discovery-section-heading",
								children: [/* @__PURE__ */ (0, Y.jsx)("h4", {
									id: "schedulerDiscoveryCandidatesTitle",
									children: "Agent search candidates"
								}), /* @__PURE__ */ (0, Y.jsx)("span", { children: "Candidate pool by ATS" })]
							}), /* @__PURE__ */ (0, Y.jsx)("div", {
								className: "scheduler-discovery-candidate-chips",
								children: l.map(([e, t], n) => /* @__PURE__ */ (0, Y.jsxs)("span", {
									className: `is-accent-${n % 5}`,
									children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: DR(e) }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: t.toLocaleString() })]
								}, e))
							})]
						}) : null,
						/* @__PURE__ */ (0, Y.jsxs)("section", {
							className: "scheduler-discovery-section",
							"aria-labelledby": "schedulerDiscoveryExecutionTitle",
							children: [
								/* @__PURE__ */ (0, Y.jsxs)("div", {
									className: "scheduler-discovery-section-heading",
									children: [/* @__PURE__ */ (0, Y.jsx)("h4", {
										id: "schedulerDiscoveryExecutionTitle",
										children: "Execution"
									}), /* @__PURE__ */ (0, Y.jsx)("span", { children: "Component outcomes" })]
								}),
								/* @__PURE__ */ (0, Y.jsx)("div", {
									className: "scheduler-discovery-execution-grid",
									children: Object.entries(s.components).map(([e, t]) => {
										let n = e === "company_discovery_agent" ? "Company Discovery Agent" : "ATS Discovery Stage", r = t === "succeeded" ? ee : t === "failed" ? te : oe;
										return /* @__PURE__ */ (0, Y.jsxs)("div", {
											className: `scheduler-discovery-execution-item is-${t}`,
											children: [
												/* @__PURE__ */ (0, Y.jsx)(r, {
													size: 17,
													"aria-hidden": "true"
												}),
												/* @__PURE__ */ (0, Y.jsx)("span", { children: n }),
												/* @__PURE__ */ (0, Y.jsx)("strong", { children: DR(t) })
											]
										}, e);
									})
								}),
								s.failure_components.length ? /* @__PURE__ */ (0, Y.jsxs)("div", {
									className: "scheduler-discovery-failure-note",
									children: [
										/* @__PURE__ */ (0, Y.jsx)(Ee, {
											size: 14,
											"aria-hidden": "true"
										}),
										s.failure_components.length,
										" execution component",
										s.failure_components.length === 1 ? "" : "s",
										" reported failure."
									]
								}) : null
							]
						}),
						/* @__PURE__ */ (0, Y.jsxs)("footer", {
							className: "scheduler-discovery-metadata",
							children: [
								/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Started" }), /* @__PURE__ */ (0, Y.jsx)("strong", {
									title: m === "—" ? void 0 : m,
									children: m
								})] }),
								/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Finished" }), /* @__PURE__ */ (0, Y.jsx)("strong", {
									title: h === "—" ? void 0 : h,
									children: h
								})] }),
								/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Duration" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: HR(s.started_at, s.finished_at) })] }),
								/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Return code" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: (i = s.return_code) == null ? "—" : i })] }),
								/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Run ID" }), /* @__PURE__ */ (0, Y.jsx)("strong", {
									className: "scheduler-run-id-cell",
									title: s.run_id,
									children: s.run_id
								})] })
							]
						})
					] }) : null
				]
			})]
		})
	});
}
function GR({ open: e, confirming: t, onClose: n, onConfirm: r, triggerRef: i }) {
	let a = (0, C.useRef)(null), o = (0, C.useRef)(null);
	return (0, C.useEffect)(() => {
		if (!e) return;
		window.requestAnimationFrame(() => {
			var e;
			return (e = o.current) == null ? void 0 : e.focus();
		});
		let t = (e) => {
			if (e.key === "Escape") {
				e.preventDefault(), n();
				return;
			}
			if (e.key !== "Tab" || !a.current) return;
			let t = Array.from(a.current.querySelectorAll("button:not([disabled])"));
			if (!t.length) return;
			let r = t[0], i = t[t.length - 1];
			e.shiftKey && document.activeElement === r ? (e.preventDefault(), i.focus()) : !e.shiftKey && document.activeElement === i && (e.preventDefault(), r.focus());
		};
		return document.addEventListener("keydown", t), () => {
			var e;
			document.removeEventListener("keydown", t), (e = i.current) == null || e.focus();
		};
	}, [
		n,
		e,
		i
	]), e ? /* @__PURE__ */ (0, Y.jsx)("div", {
		className: "modal-backdrop",
		onClick: (e) => {
			e.target === e.currentTarget && n();
		},
		children: /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "modal-card scheduler-manual-discovery-modal",
			ref: a,
			role: "dialog",
			"aria-modal": "true",
			"aria-labelledby": "schedulerManualDiscoveryTitle",
			"aria-describedby": "schedulerManualDiscoveryDescription",
			children: [/* @__PURE__ */ (0, Y.jsx)("div", {
				className: "modal-header",
				children: /* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("h3", {
					id: "schedulerManualDiscoveryTitle",
					children: "Run discovery now?"
				}), /* @__PURE__ */ (0, Y.jsx)("div", {
					className: "subtext",
					id: "schedulerManualDiscoveryDescription",
					children: "Runs the global discovery job once immediately. This does not change the existing 24-hour schedule."
				})] })
			}), /* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "scheduler-manual-discovery-actions",
				children: [/* @__PURE__ */ (0, Y.jsx)("button", {
					type: "button",
					className: "scheduler-confirm-secondary",
					disabled: t,
					onClick: n,
					ref: o,
					children: "Cancel"
				}), /* @__PURE__ */ (0, Y.jsx)("button", {
					type: "button",
					className: "scheduler-confirm-primary",
					disabled: t,
					onClick: r,
					children: t ? "Starting discovery…" : "Run discovery"
				})]
			})]
		})
	}) : null;
}
function KR({ icon: e, label: t, ok: n, explanation: r }) {
	return /* @__PURE__ */ (0, Y.jsxs)("li", {
		className: `scheduler-config-row ${n ? "is-ok" : "is-issue"}`,
		children: [
			/* @__PURE__ */ (0, Y.jsx)(e, {
				size: 16,
				"aria-hidden": "true"
			}),
			/* @__PURE__ */ (0, Y.jsx)("span", {
				className: "scheduler-config-row-label",
				children: t
			}),
			/* @__PURE__ */ (0, Y.jsx)("span", {
				className: `scheduler-badge ${n ? "scheduler-badge--succeeded" : "scheduler-badge--failed"}`,
				children: n ? "OK" : "Issue"
			}),
			/* @__PURE__ */ (0, Y.jsx)("span", {
				className: "scheduler-config-row-explanation",
				children: r
			})
		]
	});
}
function qR({ rows: e, emptyMessage: t }) {
	return e.length ? /* @__PURE__ */ (0, Y.jsx)("div", {
		className: "scheduler-diagnostics-table-viewport",
		children: /* @__PURE__ */ (0, Y.jsxs)("table", { children: [/* @__PURE__ */ (0, Y.jsx)("thead", { children: /* @__PURE__ */ (0, Y.jsxs)("tr", { children: [
			/* @__PURE__ */ (0, Y.jsx)("th", { children: "Job" }),
			/* @__PURE__ */ (0, Y.jsx)("th", { children: "Status" }),
			/* @__PURE__ */ (0, Y.jsx)("th", { children: "Trigger" }),
			/* @__PURE__ */ (0, Y.jsx)("th", { children: "Started" }),
			/* @__PURE__ */ (0, Y.jsx)("th", { children: "Finished" }),
			/* @__PURE__ */ (0, Y.jsx)("th", { children: "Return code" }),
			/* @__PURE__ */ (0, Y.jsx)("th", { children: "Run ID" })
		] }) }), /* @__PURE__ */ (0, Y.jsx)("tbody", { children: e.map((e, t) => {
			let n = fR(e.job_name, "Unnamed job"), r = _R(e.started_at), i = _R(e.finished_at), a = fR(e.run_id, "-");
			return /* @__PURE__ */ (0, Y.jsxs)("tr", { children: [
				/* @__PURE__ */ (0, Y.jsx)("td", {
					title: n,
					children: n
				}),
				/* @__PURE__ */ (0, Y.jsx)("td", { children: ER(e.status) }),
				/* @__PURE__ */ (0, Y.jsx)("td", { children: bR(e.trigger_source) }),
				/* @__PURE__ */ (0, Y.jsx)("td", {
					title: r,
					children: r
				}),
				/* @__PURE__ */ (0, Y.jsx)("td", {
					title: i,
					children: i
				}),
				/* @__PURE__ */ (0, Y.jsx)("td", { children: fR(e.return_code, "-") }),
				/* @__PURE__ */ (0, Y.jsx)("td", {
					className: "scheduler-run-id-cell",
					title: a,
					children: a
				})
			] }, TR(e, t));
		}) })] })
	}) : /* @__PURE__ */ (0, Y.jsx)("div", {
		className: "scheduler-empty scheduler-empty--compact",
		children: t
	});
}
function JR({ open: e, payload: t, onClose: n, triggerRef: r }) {
	var i, a;
	let [o, s] = (0, C.useState)("runtime"), c = (0, C.useRef)(null), l = (0, C.useRef)(null);
	if ((0, C.useEffect)(() => {
		if (!e) return;
		s("runtime"), window.requestAnimationFrame(() => {
			var e;
			return (e = l.current) == null ? void 0 : e.focus();
		});
		let t = document.body.style.overflow;
		document.body.style.overflow = "hidden";
		let i = (e) => {
			if (e.key === "Escape") {
				e.preventDefault(), n();
				return;
			}
			if (e.key !== "Tab" || !c.current) return;
			let t = Array.from(c.current.querySelectorAll("button:not([disabled]), a[href], input:not([disabled]), [tabindex]:not([tabindex='-1'])"));
			if (!t.length) return;
			let r = t[0], i = t[t.length - 1];
			e.shiftKey && document.activeElement === r ? (e.preventDefault(), i.focus()) : !e.shiftKey && document.activeElement === i && (e.preventDefault(), r.focus());
		};
		return document.addEventListener("keydown", i), () => {
			var e;
			document.removeEventListener("keydown", i), document.body.style.overflow = t, (e = r.current) == null || e.focus();
		};
	}, [
		e,
		n,
		r
	]), !e) return null;
	let u = (t == null || (i = t.contract_health) == null ? void 0 : i.checks) || {}, d = !!(!(t == null || (a = t.contract_health) == null) && a.all_checks_pass);
	return /* @__PURE__ */ (0, Y.jsx)("div", {
		className: "modal-backdrop",
		onClick: (e) => {
			e.target === e.currentTarget && n();
		},
		children: /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "modal-card scheduler-diagnostics-modal-card",
			ref: c,
			role: "dialog",
			"aria-modal": "true",
			"aria-labelledby": "schedulerDiagnosticsModalTitle",
			"aria-describedby": "schedulerDiagnosticsModalDescription",
			children: [
				/* @__PURE__ */ (0, Y.jsxs)("div", {
					className: "modal-header",
					children: [/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("h3", {
						id: "schedulerDiagnosticsModalTitle",
						children: "Scheduler diagnostics"
					}), /* @__PURE__ */ (0, Y.jsx)("div", {
						className: "subtext",
						id: "schedulerDiagnosticsModalDescription",
						children: "Read-only launchd runtime, configuration integrity, and Postgres history."
					})] }), /* @__PURE__ */ (0, Y.jsx)("button", {
						type: "button",
						className: "ghost-btn scheduler-diagnostics-close-btn",
						onClick: n,
						ref: l,
						"aria-label": "Close diagnostics",
						children: /* @__PURE__ */ (0, Y.jsx)(je, {
							size: 16,
							"aria-hidden": "true"
						})
					})]
				}),
				/* @__PURE__ */ (0, Y.jsx)("div", {
					className: "scheduler-diagnostics-tabs",
					role: "tablist",
					"aria-label": "Diagnostics views",
					children: [
						["runtime", "Runtime"],
						["configuration", "Configuration Integrity"],
						["database_history", "Database History"]
					].map(([e, t]) => /* @__PURE__ */ (0, Y.jsx)("button", {
						role: "tab",
						"aria-selected": o === e,
						className: `${JI} scheduler-diagnostics-tab ${o === e ? "is-active" : "is-inactive"}`,
						onClick: () => s(e),
						children: t
					}, e))
				}),
				/* @__PURE__ */ (0, Y.jsxs)("div", {
					className: "modal-body scheduler-diagnostics-body",
					children: [
						o === "runtime" ? /* @__PURE__ */ (0, Y.jsx)("div", {
							className: "scheduler-runtime-diagnostics-grid",
							children: ((t == null ? void 0 : t.runtime_jobs) || []).map((e) => /* @__PURE__ */ (0, Y.jsxs)("section", {
								className: "scheduler-runtime-diagnostic-card",
								children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
									className: "scheduler-runtime-diagnostic-heading",
									children: [/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("h4", { children: DR(e.job_name) }), /* @__PURE__ */ (0, Y.jsx)("span", { children: CR(e.cadence_seconds) })] }), /* @__PURE__ */ (0, Y.jsx)("span", {
										className: `scheduler-badge scheduler-badge--${AR(e)}`,
										children: OR(e)
									})]
								}), /* @__PURE__ */ (0, Y.jsxs)("dl", { children: [
									/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("dt", { children: "Installed" }), /* @__PURE__ */ (0, Y.jsx)("dd", { children: jR(e.installed) })] }),
									/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("dt", { children: "Loaded" }), /* @__PURE__ */ (0, Y.jsx)("dd", { children: jR(e.loaded) })] }),
									/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("dt", { children: "Armed" }), /* @__PURE__ */ (0, Y.jsx)("dd", { children: jR(e.armed) })] }),
									/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("dt", { children: "Running" }), /* @__PURE__ */ (0, Y.jsx)("dd", { children: jR(e.running) })] }),
									e.job_name === "agent_discovery" ? /* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("dt", { children: "Manual run" }), /* @__PURE__ */ (0, Y.jsx)("dd", { children: e.manual_run_active === !0 ? "Active" : "Inactive" })] }) : null
								] })]
							}, e.job_name))
						}) : null,
						o === "configuration" ? /* @__PURE__ */ (0, Y.jsxs)("ul", {
							className: "scheduler-config-list",
							children: [
								/* @__PURE__ */ (0, Y.jsx)(KR, {
									icon: d ? Te : Ee,
									label: "Overall configuration integrity",
									ok: d,
									explanation: d ? "All configuration checks pass." : "One or more configuration checks failed."
								}),
								/* @__PURE__ */ (0, Y.jsx)(KR, {
									icon: u.seed_sql_matches_artifact ? ee : te,
									label: "Seed SQL artifact match",
									ok: !!u.seed_sql_matches_artifact,
									explanation: "Generated seed SQL matches the committed artifact."
								}),
								/* @__PURE__ */ (0, Y.jsx)(KR, {
									icon: u.init_sql_matches_artifact ? ee : te,
									label: "Init SQL artifact match",
									ok: !!u.init_sql_matches_artifact,
									explanation: "Generated init SQL matches the committed artifact."
								})
							]
						}) : null,
						o === "database_history" ? /* @__PURE__ */ (0, Y.jsxs)(Y.Fragment, { children: [/* @__PURE__ */ (0, Y.jsxs)("p", {
							className: "scheduler-diagnostics-tab-subtitle",
							children: [/* @__PURE__ */ (0, Y.jsx)(se, {
								size: 13,
								"aria-hidden": "true"
							}), " Recent scheduler runs currently mirrored into Postgres."]
						}), /* @__PURE__ */ (0, Y.jsx)(qR, {
							rows: (t == null ? void 0 : t.recent_postgres_runs) || [],
							emptyMessage: "No Postgres run rows recorded yet."
						})] }) : null
					]
				})
			]
		})
	});
}
function YR({ readSummary: e = lR, runDiscoveryNow: t = uR, readDiscoverySummary: n = dR }) {
	let [r, i] = (0, C.useState)({ kind: "loading" }), [a, o] = (0, C.useState)(!1), [s, c] = (0, C.useState)(!1), [l, u] = (0, C.useState)(!1), [d, f] = (0, C.useState)(!1), [p, m] = (0, C.useState)(""), h = (0, C.useRef)(null), g = (0, C.useRef)(null), _ = (0, C.useCallback)(async (t = !1) => {
		t && o(!0);
		try {
			let t = await e();
			i({
				kind: "ready",
				payload: t,
				checkedAt: Date.now()
			});
		} catch (e) {
			i({
				kind: "error",
				message: e instanceof Error ? e.message : "Scheduler summary is unavailable."
			});
		} finally {
			t && o(!1);
		}
	}, [e]), v = (0, C.useCallback)(async () => {
		f(!0), m("");
		try {
			let e = await t();
			if (!e.accepted || e.job_name !== "agent_discovery") throw Error("Manual Agent Discovery was not accepted.");
			i((e) => {
				var t;
				return e.kind === "ready" ? {
					...e,
					payload: {
						...e.payload,
						runtime_jobs: (t = e.payload.runtime_jobs) == null ? void 0 : t.map((e) => e.job_name === "agent_discovery" ? {
							...e,
							manual_run_active: !0,
							manual_run_started_at: new Date(Date.now()).toISOString()
						} : e)
					}
				} : e;
			}), u(!1);
		} catch (e) {
			m(e instanceof Error ? e.message : "Manual Agent Discovery could not be started.");
		} finally {
			f(!1);
		}
	}, [t]), y = (0, C.useCallback)(() => {
		u(!1);
	}, []), b = (0, C.useCallback)(() => {
		m(""), u(!0);
	}, []);
	(0, C.useEffect)(() => {
		_();
	}, []);
	let x = r.kind === "ready" ? r.payload : null, S = r.kind, w = r.kind === "error" ? r.message : void 0, T = r.kind === "ready" ? r.checkedAt : null;
	return /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "scheduler-health-dashboard",
		"aria-busy": r.kind === "loading",
		children: [
			/* @__PURE__ */ (0, Y.jsx)(NR, {
				onRefresh: () => void _(!0),
				refreshing: a,
				lastRefreshedAt: T
			}),
			r.kind === "error" ? /* @__PURE__ */ (0, Y.jsx)("div", {
				className: "scheduler-error-banner",
				role: "alert",
				children: r.message
			}) : null,
			p ? /* @__PURE__ */ (0, Y.jsx)("div", {
				className: "scheduler-error-banner",
				role: "alert",
				children: p
			}) : null,
			/* @__PURE__ */ (0, Y.jsx)(PR, {
				payload: x,
				loading: r.kind === "loading",
				onOpenDiagnostics: () => c(!0),
				diagnosticsTriggerRef: h
			}),
			/* @__PURE__ */ (0, Y.jsx)(FR, {
				payload: x,
				loading: r.kind === "loading",
				manualSubmitting: d,
				onRequestManualDiscovery: b,
				manualDiscoveryTriggerRef: g
			}),
			/* @__PURE__ */ (0, Y.jsx)(zR, {
				status: S,
				errorMessage: w,
				payload: x,
				onRetry: () => void _(!0),
				readDiscoverySummary: n
			}),
			/* @__PURE__ */ (0, Y.jsx)(JR, {
				open: s,
				payload: x,
				onClose: () => c(!1),
				triggerRef: h
			}),
			/* @__PURE__ */ (0, Y.jsx)(GR, {
				open: l,
				confirming: d,
				onClose: y,
				onConfirm: () => void v(),
				triggerRef: g
			})
		]
	});
}
//#endregion
//#region src/diagnostics/AdvancedDiagnosticsDashboard.tsx
var XR = {
	mode: "empty",
	savedScanOptions: [],
	selectedScanId: "",
	context: null,
	hrefs: {
		advancedDiagnostics: "/advanced-diagnostics",
		scanWorkspace: "/scan-workspace"
	}
}, ZR = [
	{
		sectionId: "advancedDiagnosticsSectionGeneration",
		navLabel: "Generation",
		tone: "blue",
		icon: ie,
		title: "Generation diagnostics",
		description: "Controls for suggestion and exact-change generation checks.",
		standaloneCheckboxes: [{
			id: "scanWorkspaceLiveTailoringSuggestionToggle",
			label: "Live tailoring suggestions"
		}, {
			id: "scanWorkspaceLiveExactChangeProposalToggle",
			label: "Live exact change proposals"
		}],
		checkboxGroups: [{
			checkbox: {
				id: "scanWorkspaceManualExactChangeAcceptanceToggle",
				label: "Accept selected exact changes"
			},
			texts: [{
				id: "scanWorkspaceAcceptedExactChangeProposalIds",
				placeholder: "Accepted proposal IDs",
				ariaLabel: "Accepted exact change proposal IDs"
			}]
		}]
	},
	{
		sectionId: "advancedDiagnosticsSectionArtifactSafety",
		navLabel: "Artifact safety",
		tone: "teal",
		icon: Te,
		title: "Resume artifact safety",
		description: "Checks protected resume-copy and artifact verification workflow.",
		checkboxGroups: [{
			checkbox: {
				id: "scanWorkspaceGuardedResumeCopyArtifactToggle",
				label: "Create guarded resume copy"
			},
			texts: [{
				id: "scanWorkspaceApprovedChangePlanId",
				placeholder: "Approved change plan ID",
				ariaLabel: "Approved change plan ID"
			}]
		}, {
			checkbox: {
				id: "scanWorkspaceGuardedResumeCopyArtifactVerificationToggle",
				label: "Verify guarded resume copy"
			},
			texts: [{
				id: "scanWorkspaceGuardedResumeCopyArtifactId",
				placeholder: "Guarded artifact ID",
				ariaLabel: "Guarded resume copy artifact ID"
			}]
		}]
	},
	{
		sectionId: "advancedDiagnosticsSectionReviewDecision",
		navLabel: "Review and decision",
		tone: "violet",
		icon: ue,
		title: "Review packet/operator decision",
		description: "Checks review-packet creation and human decision capture.",
		checkboxGroups: [{
			checkbox: {
				id: "scanWorkspaceVerifiedArtifactOperatorReviewPacketToggle",
				label: "Create verified artifact review packet"
			},
			texts: [{
				id: "scanWorkspaceVerifiedArtifactOperatorReviewArtifactId",
				placeholder: "Verified artifact ID",
				ariaLabel: "Verified artifact operator review artifact ID"
			}]
		}, {
			checkbox: {
				id: "scanWorkspaceVerifiedArtifactOperatorDecisionToggle",
				label: "Capture verified artifact operator decision"
			},
			texts: [{
				id: "scanWorkspaceVerifiedArtifactOperatorDecisionPacketId",
				placeholder: "Operator review packet ID",
				ariaLabel: "Verified artifact operator decision packet ID"
			}, {
				id: "scanWorkspaceVerifiedArtifactOperatorDecisionArtifactId",
				placeholder: "Verified artifact ID",
				ariaLabel: "Verified artifact operator decision artifact ID"
			}],
			selects: [{
				id: "scanWorkspaceVerifiedArtifactOperatorDecisionValue",
				ariaLabel: "Verified artifact operator decision value",
				options: [
					{
						value: "",
						label: "Decision"
					},
					{
						value: "accepted",
						label: "Accepted"
					},
					{
						value: "rejected",
						label: "Rejected"
					},
					{
						value: "needs_changes",
						label: "Needs changes"
					}
				]
			}]
		}]
	},
	{
		sectionId: "advancedDiagnosticsSectionManualHandoff",
		navLabel: "Manual handoff",
		tone: "amber",
		icon: pe,
		title: "Manual handoff/readiness",
		description: "Checks manual-only application handoff, readiness, audit, and safety summaries.",
		checkboxGroups: [
			{
				checkbox: {
					id: "scanWorkspaceApplicationReadinessPacketToggle",
					label: "Create application-readiness packet"
				},
				texts: [
					{
						id: "scanWorkspaceApplicationReadinessDecisionId",
						placeholder: "Operator decision ID",
						ariaLabel: "Application readiness operator decision ID"
					},
					{
						id: "scanWorkspaceApplicationReadinessReviewPacketId",
						placeholder: "Operator review packet ID",
						ariaLabel: "Application readiness operator review packet ID"
					},
					{
						id: "scanWorkspaceApplicationReadinessArtifactId",
						placeholder: "Verified artifact ID",
						ariaLabel: "Application readiness artifact ID"
					}
				]
			},
			{
				checkbox: {
					id: "scanWorkspaceManualApplicationHandoffPacketToggle",
					label: "Create human-only manual application handoff packet"
				},
				texts: [{
					id: "scanWorkspaceManualHandoffReadinessPacketId",
					placeholder: "Application readiness packet ID",
					ariaLabel: "Manual handoff application readiness packet ID"
				}, {
					id: "scanWorkspaceManualHandoffArtifactId",
					placeholder: "Verified artifact ID",
					ariaLabel: "Manual handoff verified artifact ID"
				}]
			},
			{
				checkbox: {
					id: "scanWorkspaceHandoffAuditTrailToggle",
					label: "Create human-only handoff audit trail"
				},
				texts: [
					{
						id: "scanWorkspaceHandoffAuditHandoffPacketId",
						placeholder: "Manual handoff packet ID",
						ariaLabel: "Handoff audit manual handoff packet ID"
					},
					{
						id: "scanWorkspaceHandoffAuditReadinessPacketId",
						placeholder: "Application readiness packet ID",
						ariaLabel: "Handoff audit application readiness packet ID"
					},
					{
						id: "scanWorkspaceHandoffAuditArtifactId",
						placeholder: "Verified artifact ID",
						ariaLabel: "Handoff audit verified artifact ID"
					}
				]
			},
			{
				checkbox: {
					id: "scanWorkspaceSafetyBoundarySummaryToggle",
					label: "Create human-only safety boundary summary"
				},
				texts: [
					{
						id: "scanWorkspaceSafetyBoundaryAuditTrailId",
						placeholder: "Handoff audit trail ID",
						ariaLabel: "Safety boundary handoff audit trail ID"
					},
					{
						id: "scanWorkspaceSafetyBoundaryHandoffPacketId",
						placeholder: "Manual handoff packet ID",
						ariaLabel: "Safety boundary manual handoff packet ID"
					},
					{
						id: "scanWorkspaceSafetyBoundaryReadinessPacketId",
						placeholder: "Application readiness packet ID",
						ariaLabel: "Safety boundary application readiness packet ID"
					},
					{
						id: "scanWorkspaceSafetyBoundaryArtifactId",
						placeholder: "Verified artifact ID",
						ariaLabel: "Safety boundary verified artifact ID"
					}
				]
			},
			{
				checkbox: {
					id: "scanWorkspaceWorkflowReadinessCheckpointToggle",
					label: "Create human-only workflow readiness checkpoint"
				},
				texts: [
					{
						id: "scanWorkspaceWorkflowReadinessSummaryId",
						placeholder: "Safety boundary summary ID",
						ariaLabel: "Workflow readiness safety boundary summary ID"
					},
					{
						id: "scanWorkspaceWorkflowReadinessAuditTrailId",
						placeholder: "Handoff audit trail ID",
						ariaLabel: "Workflow readiness handoff audit trail ID"
					},
					{
						id: "scanWorkspaceWorkflowReadinessHandoffPacketId",
						placeholder: "Manual handoff packet ID",
						ariaLabel: "Workflow readiness manual handoff packet ID"
					},
					{
						id: "scanWorkspaceWorkflowReadinessReadinessPacketId",
						placeholder: "Application readiness packet ID",
						ariaLabel: "Workflow readiness application readiness packet ID"
					},
					{
						id: "scanWorkspaceWorkflowReadinessArtifactId",
						placeholder: "Verified artifact ID",
						ariaLabel: "Workflow readiness verified artifact ID"
					}
				]
			}
		]
	}
], QR = "advancedDiagnosticsSectionReadbacks", $R = [
	{
		id: "scanWorkspaceJdLlmReadback",
		label: "Live JD LLM",
		tone: "default"
	},
	{
		id: "scanWorkspaceTailoringLlmReadback",
		label: "Live tailoring LLM",
		tone: "default"
	},
	{
		id: "scanWorkspaceExactChangeLlmReadback",
		label: "Live exact change LLM",
		tone: "default"
	},
	{
		id: "scanWorkspaceManualExactChangeAcceptanceReadback",
		label: "Manual exact change acceptance",
		tone: "default"
	},
	{
		id: "scanWorkspaceGuardedResumeCopyArtifactReadback",
		label: "Guarded resume copy artifact",
		tone: "default"
	},
	{
		id: "scanWorkspaceGuardedResumeCopyArtifactVerificationReadback",
		label: "Guarded artifact verification",
		tone: "default"
	},
	{
		id: "scanWorkspaceVerifiedArtifactOperatorReviewPacketReadback",
		label: "Verified artifact operator review packet",
		tone: "default"
	},
	{
		id: "scanWorkspaceVerifiedArtifactOperatorDecisionReadback",
		label: "Verified artifact operator decision",
		tone: "default"
	},
	{
		id: "scanWorkspaceApplicationReadinessPacketReadback",
		label: "Application readiness packet",
		tone: "default"
	},
	{
		id: "scanWorkspaceManualApplicationHandoffPacketReadback",
		label: "Manual application handoff packet",
		tone: "default"
	},
	{
		id: "scanWorkspaceHandoffAuditTrailReadback",
		label: "Handoff audit trail",
		tone: "default"
	},
	{
		id: "scanWorkspaceSafetyBoundarySummaryReadback",
		label: "Safety boundary summary",
		tone: "default"
	},
	{
		id: "scanWorkspaceWorkflowReadinessCheckpointReadback",
		label: "Workflow readiness checkpoint",
		tone: "default"
	},
	{
		id: "scanWorkspaceAgenticWorkflowIntegrationReadback",
		label: "Agentic workflow demo readiness",
		tone: "waiting",
		ariaLabel: "Agentic workflow demo readiness: waiting for existing scan/evaluation readback"
	},
	{
		id: "scanWorkspaceProductionReadinessCheckpointReadback",
		label: "Demo readiness",
		tone: "waiting",
		ariaLabel: "Demo readiness: backend checkpoint readback waiting for existing data"
	}
], ez = $R.filter((e) => e.tone === "default").length, tz = $R.filter((e) => e.tone === "waiting").length, nz = [...ZR.map((e) => ({
	sectionId: e.sectionId,
	label: e.navLabel
})), {
	sectionId: QR,
	label: "Readback status"
}];
function rz() {
	let e = {}, t = {}, n = {};
	for (let r of ZR) {
		for (let t of r.standaloneCheckboxes || []) e[t.id] = !1;
		for (let i of r.checkboxGroups) {
			e[i.checkbox.id] = !1;
			for (let e of i.texts || []) t[e.id] = "";
			for (let e of i.selects || []) n[e.id] = "";
		}
	}
	return {
		checkboxes: e,
		texts: t,
		selects: n
	};
}
function iz({ id: e, label: t, checked: n, onChange: r }) {
	return /* @__PURE__ */ (0, Y.jsxs)("label", {
		className: "advanced-diagnostics-checkbox-field",
		htmlFor: e,
		children: [/* @__PURE__ */ (0, Y.jsx)("input", {
			id: e,
			type: "checkbox",
			checked: n,
			onChange: (e) => r(e.target.checked)
		}), /* @__PURE__ */ (0, Y.jsx)("span", { children: t })]
	});
}
function az({ field: e, value: t, onChange: n, nested: r }) {
	return /* @__PURE__ */ (0, Y.jsx)("input", {
		type: "text",
		id: e.id,
		className: `advanced-diagnostics-text-field ${r ? "is-nested" : ""}`,
		placeholder: e.placeholder,
		"aria-label": e.ariaLabel,
		value: t,
		onChange: (e) => n(e.target.value)
	});
}
function oz({ field: e, value: t, onChange: n, nested: r }) {
	return /* @__PURE__ */ (0, Y.jsx)("select", {
		id: e.id,
		className: `advanced-diagnostics-select-field ${r ? "is-nested" : ""}`,
		"aria-label": e.ariaLabel,
		value: t,
		onChange: (e) => n(e.target.value),
		children: e.options.map((e) => /* @__PURE__ */ (0, Y.jsx)("option", {
			value: e.value,
			children: e.label
		}, e.value || "__blank__"))
	});
}
function sz({ group: e, controls: t, onCheckboxChange: n, onTextChange: r, onSelectChange: i }) {
	let a = e.icon;
	return /* @__PURE__ */ (0, Y.jsxs)("section", {
		className: "advanced-diagnostics-card",
		"data-tone": e.tone,
		id: e.sectionId,
		"aria-labelledby": `${e.sectionId}Heading`,
		children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "advanced-diagnostics-card-heading",
			children: [
				/* @__PURE__ */ (0, Y.jsx)("span", {
					className: "advanced-diagnostics-card-icon-tile",
					"aria-hidden": "true",
					children: /* @__PURE__ */ (0, Y.jsx)(a, { size: 17 })
				}),
				/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("h3", {
					id: `${e.sectionId}Heading`,
					children: e.title
				}), /* @__PURE__ */ (0, Y.jsx)("p", {
					className: "advanced-diagnostics-card-description",
					children: e.description
				})] }),
				/* @__PURE__ */ (0, Y.jsx)("span", {
					className: "advanced-diagnostics-badge advanced-diagnostics-badge--review-only",
					children: "Review only"
				})
			]
		}), /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "advanced-diagnostics-card-fields",
			children: [(e.standaloneCheckboxes || []).map((e) => /* @__PURE__ */ (0, Y.jsx)(iz, {
				id: e.id,
				label: e.label,
				checked: !!t.checkboxes[e.id],
				onChange: (t) => n(e.id, t)
			}, e.id)), e.checkboxGroups.map((e) => /* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "advanced-diagnostics-field-group",
				children: [/* @__PURE__ */ (0, Y.jsx)(iz, {
					id: e.checkbox.id,
					label: e.checkbox.label,
					checked: !!t.checkboxes[e.checkbox.id],
					onChange: (t) => n(e.checkbox.id, t)
				}), /* @__PURE__ */ (0, Y.jsxs)("div", {
					className: "advanced-diagnostics-field-group-nested",
					children: [(e.texts || []).map((e) => /* @__PURE__ */ (0, Y.jsx)(az, {
						field: e,
						value: t.texts[e.id] || "",
						onChange: (t) => r(e.id, t),
						nested: !0
					}, e.id)), (e.selects || []).map((e) => /* @__PURE__ */ (0, Y.jsx)(oz, {
						field: e,
						value: t.selects[e.id] || "",
						onChange: (t) => i(e.id, t),
						nested: !0
					}, e.id))]
				})]
			}, e.checkbox.id))]
		})]
	});
}
function cz({ row: e }) {
	return /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: `advanced-diagnostics-readback-row advanced-diagnostics-readback-row--${e.tone}`,
		id: e.id,
		"aria-live": "polite",
		...e.ariaLabel ? { "aria-label": e.ariaLabel } : {},
		children: [/* @__PURE__ */ (0, Y.jsx)("span", {
			className: "advanced-diagnostics-readback-label",
			children: e.label
		}), /* @__PURE__ */ (0, Y.jsx)("span", {
			className: `advanced-diagnostics-badge advanced-diagnostics-badge--${e.tone}`,
			children: e.tone === "waiting" ? "Waiting" : "Default off"
		})]
	});
}
function lz({ activeSection: e }) {
	return /* @__PURE__ */ (0, Y.jsxs)(Y.Fragment, { children: [/* @__PURE__ */ (0, Y.jsxs)("nav", {
		className: "advanced-diagnostics-section-rail",
		"aria-label": "Diagnostics sections",
		children: [/* @__PURE__ */ (0, Y.jsxs)("p", {
			className: "advanced-diagnostics-section-rail-summary",
			children: [
				$R.length,
				" readbacks · ",
				ez,
				" default-off · ",
				tz,
				" waiting"
			]
		}), /* @__PURE__ */ (0, Y.jsx)("ul", { children: nz.map((t) => /* @__PURE__ */ (0, Y.jsx)("li", { children: /* @__PURE__ */ (0, Y.jsx)("a", {
			href: `#${t.sectionId}`,
			className: e === t.sectionId ? "is-active" : "",
			children: t.label
		}) }, t.sectionId)) })]
	}), /* @__PURE__ */ (0, Y.jsx)("nav", {
		className: "advanced-diagnostics-section-shortcuts",
		"aria-label": "Diagnostics sections",
		children: nz.map((t) => /* @__PURE__ */ (0, Y.jsx)("a", {
			href: `#${t.sectionId}`,
			className: e === t.sectionId ? "is-active" : "",
			children: t.label
		}, t.sectionId))
	})] });
}
function uz() {
	return /* @__PURE__ */ (0, Y.jsx)("header", {
		className: "advanced-diagnostics-header app-page-header",
		children: /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "advanced-diagnostics-header-primary app-page-header__main app-page-header__main--with-icon",
			children: [/* @__PURE__ */ (0, Y.jsx)("span", {
				className: "advanced-diagnostics-header-icon-tile",
				"aria-hidden": "true",
				children: /* @__PURE__ */ (0, Y.jsx)(Te, { size: 22 })
			}), /* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "app-page-header__copy",
				children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
					className: "advanced-diagnostics-header-title-row app-page-header__title-row",
					children: [
						/* @__PURE__ */ (0, Y.jsx)("h1", {
							className: "app-page-header__title",
							children: "Advanced Diagnostics"
						}),
						/* @__PURE__ */ (0, Y.jsx)("span", {
							className: "advanced-diagnostics-badge advanced-diagnostics-badge--muted app-page-header__badge",
							children: "Admin only"
						}),
						/* @__PURE__ */ (0, Y.jsx)("span", {
							className: "advanced-diagnostics-badge advanced-diagnostics-badge--muted app-page-header__badge",
							children: "Read-only"
						})
					]
				}), /* @__PURE__ */ (0, Y.jsx)("p", {
					className: "app-page-header__description",
					children: "Admin workflow diagnostics for saved scan contexts and scan-specific readbacks."
				})]
			})]
		})
	});
}
function dz({ options: e, hrefs: t, navigate: n }) {
	let [r, i] = (0, C.useState)([]), a = (0, C.useMemo)(() => e.map((e) => ({
		value: e.scanId,
		label: e.secondary ? `${e.primary} — ${e.secondary}` : e.primary
	})), [e]);
	return /* @__PURE__ */ (0, Y.jsxs)("section", {
		className: "advanced-diagnostics-card advanced-diagnostics-hub-card",
		children: [
			/* @__PURE__ */ (0, Y.jsx)("h2", { children: "Choose a saved scan" }),
			/* @__PURE__ */ (0, Y.jsx)("p", {
				className: "advanced-diagnostics-card-description",
				children: "Select a saved scan to open scan-specific diagnostics."
			}),
			/* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "advanced-diagnostics-hub-controls",
				children: [/* @__PURE__ */ (0, Y.jsx)(qI, {
					id: "advancedDiagnosticsScanSelect",
					label: "Saved scan",
					options: a,
					values: r,
					onChange: i,
					placeholder: "Choose a saved scan...",
					mode: "single",
					searchable: !0,
					portalClassName: "advanced-diagnostics-scan-menu"
				}), /* @__PURE__ */ (0, Y.jsx)("button", {
					type: "button",
					className: "ghost-btn btn-sm advanced-diagnostics-open-btn",
					disabled: !r[0],
					onClick: () => {
						let e = r[0];
						e && n(`${t.advancedDiagnostics}?saved_scan_id=${encodeURIComponent(e)}`);
					},
					children: "Open diagnostics"
				})]
			})
		]
	});
}
function fz({ hrefs: e }) {
	return /* @__PURE__ */ (0, Y.jsxs)("section", {
		className: "advanced-diagnostics-card advanced-diagnostics-empty-card",
		children: [
			/* @__PURE__ */ (0, Y.jsx)("span", {
				className: "advanced-diagnostics-empty-icon-cluster",
				"aria-hidden": "true",
				children: /* @__PURE__ */ (0, Y.jsx)(ue, { size: 26 })
			}),
			/* @__PURE__ */ (0, Y.jsx)("h2", { children: "No saved scans available" }),
			/* @__PURE__ */ (0, Y.jsx)("p", {
				className: "advanced-diagnostics-card-description",
				children: "Advanced Diagnostics needs a saved or loaded AI Optimize Scan before scan-specific controls and readbacks can be opened."
			}),
			/* @__PURE__ */ (0, Y.jsx)("a", {
				className: "ghost-btn btn-sm",
				href: e.scanWorkspace,
				children: "Open New Scan"
			})
		]
	});
}
function pz({ hrefs: e }) {
	return /* @__PURE__ */ (0, Y.jsxs)("section", {
		className: "advanced-diagnostics-card advanced-diagnostics-invalid-card",
		children: [
			/* @__PURE__ */ (0, Y.jsx)("span", {
				className: "advanced-diagnostics-invalid-icon-tile",
				"aria-hidden": "true",
				children: /* @__PURE__ */ (0, Y.jsx)(le, { size: 26 })
			}),
			/* @__PURE__ */ (0, Y.jsx)("h2", { children: "Scan context unavailable" }),
			/* @__PURE__ */ (0, Y.jsx)("p", {
				className: "advanced-diagnostics-card-description",
				children: "This scan could not be found or is not available to this account."
			}),
			/* @__PURE__ */ (0, Y.jsx)("a", {
				className: "ghost-btn btn-sm",
				href: e.advancedDiagnostics,
				children: "Choose another saved scan"
			})
		]
	});
}
function mz({ context: e, hrefs: t }) {
	return /* @__PURE__ */ (0, Y.jsxs)("section", {
		className: "advanced-diagnostics-card advanced-diagnostics-context-hero",
		children: [
			/* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "advanced-diagnostics-context-hero-heading",
				children: [/* @__PURE__ */ (0, Y.jsx)("p", {
					className: "advanced-diagnostics-context-hero-eyebrow",
					children: "Scan context"
				}), /* @__PURE__ */ (0, Y.jsxs)("div", {
					className: "advanced-diagnostics-context-hero-actions",
					children: [/* @__PURE__ */ (0, Y.jsx)("a", {
						className: "ghost-btn btn-sm advanced-diagnostics-change-scan-btn",
						href: t.advancedDiagnostics,
						children: "Change scan"
					}), /* @__PURE__ */ (0, Y.jsx)("a", {
						className: "advanced-diagnostics-back-btn",
						href: e.backToScanHref,
						children: "Back to scan"
					})]
				})]
			}),
			/* @__PURE__ */ (0, Y.jsxs)("h2", {
				title: `${e.company} / ${e.title}`,
				children: [
					e.company,
					" / ",
					e.title
				]
			}),
			/* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "advanced-diagnostics-context-hero-pills",
				children: [
					/* @__PURE__ */ (0, Y.jsxs)("span", {
						className: "advanced-diagnostics-pill",
						title: e.resume,
						children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: "Resume" }), e.resume]
					}),
					/* @__PURE__ */ (0, Y.jsxs)("span", {
						className: "advanced-diagnostics-pill",
						title: e.status,
						children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: "Status" }), e.status]
					}),
					/* @__PURE__ */ (0, Y.jsxs)("span", {
						className: "advanced-diagnostics-pill",
						title: e.contextId,
						children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: "Context" }), /* @__PURE__ */ (0, Y.jsx)("span", {
							className: "advanced-diagnostics-pill-truncate",
							children: e.contextId
						})]
					})
				]
			})
		]
	});
}
function hz() {
	return /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "advanced-diagnostics-safety-callout",
		role: "note",
		children: [/* @__PURE__ */ (0, Y.jsx)(Te, {
			size: 18,
			"aria-hidden": "true"
		}), /* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: "Selections are review-only" }), /* @__PURE__ */ (0, Y.jsx)("p", { children: "Selecting diagnostics does not run them. These do not apply to jobs automatically. Diagnostics never apply to jobs automatically." })] })]
	});
}
function gz({ onClear: e }) {
	return /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "advanced-diagnostics-action-bar",
		children: [/* @__PURE__ */ (0, Y.jsx)("p", {
			className: "advanced-diagnostics-action-bar-note",
			children: "Selections remain local and review-only. Execution is not enabled yet. Selections are for admin review only."
		}), /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "advanced-diagnostics-action-bar-buttons",
			children: [/* @__PURE__ */ (0, Y.jsx)("button", {
				type: "button",
				className: "advanced-diagnostics-clear-btn",
				onClick: e,
				children: "Clear selections"
			}), /* @__PURE__ */ (0, Y.jsx)("button", {
				type: "button",
				className: "advanced-diagnostics-run-btn",
				disabled: !0,
				title: "Execution is not enabled yet. Selections are for admin review only.",
				children: "Run selected diagnostics"
			})]
		})]
	});
}
function _z({ state: e = XR, navigate: t = (e) => {
	window.location.href = e;
} }) {
	let [n, r] = (0, C.useState)(() => rz()), [i, a] = (0, C.useState)(nz[0].sectionId);
	(0, C.useEffect)(() => {
		if (typeof IntersectionObserver > "u") return;
		let e = new IntersectionObserver((e) => {
			var t;
			let n = e.filter((e) => e.isIntersecting).sort((e, t) => t.intersectionRatio - e.intersectionRatio)[0];
			!(n == null || (t = n.target) == null) && t.id && a(n.target.id);
		}, { rootMargin: "-35% 0px -45% 0px" });
		for (let t of nz) {
			let n = document.getElementById(t.sectionId);
			n && e.observe(n);
		}
		return () => e.disconnect();
	}, [e.mode]);
	let o = (e, t) => {
		r((n) => ({
			...n,
			checkboxes: {
				...n.checkboxes,
				[e]: t
			}
		}));
	}, s = (e, t) => {
		r((n) => ({
			...n,
			texts: {
				...n.texts,
				[e]: t
			}
		}));
	}, c = (e, t) => {
		r((n) => ({
			...n,
			selects: {
				...n.selects,
				[e]: t
			}
		}));
	}, l = () => r(rz()), u = e.mode === "context";
	return /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "advanced-diagnostics-dashboard",
		children: [
			/* @__PURE__ */ (0, Y.jsx)(uz, {}),
			e.mode === "hub" ? /* @__PURE__ */ (0, Y.jsx)(dz, {
				options: e.savedScanOptions,
				hrefs: e.hrefs,
				navigate: t
			}) : null,
			e.mode === "empty" ? /* @__PURE__ */ (0, Y.jsx)(fz, { hrefs: e.hrefs }) : null,
			e.mode === "invalid" ? /* @__PURE__ */ (0, Y.jsx)(pz, { hrefs: e.hrefs }) : null,
			e.mode === "context" && e.context ? /* @__PURE__ */ (0, Y.jsx)(mz, {
				context: e.context,
				hrefs: e.hrefs
			}) : null,
			u ? /* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "advanced-diagnostics-body",
				id: "scanWorkspaceAdvancedDiagnostics",
				children: [
					/* @__PURE__ */ (0, Y.jsx)(hz, {}),
					/* @__PURE__ */ (0, Y.jsxs)("div", {
						className: "advanced-diagnostics-layout",
						children: [/* @__PURE__ */ (0, Y.jsx)(lz, { activeSection: i }), /* @__PURE__ */ (0, Y.jsxs)("div", {
							className: "advanced-diagnostics-groups",
							children: [ZR.map((e) => /* @__PURE__ */ (0, Y.jsx)(sz, {
								group: e,
								controls: n,
								onCheckboxChange: o,
								onTextChange: s,
								onSelectChange: c
							}, e.sectionId)), /* @__PURE__ */ (0, Y.jsxs)("section", {
								className: "advanced-diagnostics-card",
								"data-tone": "slate",
								id: QR,
								"aria-labelledby": `${QR}Heading`,
								children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
									className: "advanced-diagnostics-card-heading",
									children: [/* @__PURE__ */ (0, Y.jsx)("span", {
										className: "advanced-diagnostics-card-icon-tile",
										"aria-hidden": "true",
										children: /* @__PURE__ */ (0, Y.jsx)(re, { size: 17 })
									}), /* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("h3", {
										id: `${QR}Heading`,
										children: "Readback status"
									}), /* @__PURE__ */ (0, Y.jsx)("p", {
										className: "advanced-diagnostics-card-description",
										children: "Default-off feature/readback status for this scan context."
									})] })]
								}), /* @__PURE__ */ (0, Y.jsx)("div", {
									className: "advanced-diagnostics-readbacks",
									"aria-label": "Advanced diagnostic readbacks",
									children: $R.map((e) => /* @__PURE__ */ (0, Y.jsx)(cz, { row: e }, e.id))
								})]
							})]
						})]
					}),
					/* @__PURE__ */ (0, Y.jsx)(gz, { onClear: l })
				]
			}) : null
		]
	});
}
//#endregion
//#region src/agentic/agenticOperationsModel.ts
async function vz() {
	let e = await fetch("/profile/admin/agentic-operations/overview", {
		method: "GET",
		credentials: "same-origin",
		headers: { Accept: "application/json" }
	}), t = await e.json().catch(() => ({}));
	if (!e.ok) throw Error(t.detail || `Agentic Operations overview request failed (${e.status})`);
	return t;
}
//#endregion
//#region src/agentic/AgenticOperationsDashboard.tsx
var yz = [
	{
		field: "score_mutation",
		label: "Score",
		summaryField: "score_mutation_capable_count"
	},
	{
		field: "rank_mutation",
		label: "Rank",
		summaryField: "rank_mutation_capable_count"
	},
	{
		field: "queue_mutation",
		label: "Queue",
		summaryField: "queue_mutation_capable_count"
	},
	{
		field: "resume_text_mutation",
		label: "Resume text",
		summaryField: "resume_text_mutation_capable_count"
	},
	{
		field: "operator_state_persistence",
		label: "Operator state",
		summaryField: "operator_state_persistence_capable_count"
	},
	{
		field: "application_action_capability",
		label: "Application action",
		summaryField: "application_action_capable_count"
	}
], bz = [
	"cross_user_access",
	"database_write_performed",
	"schema_write_performed",
	"provider_call_performed",
	"pipeline_execution_performed",
	"scheduler_mutation_performed",
	"scoring_changed",
	"ranking_changed",
	"queue_mutation_performed",
	"resume_mutation_performed",
	"application_execution_performed",
	"ats_submission_performed"
];
function xz(e) {
	return String(e == null ? "" : e).trim();
}
function Sz(e, t = "Unavailable") {
	let n = xz(e);
	return n ? n.replace(/[_-]+/g, " ").replace(/\b\w/g, (e) => e.toUpperCase()).replace(/\bAi\b/g, "AI") : t;
}
function Cz(e) {
	return typeof e == "number" && Number.isFinite(e) ? String(e) : "Unavailable";
}
function wz(e) {
	if (!Array.isArray(e)) return {
		agents: [],
		invalidCount: 0,
		state: "unavailable"
	};
	if (e.length === 0) return {
		agents: [],
		invalidCount: 0,
		state: "empty"
	};
	let t = e.filter((e) => {
		if (!e || typeof e != "object" || Array.isArray(e)) return !1;
		let t = e;
		return !!(xz(t.key) && xz(t.display_name) && xz(t.responsibility));
	});
	return {
		agents: t,
		invalidCount: e.length - t.length,
		state: t.length > 0 ? "available" : "unavailable"
	};
}
function Tz(e, t) {
	return !t || e.length === 0 || typeof t.canonical_agent_count != "number" || e.some((e) => yz.some(({ field: t }) => typeof e[t] != "boolean")) || yz.some(({ summaryField: e }) => typeof t[e] != "number") ? !1 : t.canonical_agent_count !== e.length || yz.some(({ field: n, summaryField: r }) => t[r] !== e.filter((e) => e[n] === !0).length);
}
var Ez = new Intl.DateTimeFormat(void 0, {
	month: "short",
	day: "numeric",
	year: "numeric",
	hour: "numeric",
	minute: "2-digit"
});
function Dz(e) {
	let t = xz(e);
	if (!t) return "Unavailable";
	let n = new Date(t);
	return Number.isNaN(n.getTime()) ? t : Ez.format(n);
}
function Oz(e) {
	return e === "not_configured" ? "No current pipeline status path is configured for the latest owner-scoped run." : e === "not_found" ? "The current pipeline status artifact was not found." : e === "malformed" ? "The current pipeline status artifact could not be read as valid status data." : "Current pipeline status is unavailable.";
}
function kz(e) {
	return e ? e.available === !0 ? Sz(e.status, "Unknown") : Sz(e.state) : "Unavailable";
}
function Az(e) {
	let t = e.safety_metadata;
	return !!(e.read_only === !0 && e.admin_only === !0 && (t == null ? void 0 : t.read_only) === !0 && t.admin_only === !0 && bz.every((e) => t[e] === !1));
}
function jz({ confirmed: e }) {
	let t = document.getElementById("agenticOperationsHeaderReadOnlyBadge");
	return !e || !t ? null : (0, Xw.createPortal)(/* @__PURE__ */ (0, Y.jsx)("span", {
		className: "agentic-operations-header-badge app-page-header__badge",
		children: "Read-only"
	}), t);
}
function Mz(e) {
	let t = xz(e).toLowerCase();
	return [
		"succeeded",
		"complete",
		"completed",
		"available"
	].includes(t) ? "success" : [
		"failed",
		"error",
		"malformed"
	].includes(t) ? "danger" : [
		"running",
		"in_progress",
		"processing"
	].includes(t) ? "active" : "neutral";
}
function Nz() {
	return /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "agentic-operations-loading",
		role: "status",
		children: [/* @__PURE__ */ (0, Y.jsx)("span", {
			className: "agentic-operations-loading-icon",
			"aria-hidden": "true",
			children: /* @__PURE__ */ (0, Y.jsx)(O, { size: 20 })
		}), /* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: "Loading operations overview…" }), /* @__PURE__ */ (0, Y.jsx)("span", { children: "Reading current pipeline, recent runs, and safety metadata." })] })]
	});
}
function Pz({ payload: e }) {
	var t;
	let n = e.current_pipeline, r = e.recent_runs_state, i = (t = e.safety_summary) == null ? void 0 : t.canonical_agent_count;
	return /* @__PURE__ */ (0, Y.jsx)("section", {
		className: "agentic-operations-summary-grid",
		"aria-label": "Agentic Operations summary",
		children: [
			{
				icon: O,
				label: "Pipeline status",
				value: kz(n),
				detail: (n == null ? void 0 : n.available) === !0 ? "Current owner-scoped run" : "Status readback"
			},
			{
				icon: Ae,
				label: "Current stage",
				value: (n == null ? void 0 : n.available) === !0 ? Sz(n.current_stage) : "Unavailable",
				detail: (n == null ? void 0 : n.available) === !0 ? xz(n.stage_message) || "No stage message recorded" : "No available current stage"
			},
			{
				icon: ae,
				label: "Recent runs",
				value: (r == null ? void 0 : r.available) === !0 ? Cz(r.count) : "Unavailable",
				detail: (r == null ? void 0 : r.available) === !0 ? `Bounded to ${Cz(r.bound)}` : "Owner-scoped history unavailable"
			},
			{
				icon: A,
				label: "Canonical agents",
				value: Cz(i),
				detail: "Current registry count"
			}
		].map((e) => {
			let t = e.icon;
			return /* @__PURE__ */ (0, Y.jsxs)("article", {
				className: "agentic-operations-summary-card",
				children: [
					/* @__PURE__ */ (0, Y.jsx)("span", {
						className: "agentic-operations-summary-icon",
						"aria-hidden": "true",
						children: /* @__PURE__ */ (0, Y.jsx)(t, { size: 17 })
					}),
					/* @__PURE__ */ (0, Y.jsx)("span", {
						className: "agentic-operations-summary-label",
						children: e.label
					}),
					/* @__PURE__ */ (0, Y.jsx)("strong", { children: e.value }),
					/* @__PURE__ */ (0, Y.jsx)("span", {
						className: "agentic-operations-summary-detail",
						children: e.detail
					})
				]
			}, e.label);
		})
	});
}
function Fz({ pipeline: e }) {
	if ((e == null ? void 0 : e.available) !== !0) {
		let t = (e == null ? void 0 : e.state) || "unavailable";
		return /* @__PURE__ */ (0, Y.jsxs)("section", {
			className: "agentic-operations-card agentic-operations-current",
			"aria-labelledby": "agenticOperationsCurrentTitle",
			children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "agentic-operations-section-heading",
				children: [/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", {
					className: "agentic-operations-eyebrow",
					children: "Runtime readback"
				}), /* @__PURE__ */ (0, Y.jsx)("h2", {
					id: "agenticOperationsCurrentTitle",
					children: "Current pipeline"
				})] }), /* @__PURE__ */ (0, Y.jsx)("span", {
					className: `agentic-operations-status agentic-operations-status--${Mz(t)}`,
					children: Sz(t)
				})]
			}), /* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "agentic-operations-unavailable",
				children: [/* @__PURE__ */ (0, Y.jsx)(Ee, {
					size: 20,
					"aria-hidden": "true"
				}), /* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: Sz(t) }), /* @__PURE__ */ (0, Y.jsx)("p", { children: Oz(t) })] })]
			})]
		});
	}
	let t = Array.isArray(e.completed_stages) ? e.completed_stages.length : null, n = Array.isArray(e.stage_order) ? e.stage_order.length : null, r = t !== null && n !== null && n > 0, i = r ? Math.min(100, Math.max(0, t / n * 100)) : 0, a = e.updated_at_utc || e.updated_at;
	return /* @__PURE__ */ (0, Y.jsxs)("section", {
		className: "agentic-operations-card agentic-operations-current",
		"aria-labelledby": "agenticOperationsCurrentTitle",
		children: [
			/* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "agentic-operations-section-heading",
				children: [/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", {
					className: "agentic-operations-eyebrow",
					children: "Runtime readback"
				}), /* @__PURE__ */ (0, Y.jsx)("h2", {
					id: "agenticOperationsCurrentTitle",
					children: "Current pipeline"
				})] }), /* @__PURE__ */ (0, Y.jsx)("span", {
					className: `agentic-operations-status agentic-operations-status--${Mz(e.status)}`,
					children: Sz(e.status, "Unknown")
				})]
			}),
			/* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "agentic-operations-stage-hero",
				children: [/* @__PURE__ */ (0, Y.jsx)("span", {
					className: "agentic-operations-stage-icon",
					"aria-hidden": "true",
					children: /* @__PURE__ */ (0, Y.jsx)(Ae, { size: 21 })
				}), /* @__PURE__ */ (0, Y.jsxs)("div", { children: [
					/* @__PURE__ */ (0, Y.jsx)("span", { children: "Current stage" }),
					/* @__PURE__ */ (0, Y.jsx)("h3", { children: Sz(e.current_stage) }),
					/* @__PURE__ */ (0, Y.jsx)("p", { children: xz(e.stage_message) || "No stage message recorded." })
				] })]
			}),
			r ? /* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "agentic-operations-progress-block",
				children: [/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Recorded stage progress" }), /* @__PURE__ */ (0, Y.jsxs)("strong", { children: [
					t,
					" of ",
					n
				] })] }), /* @__PURE__ */ (0, Y.jsx)("div", {
					className: "agentic-operations-progress-track",
					role: "progressbar",
					"aria-valuemin": 0,
					"aria-valuemax": n,
					"aria-valuenow": t,
					children: /* @__PURE__ */ (0, Y.jsx)("span", { style: { width: `${i}%` } })
				})]
			}) : null,
			/* @__PURE__ */ (0, Y.jsxs)("dl", {
				className: "agentic-operations-detail-grid",
				children: [
					/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("dt", { children: "Run ID" }), /* @__PURE__ */ (0, Y.jsx)("dd", {
						title: xz(e.run_id),
						children: xz(e.run_id) || "Unavailable"
					})] }),
					/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("dt", { children: "Stage started" }), /* @__PURE__ */ (0, Y.jsx)("dd", { children: Dz(e.stage_started_at) })] }),
					/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("dt", { children: "Updated" }), /* @__PURE__ */ (0, Y.jsx)("dd", { children: Dz(a) })] }),
					/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("dt", { children: "Final job count" }), /* @__PURE__ */ (0, Y.jsx)("dd", { children: Cz(e.final_job_count) })] }),
					/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("dt", { children: "Return code" }), /* @__PURE__ */ (0, Y.jsx)("dd", { children: e.return_code === null || e.return_code === void 0 || e.return_code === "" ? "Unavailable" : String(e.return_code) })] })
				]
			})
		]
	});
}
function Iz(e) {
	return Dz(e.completed_at || e.updated_at || e.started_at);
}
function Lz({ payload: e, selectedRunId: t, onSelect: n }) {
	let r = e.recent_runs_state, i = Array.isArray(e.recent_runs) ? e.recent_runs : [];
	return /* @__PURE__ */ (0, Y.jsxs)("section", {
		className: "agentic-operations-card agentic-operations-runs",
		"aria-labelledby": "agenticOperationsRunsTitle",
		children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "agentic-operations-section-heading",
			children: [/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", {
				className: "agentic-operations-eyebrow",
				children: "Owner-scoped history"
			}), /* @__PURE__ */ (0, Y.jsx)("h2", {
				id: "agenticOperationsRunsTitle",
				children: "Recent pipeline runs"
			})] }), /* @__PURE__ */ (0, Y.jsx)("span", {
				className: "agentic-operations-section-meta",
				children: (r == null ? void 0 : r.available) === !0 ? `${Cz(r.count)} recorded` : "Unavailable"
			})]
		}), (r == null ? void 0 : r.available) === !0 ? i.length === 0 ? /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "agentic-operations-empty",
			children: [/* @__PURE__ */ (0, Y.jsx)(ae, {
				size: 20,
				"aria-hidden": "true"
			}), /* @__PURE__ */ (0, Y.jsx)("strong", { children: "No recent runs recorded" })]
		}) : /* @__PURE__ */ (0, Y.jsx)("div", {
			className: "agentic-operations-run-list",
			role: "list",
			children: i.map((e, r) => {
				let i = xz(e.run_id), a = !!(i && i === t);
				return /* @__PURE__ */ (0, Y.jsxs)("article", {
					className: `agentic-operations-run-row${a ? " is-selected" : ""}`,
					role: "listitem",
					children: [
						/* @__PURE__ */ (0, Y.jsxs)("div", {
							className: "agentic-operations-run-primary",
							children: [
								/* @__PURE__ */ (0, Y.jsx)("span", {
									className: `agentic-operations-status agentic-operations-status--${Mz(e.status)}`,
									children: Sz(e.status, "Unknown")
								}),
								/* @__PURE__ */ (0, Y.jsx)("strong", {
									title: i,
									children: i || "Run ID unavailable"
								}),
								/* @__PURE__ */ (0, Y.jsx)("span", { children: Iz(e) })
							]
						}),
						/* @__PURE__ */ (0, Y.jsxs)("div", {
							className: "agentic-operations-run-stage",
							children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: xz(e.current_stage) ? Sz(e.current_stage) : "Final stage unavailable" }), /* @__PURE__ */ (0, Y.jsx)("small", { children: xz(e.stage_message) || xz(e.summary_message) || "No run message recorded" })]
						}),
						/* @__PURE__ */ (0, Y.jsxs)("div", {
							className: "agentic-operations-run-count",
							children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Final jobs" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: Cz(e.final_job_count) })]
						}),
						/* @__PURE__ */ (0, Y.jsx)("div", {
							className: "agentic-operations-run-action",
							children: i ? /* @__PURE__ */ (0, Y.jsx)("input", {
								type: "button",
								className: "agentic-operations-inspect",
								value: a ? "Selected" : "Inspect",
								"aria-label": `${a ? "Selected" : "Inspect"} pipeline run ${i}`,
								"aria-pressed": a,
								onClick: () => n(i)
							}) : /* @__PURE__ */ (0, Y.jsx)("span", { children: "Inspection unavailable" })
						})
					]
				}, `${i || "run"}-${r}`);
			})
		}) : /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "agentic-operations-unavailable agentic-operations-unavailable--compact",
			children: [/* @__PURE__ */ (0, Y.jsx)(ae, {
				size: 19,
				"aria-hidden": "true"
			}), /* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: "Recent runs unavailable" }), /* @__PURE__ */ (0, Y.jsx)("p", { children: "Owner-scoped pipeline history could not be read." })] })]
		})]
	});
}
function Rz({ run: e }) {
	if (!e) return /* @__PURE__ */ (0, Y.jsxs)("section", {
		className: "agentic-operations-card agentic-operations-inspector",
		"aria-labelledby": "agenticOperationsInspectorTitle",
		children: [/* @__PURE__ */ (0, Y.jsx)("div", {
			className: "agentic-operations-section-heading",
			children: /* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", {
				className: "agentic-operations-eyebrow",
				children: "Recorded run summary"
			}), /* @__PURE__ */ (0, Y.jsx)("h2", {
				id: "agenticOperationsInspectorTitle",
				children: "Run Inspector"
			})] })
		}), /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "agentic-operations-inspector-empty",
			children: [/* @__PURE__ */ (0, Y.jsx)(ae, {
				size: 20,
				"aria-hidden": "true"
			}), /* @__PURE__ */ (0, Y.jsx)("strong", { children: "Select a recent pipeline run to inspect its recorded summary." })]
		})]
	});
	let t = xz(e.run_id), n = xz(e.stage_message) || xz(e.summary_message), r = xz(e.error), i = xz(e.completed_at || e.updated_at || e.started_at), a = xz(e.current_stage), o = typeof e.final_job_count == "number" && Number.isFinite(e.final_job_count), s = e.return_code !== null && e.return_code !== void 0 && e.return_code !== "";
	return /* @__PURE__ */ (0, Y.jsxs)("section", {
		className: "agentic-operations-card agentic-operations-inspector",
		"aria-labelledby": "agenticOperationsInspectorTitle",
		children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "agentic-operations-section-heading",
			children: [/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", {
				className: "agentic-operations-eyebrow",
				children: "Recorded run summary"
			}), /* @__PURE__ */ (0, Y.jsx)("h2", {
				id: "agenticOperationsInspectorTitle",
				children: "Run Inspector"
			})] }), xz(e.status) ? /* @__PURE__ */ (0, Y.jsx)("span", {
				className: `agentic-operations-status agentic-operations-status--${Mz(e.status)}`,
				children: Sz(e.status)
			}) : null]
		}), /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "agentic-operations-inspector-content",
			children: [
				/* @__PURE__ */ (0, Y.jsxs)("dl", {
					className: "agentic-operations-inspector-grid",
					children: [
						/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("dt", { children: "Run ID" }), /* @__PURE__ */ (0, Y.jsx)("dd", {
							title: t,
							children: t
						})] }),
						i ? /* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("dt", { children: "Recorded at" }), /* @__PURE__ */ (0, Y.jsx)("dd", { children: Iz(e) })] }) : null,
						a ? /* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("dt", { children: "Current / final stage" }), /* @__PURE__ */ (0, Y.jsx)("dd", { children: Sz(a) })] }) : null,
						o ? /* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("dt", { children: "Final job count" }), /* @__PURE__ */ (0, Y.jsx)("dd", { children: String(e.final_job_count) })] }) : null,
						s ? /* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("dt", { children: "Return code" }), /* @__PURE__ */ (0, Y.jsx)("dd", { children: String(e.return_code) })] }) : null
					]
				}),
				n ? /* @__PURE__ */ (0, Y.jsxs)("p", {
					className: "agentic-operations-inspector-message",
					children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Recorded message" }), n]
				}) : null,
				r ? /* @__PURE__ */ (0, Y.jsxs)("p", {
					className: "agentic-operations-inspector-error",
					children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Recorded error" }), r]
				}) : null,
				/* @__PURE__ */ (0, Y.jsxs)("a", {
					className: "agentic-operations-review-link",
					href: `/profile/pipeline-runs/${encodeURIComponent(t)}/agentic-review`,
					children: ["Open Agentic Review ", /* @__PURE__ */ (0, Y.jsx)(ce, {
						size: 14,
						"aria-hidden": "true"
					})]
				})
			]
		})]
	});
}
function zz({ value: e, trueLabel: t, falseLabel: n, unavailableLabel: r }) {
	let i = e === !0 ? "yes" : e === !1 ? "no" : "unavailable", a = i === "yes" ? t : i === "no" ? n : r;
	return /* @__PURE__ */ (0, Y.jsxs)("span", {
		className: `agentic-operations-declaration agentic-operations-declaration--${i}`,
		children: [i === "yes" ? /* @__PURE__ */ (0, Y.jsx)(M, {
			size: 13,
			"aria-hidden": "true"
		}) : /* @__PURE__ */ (0, Y.jsx)(_e, {
			size: 13,
			"aria-hidden": "true"
		}), /* @__PURE__ */ (0, Y.jsx)("span", { children: a })]
	});
}
function Bz({ registry: e }) {
	return /* @__PURE__ */ (0, Y.jsxs)("section", {
		className: "agentic-operations-card agentic-operations-registry",
		"aria-labelledby": "agenticOperationsRegistryTitle",
		children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "agentic-operations-section-heading",
			children: [/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", {
				className: "agentic-operations-eyebrow",
				children: "Declared capabilities"
			}), /* @__PURE__ */ (0, Y.jsx)("h2", {
				id: "agenticOperationsRegistryTitle",
				children: "Canonical Agent Registry"
			})] }), /* @__PURE__ */ (0, Y.jsx)("span", {
				className: "agentic-operations-section-meta",
				children: e.state === "available" ? `${e.agents.length} registered` : "Unavailable"
			})]
		}), e.state === "available" ? /* @__PURE__ */ (0, Y.jsxs)(Y.Fragment, { children: [/* @__PURE__ */ (0, Y.jsx)("div", {
			className: "agentic-operations-agent-grid",
			children: e.agents.map((e, t) => /* @__PURE__ */ (0, Y.jsxs)("article", {
				className: "agentic-operations-agent-card",
				children: [
					/* @__PURE__ */ (0, Y.jsxs)("div", {
						className: "agentic-operations-agent-heading",
						children: [/* @__PURE__ */ (0, Y.jsx)("span", {
							className: "agentic-operations-agent-icon",
							"aria-hidden": "true",
							children: /* @__PURE__ */ (0, Y.jsx)(A, { size: 17 })
						}), /* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Canonical definition" }), /* @__PURE__ */ (0, Y.jsx)("h3", { children: xz(e.display_name) })] })]
					}),
					/* @__PURE__ */ (0, Y.jsx)("p", { children: xz(e.responsibility) }),
					/* @__PURE__ */ (0, Y.jsxs)("div", {
						className: "agentic-operations-declarations",
						"aria-label": `${xz(e.display_name)} declared capabilities`,
						children: [
							/* @__PURE__ */ (0, Y.jsx)(zz, {
								value: e.deterministic_core,
								trueLabel: "Deterministic core",
								falseLabel: "Non-deterministic core",
								unavailableLabel: "Deterministic core unavailable"
							}),
							/* @__PURE__ */ (0, Y.jsx)(zz, {
								value: e.llm_capable,
								trueLabel: "LLM capable",
								falseLabel: "Not LLM capable",
								unavailableLabel: "LLM capability unavailable"
							}),
							/* @__PURE__ */ (0, Y.jsx)(zz, {
								value: e.optional_controlled_llm_guardrail,
								trueLabel: "Controlled LLM guardrail available",
								falseLabel: "Controlled LLM guardrail not available",
								unavailableLabel: "Controlled LLM guardrail unavailable"
							}),
							/* @__PURE__ */ (0, Y.jsx)(zz, {
								value: e.advisory_only,
								trueLabel: "Advisory only",
								falseLabel: "Not advisory-only",
								unavailableLabel: "Advisory status unavailable"
							}),
							/* @__PURE__ */ (0, Y.jsx)(zz, {
								value: e.human_approval_required,
								trueLabel: "Human approval required",
								falseLabel: "Human approval not required by definition",
								unavailableLabel: "Human approval requirement unavailable"
							})
						]
					})
				]
			}, `${xz(e.key)}-${t}`))
		}), e.invalidCount > 0 ? /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "agentic-operations-registry-note",
			role: "status",
			children: [
				/* @__PURE__ */ (0, Y.jsx)(Ee, {
					size: 16,
					"aria-hidden": "true"
				}),
				e.invalidCount,
				" malformed canonical ",
				e.invalidCount === 1 ? "definition was" : "definitions were",
				" not rendered."
			]
		}) : null] }) : /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "agentic-operations-registry-empty",
			children: [/* @__PURE__ */ (0, Y.jsx)(A, {
				size: 20,
				"aria-hidden": "true"
			}), /* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: e.state === "empty" ? "No canonical agent definitions returned" : "Canonical registry unavailable" }), /* @__PURE__ */ (0, Y.jsx)("p", { children: "No canonical agents are fabricated when registry data is absent or malformed." })] })]
		})]
	});
}
function Vz({ value: e, label: t }) {
	let n = e === !0 ? "yes" : e === !1 ? "no" : "unavailable", r = n === "yes" ? "Yes" : n === "no" ? "No" : "Unavailable";
	return /* @__PURE__ */ (0, Y.jsxs)("span", {
		className: `agentic-operations-authority agentic-operations-authority--${n}`,
		"aria-label": `${t}: ${r}`,
		children: [n === "yes" ? /* @__PURE__ */ (0, Y.jsx)(M, {
			size: 13,
			"aria-hidden": "true"
		}) : /* @__PURE__ */ (0, Y.jsx)(_e, {
			size: 13,
			"aria-hidden": "true"
		}), /* @__PURE__ */ (0, Y.jsx)("span", { children: r })]
	});
}
function Hz({ registry: e, summary: t }) {
	let n = Tz(e.agents, t);
	return /* @__PURE__ */ (0, Y.jsxs)("section", {
		className: "agentic-operations-card agentic-operations-matrix",
		"aria-labelledby": "agenticOperationsMatrixTitle",
		children: [
			/* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "agentic-operations-section-heading",
				children: [/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", {
					className: "agentic-operations-eyebrow",
					children: "Declared mutation authority"
				}), /* @__PURE__ */ (0, Y.jsx)("h2", {
					id: "agenticOperationsMatrixTitle",
					children: "Safety / Mutation Authority Matrix"
				})] }), /* @__PURE__ */ (0, Y.jsx)("span", {
					className: "agentic-operations-section-meta",
					children: "Registry definitions"
				})]
			}),
			n ? /* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "agentic-operations-consistency-warning",
				role: "status",
				children: [/* @__PURE__ */ (0, Y.jsx)(Ee, {
					size: 17,
					"aria-hidden": "true"
				}), /* @__PURE__ */ (0, Y.jsx)("span", { children: "Registry capability totals do not match the returned safety summary." })]
			}) : null,
			e.state === "available" ? /* @__PURE__ */ (0, Y.jsx)("div", {
				className: "agentic-operations-matrix-scroll",
				children: /* @__PURE__ */ (0, Y.jsxs)("table", { children: [
					/* @__PURE__ */ (0, Y.jsx)("caption", { children: "Declared mutation authority by canonical agent" }),
					/* @__PURE__ */ (0, Y.jsx)("thead", { children: /* @__PURE__ */ (0, Y.jsxs)("tr", { children: [/* @__PURE__ */ (0, Y.jsx)("th", {
						scope: "col",
						children: "Canonical agent"
					}), yz.map((e) => /* @__PURE__ */ (0, Y.jsx)("th", {
						scope: "col",
						children: e.label
					}, e.field))] }) }),
					/* @__PURE__ */ (0, Y.jsx)("tbody", { children: e.agents.map((e, t) => /* @__PURE__ */ (0, Y.jsxs)("tr", { children: [/* @__PURE__ */ (0, Y.jsx)("th", {
						scope: "row",
						children: xz(e.display_name)
					}), yz.map((t) => /* @__PURE__ */ (0, Y.jsx)("td", { children: /* @__PURE__ */ (0, Y.jsx)(Vz, {
						value: e[t.field],
						label: t.label
					}) }, t.field))] }, `${xz(e.key)}-${t}`)) })
				] })
			}) : /* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "agentic-operations-registry-empty agentic-operations-registry-empty--compact",
				children: [/* @__PURE__ */ (0, Y.jsx)(Te, {
					size: 20,
					"aria-hidden": "true"
				}), /* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: "Mutation authority unavailable" }), /* @__PURE__ */ (0, Y.jsx)("p", { children: "No authoritative per-agent rows were returned." })] })]
			})
		]
	});
}
function Uz({ payload: e, confirmed: t }) {
	let n = !!e.safety_metadata, r = e.safety_summary, i = [
		["Canonical agents", r == null ? void 0 : r.canonical_agent_count],
		["Queue mutation capable", r == null ? void 0 : r.queue_mutation_capable_count],
		["Resume mutation capable", r == null ? void 0 : r.resume_text_mutation_capable_count],
		["Application-action capable", r == null ? void 0 : r.application_action_capable_count]
	];
	return /* @__PURE__ */ (0, Y.jsxs)("section", {
		className: `agentic-operations-safety ${t ? "is-confirmed" : "is-attention"}`,
		"aria-labelledby": "agenticOperationsSafetyTitle",
		children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "agentic-operations-safety-copy",
			children: [/* @__PURE__ */ (0, Y.jsx)("span", {
				className: "agentic-operations-safety-icon",
				"aria-hidden": "true",
				children: t ? /* @__PURE__ */ (0, Y.jsx)(Te, { size: 21 }) : /* @__PURE__ */ (0, Y.jsx)(Ee, { size: 21 })
			}), /* @__PURE__ */ (0, Y.jsxs)("div", { children: [
				/* @__PURE__ */ (0, Y.jsx)("span", {
					className: "agentic-operations-eyebrow",
					children: "Contract boundary"
				}),
				/* @__PURE__ */ (0, Y.jsx)("div", {
					className: "agentic-operations-safety-title-row",
					children: /* @__PURE__ */ (0, Y.jsx)("h2", {
						id: "agenticOperationsSafetyTitle",
						children: "Safety overview"
					})
				}),
				/* @__PURE__ */ (0, Y.jsx)("p", { children: t ? "The returned contract confirms admin-only readback with no reported operational side effects." : n ? "Safety metadata is inconsistent with the expected read-only contract." : "Safety metadata is unavailable; no read-only success claim is shown." })
			] })]
		}), /* @__PURE__ */ (0, Y.jsx)("dl", {
			className: "agentic-operations-safety-metrics",
			children: i.map(([e, t]) => /* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("dt", { children: e }), /* @__PURE__ */ (0, Y.jsx)("dd", { children: Cz(t) })] }, e))
		})]
	});
}
function Wz({ readOverview: e = vz }) {
	let [t, n] = (0, C.useState)({ kind: "loading" }), [r, i] = (0, C.useState)(!1), [a, o] = (0, C.useState)(null), s = (0, C.useRef)(null), c = (0, C.useCallback)((t = !1) => {
		if (s.current) return s.current;
		t && i(!0);
		let r = e().then((e) => n({
			kind: "ready",
			payload: e
		})).catch((e) => n({
			kind: "error",
			message: e instanceof Error ? e.message : "Agentic Operations overview is unavailable."
		})).finally(() => {
			s.current = null, t && i(!1);
		});
		return s.current = r, r;
	}, [e]);
	(0, C.useEffect)(() => {
		c();
	}, [c]);
	let l = t.kind === "ready" && Array.isArray(t.payload.recent_runs) ? t.payload.recent_runs : [], u = a && l.find((e) => xz(e.run_id) === a) || null;
	(0, C.useEffect)(() => {
		t.kind === "ready" && a && !u && o(null);
	}, [
		u,
		a,
		t.kind
	]);
	let d = t.kind === "ready" && Az(t.payload), f = t.kind === "ready" ? wz(t.payload.canonical_agents) : null;
	return /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "agentic-operations-dashboard",
		"aria-busy": t.kind === "loading" || r,
		children: [
			/* @__PURE__ */ (0, Y.jsx)(jz, { confirmed: d }),
			/* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "agentic-operations-toolbar",
				children: [/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", {
					className: "agentic-operations-eyebrow",
					children: "Operations overview"
				}), /* @__PURE__ */ (0, Y.jsx)("p", { children: "Live readback for the current owner-scoped pipeline and canonical agent safety boundary." })] }), /* @__PURE__ */ (0, Y.jsxs)("button", {
					type: "button",
					className: "agentic-operations-refresh",
					onClick: () => void c(!0),
					disabled: r || t.kind === "loading",
					children: [/* @__PURE__ */ (0, Y.jsx)(be, {
						size: 15,
						"aria-hidden": "true",
						className: r ? "is-spinning" : ""
					}), r ? "Refreshing…" : "Refresh overview"]
				})]
			}),
			t.kind === "loading" ? /* @__PURE__ */ (0, Y.jsx)(Nz, {}) : null,
			t.kind === "error" ? /* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "agentic-operations-error",
				role: "alert",
				children: [/* @__PURE__ */ (0, Y.jsx)(Ee, {
					size: 20,
					"aria-hidden": "true"
				}), /* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: "Overview unavailable" }), /* @__PURE__ */ (0, Y.jsx)("p", { children: t.message })] })]
			}) : null,
			t.kind === "ready" && f ? /* @__PURE__ */ (0, Y.jsxs)(Y.Fragment, { children: [
				/* @__PURE__ */ (0, Y.jsx)(Pz, { payload: t.payload }),
				/* @__PURE__ */ (0, Y.jsxs)("div", {
					className: "agentic-operations-primary-grid",
					children: [/* @__PURE__ */ (0, Y.jsx)(Fz, { pipeline: t.payload.current_pipeline }), /* @__PURE__ */ (0, Y.jsx)(Lz, {
						payload: t.payload,
						selectedRunId: a,
						onSelect: o
					})]
				}),
				/* @__PURE__ */ (0, Y.jsx)(Rz, { run: u }),
				/* @__PURE__ */ (0, Y.jsx)(Uz, {
					payload: t.payload,
					confirmed: d
				}),
				/* @__PURE__ */ (0, Y.jsx)(Bz, { registry: f }),
				/* @__PURE__ */ (0, Y.jsx)(Hz, {
					registry: f,
					summary: t.payload.safety_summary
				})
			] }) : null
		]
	});
}
//#endregion
//#region src/PlanningWorklist.tsx
var Gz = "applylens:planning-worklist-state", Kz = "applylens:planning-worklist-action", qz = "applylens.planning.columnWidths.v1", Jz = {
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
}, Yz = [
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
], Xz = [
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
], Zz = [
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
], Qz = {
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
function $z(e) {
	window.dispatchEvent(new CustomEvent(Kz, { detail: e }));
}
function eB(e) {
	return String(e == null ? "" : e).trim();
}
function tB(e) {
	let t = eB(e).replace(/_/g, " ");
	return t ? t.charAt(0).toUpperCase() + t.slice(1) : "Unavailable";
}
function nB(e) {
	let t = eB(e);
	return t ? t.replace(/\.pdf$/i, "").replace(/_/g, " ") : "Not selected";
}
function rB(e) {
	return eB(e.operator_selected_resume || e.selected_resume || e.winner_resume);
}
function iB(e) {
	let t = eB(e);
	if (!t) return "Unavailable";
	let n = new Date(t);
	return Number.isNaN(n.getTime()) ? t : new Intl.DateTimeFormat(void 0, {
		month: "short",
		day: "numeric",
		year: "numeric"
	}).format(n);
}
function aB(e) {
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
	}[eB(e.action).toUpperCase()] || {
		label: eB(e.action) || "Unavailable",
		tone: "unavailable"
	};
}
function oB(e) {
	let t = eB(e).toLowerCase();
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
function sB() {
	try {
		let e = JSON.parse(localStorage.getItem("applylens.planning.columnWidths.v1") || "{}");
		if (!e || typeof e != "object" || Array.isArray(e)) return {};
		let t = "version" in e && e.version === 1 ? e.widths : e;
		return !t || typeof t != "object" || Array.isArray(t) ? {} : Object.fromEntries(Object.entries(t).flatMap(([e, t]) => {
			let n = Qz[e], r = Number(t);
			return !n || !Number.isFinite(r) ? [] : [[e, Math.min(n.max, Math.max(n.min, r))]];
		}));
	} catch (e) {
		return {};
	}
}
function cB(e) {
	localStorage.setItem(qz, JSON.stringify({
		version: 1,
		widths: e
	}));
}
function lB(e, t) {
	return eB(e.job_doc_id || e.job_url || e.queue_rank) || `planning-row-${t}`;
}
function uB(e) {
	if (e && typeof e == "object" && !Array.isArray(e)) return e;
	let t = eB(e);
	if (!t) return null;
	try {
		let e = JSON.parse(t);
		return e && typeof e == "object" && !Array.isArray(e) ? e : null;
	} catch (e) {
		return null;
	}
}
function dB({ row: e }) {
	let t = uB(e.llm_adjudicator_readback), n = eB((t == null ? void 0 : t.status) || e.llm_adjudicator_readback_status || "Unavailable"), r = Array.isArray(t == null ? void 0 : t.candidate_resume_names) ? t.candidate_resume_names.map(eB).filter(Boolean).join(", ") : "", i = [
		["Status", tB(n)],
		["Provider", eB((t == null ? void 0 : t.provider_used) || (t == null ? void 0 : t.provider_requested))],
		["Model", eB((t == null ? void 0 : t.model_used) || (t == null ? void 0 : t.model_requested))],
		["Candidates", r],
		["Recommendation", eB(t == null ? void 0 : t.adjudicator_recommendation_label)],
		["Summary", eB(t == null ? void 0 : t.adjudicator_summary)]
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
function fB({ row: e }) {
	let t = [
		"true",
		"1",
		"yes",
		"on"
	].includes(eB(e.llm_adjudicator_readback_enabled).toLowerCase());
	return /* @__PURE__ */ (0, Y.jsxs)($I, { children: [/* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "planning-react-details-grid",
		children: [
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Full location" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: eB(e.job_location) || "Unavailable" })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Prefilter relevance" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: tB(e.selection_signal) })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "AI evaluation" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: tB(e.llm_adjudicator_readback_status) })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Runner-up resume" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: nB(e.runner_up_resume || e.runnerup_resume) })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Runner-up score" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: eB(e.runner_up_score) || "Unavailable" })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Score gap" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: eB(e.score_gap) || "Unavailable" })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Operator decision" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: tB(e.operator_decision || "Not decided") })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Priority reason" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: eB(e.queue_priority_reason) || "Unavailable" })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Missing requirements" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: eB(e.missing_requirement_count) || "0" })] })
		]
	}), t ? /* @__PURE__ */ (0, Y.jsx)(dB, { row: e }) : null] });
}
function pB() {
	return [
		{
			id: "expand",
			header: "",
			size: 42,
			minSize: 42,
			maxSize: 42,
			enableSorting: !1,
			enableResizing: !1,
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)(YI, {
				expanded: e.getIsExpanded(),
				label: `${e.getIsExpanded() ? "Collapse" : "Expand"} planning details for ${eB(e.original.job_title) || "job"}`,
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
			accessorFn: (e) => eB(e.job_title),
			cell: ({ row: e }) => {
				let t = eB(e.original.job_title) || "Untitled job", n = eB(e.original.job_company) || "Company unavailable", r = eB(e.original.job_location) || "Location unavailable", i = eB(e.original.job_url || e.original.job_doc_id);
				return /* @__PURE__ */ (0, Y.jsx)(QI, {
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
				dateTime: eB(e.original.posted_at),
				children: iB(e.original.posted_at)
			})
		},
		{
			id: "recommendation",
			header: "Review readiness",
			size: 184,
			minSize: 150,
			maxSize: 260,
			accessorFn: (e) => aB(e).label,
			cell: ({ row: e }) => {
				let t = aB(e.original), n = [
					"true",
					"1",
					"yes",
					"on"
				].includes(eB(e.original.llm_adjudicator_readback_enabled).toLowerCase());
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
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)(XI, {
				value: e.original.winner_score,
				strength: tB(e.original.winner_bucket)
			})
		},
		{
			id: "selected_resume",
			header: "Resume selection",
			size: 230,
			minSize: 200,
			maxSize: 360,
			accessorFn: rB,
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)("span", {
				className: "planning-react-resume",
				title: rB(e.original),
				children: nB(rB(e.original))
			})
		},
		{
			id: "packet_status",
			header: () => /* @__PURE__ */ (0, Y.jsxs)("span", {
				className: "planning-react-packet-header",
				children: ["Packet / workspace", /* @__PURE__ */ (0, Y.jsx)(ZI, {
					label: "About packet and workspace status",
					children: "A packet is a review bundle for this job. It does not apply to the job."
				})]
			}),
			size: 188,
			minSize: 160,
			maxSize: 280,
			accessorFn: (e) => oB(e.packet_generation_allowed),
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsxs)("span", {
				className: "planning-react-status-stack",
				children: [/* @__PURE__ */ (0, Y.jsx)("span", {
					className: `planning-react-badge ${oB(e.original.packet_generation_allowed) === "Packet ready" ? "is-ready" : ""}`,
					children: oB(e.original.packet_generation_allowed)
				}), /* @__PURE__ */ (0, Y.jsx)("span", { children: tB(e.original.tailoring_workspace_state || "Workspace unavailable") })]
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
					onClick: () => $z({
						type: "next_step",
						row: e.original
					}),
					children: t.label
				});
			}
		}
	];
}
function mB({ state: e }) {
	let [t, n] = (0, C.useState)(e.filters);
	(0, C.useEffect)(() => n(e.filters), [e.filters]);
	let r = (e) => {
		n(e), $z({
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
			/* @__PURE__ */ (0, Y.jsx)(qI, {
				id: "planningActionFilter",
				label: "Action",
				options: Yz,
				values: t.actions,
				onChange: (e) => r({
					...t,
					actions: e
				}),
				placeholder: "All",
				mode: "single"
			}),
			/* @__PURE__ */ (0, Y.jsx)(qI, {
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
			/* @__PURE__ */ (0, Y.jsx)(qI, {
				id: "planningWinnerBucket",
				label: "Match Strength",
				options: Xz,
				values: t.winnerBuckets,
				onChange: (e) => r({
					...t,
					winnerBuckets: e
				}),
				placeholder: "All",
				mode: "single"
			}),
			/* @__PURE__ */ (0, Y.jsx)(qI, {
				id: "planningTailoringFilter",
				label: "Tailoring",
				options: Zz,
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
						className: `${JI} ${t.undecidedOnly ? "" : "is-active"}`.trim(),
						onClick: () => r({
							...t,
							undecidedOnly: !1
						}),
						children: "No"
					}), /* @__PURE__ */ (0, Y.jsx)("button", {
						type: "button",
						"aria-pressed": t.undecidedOnly,
						className: `${JI} ${t.undecidedOnly ? "is-active" : ""}`.trim(),
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
					onClick: () => $z({
						type: "apply_filters",
						filters: t
					}),
					children: "Apply Filters"
				}), /* @__PURE__ */ (0, Y.jsx)("button", {
					type: "button",
					className: "planning-filter-clear",
					id: "planningClearFiltersBtn",
					onClick: () => $z({ type: "clear_filters" }),
					children: "Clear"
				})]
			})
		]
	});
}
function hB({ state: e }) {
	let [t, n] = (0, C.useState)(sB), [r, i] = (0, C.useState)(""), a = (0, C.useMemo)(pB, []), o = (0, C.useMemo)(() => e.rows.slice(), [e.rows]), s = (0, C.useMemo)(() => e.sort.key ? [{
		id: e.sort.key,
		desc: e.sort.direction === "desc"
	}] : [], [e.sort]);
	(0, C.useEffect)(() => i(""), [
		e.resultKey,
		e.pagination.page,
		e.sort.key,
		e.sort.direction
	]);
	let c = WI({
		data: o,
		columns: a,
		state: {
			sorting: s,
			columnSizing: t,
			expanded: r ? { [r]: !0 } : {}
		},
		getRowId: lB,
		onSortingChange: (e) => {
			let t = (typeof e == "function" ? e(s) : e)[0];
			t && (i(""), $z({
				type: "sort_change",
				key: t.id,
				direction: t.desc ? "desc" : "asc"
			}));
		},
		onColumnSizingChange: (e) => {
			n((t) => {
				let n = typeof e == "function" ? e(t) : e;
				return cB(n), n;
			});
		},
		onExpandedChange: (e) => {
			let t = r ? { [r]: !0 } : {}, n = typeof e == "function" ? e(t) : e, a = n === !0 ? t : n, o = Object.keys(a).find((e) => a[e] && !t[e]);
			i(o || Object.keys(a).find((e) => a[e]) || "");
		},
		getRowCanExpand: () => !0,
		getCoreRowModel: RI(),
		manualSorting: !0,
		enableSortingRemoval: !1,
		columnResizeMode: "onChange"
	});
	return /* @__PURE__ */ (0, Y.jsx)(rL, {
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
		renderDetails: (e) => /* @__PURE__ */ (0, Y.jsx)(fB, { row: e.original }),
		empty: /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "planning-react-empty",
			children: [
				/* @__PURE__ */ (0, Y.jsx)("strong", { children: "No planning rows match these filters" }),
				/* @__PURE__ */ (0, Y.jsx)("span", { children: "Clear the current filters to return to the complete planning worklist." }),
				/* @__PURE__ */ (0, Y.jsx)("button", {
					type: "button",
					className: JI,
					onClick: () => $z({ type: "clear_filters" }),
					children: "Clear filters"
				})
			]
		}),
		onPageChange: (e) => $z({
			type: "page_change",
			page: e
		}),
		onRetry: () => $z({ type: "retry" })
	});
}
var gB = [
	{
		key: "total",
		label: "Total results",
		caption: "Across all result pages",
		help: "All planning rows matching the applied filters.",
		icon: ie
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
		icon: de
	},
	{
		key: "needsDecision",
		label: "Needs decision",
		caption: "Operator attention",
		help: "Rows on this page that do not yet have an operator decision.",
		icon: De
	}
];
function _B({ state: e }) {
	return /* @__PURE__ */ (0, Y.jsx)("section", {
		className: "planning-react-summary-grid",
		"aria-label": "Planning summary",
		children: gB.map((t) => {
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
						}), /* @__PURE__ */ (0, Y.jsx)(ZI, {
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
var vB = "applylens:decisions-dashboard-state", yB = "applylens:decisions-dashboard-action", bB = "applylens:decisions-dashboard-ready", xB = "applylens:applications-dashboard-state", SB = "applylens:applications-dashboard-action", CB = "applylens:applications-dashboard-ready", wB = "applylens.decisions.columnWidths.v1", TB = "applylens.applications.columnWidths.v1", EB = {
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
}, DB = {
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
}, OB = [
	"APPLY",
	"TAILOR",
	"SKIP",
	"HOLD"
].map((e) => ({
	value: e,
	label: e
})), $ = (e) => String(e == null ? "" : e).trim(), kB = (e, t = "Unavailable") => $(e) || t, AB = (e) => {
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
}, jB = (e, t) => $(e.action_key) || [
	$(e.decision_timestamp || e.action_timestamp),
	$(e.job_doc_id || e.job_url),
	$(e.decision || e.application_status),
	t
].join("|"), MB = (e) => e.key ? [{
	id: e.key,
	desc: e.direction === "desc"
}] : [];
function NB(e, t) {
	window.dispatchEvent(new CustomEvent(e, { detail: t }));
}
function PB(e) {
	try {
		let t = JSON.parse(localStorage.getItem(e) || "{}"), n = (t == null ? void 0 : t.version) === 1 ? t.widths : t;
		return n && typeof n == "object" && !Array.isArray(n) ? n : {};
	} catch (e) {
		return {};
	}
}
function FB(e, t) {
	localStorage.setItem(e, JSON.stringify({
		version: 1,
		widths: t
	}));
}
function IB(e, t) {
	let n = kB(e);
	return /* @__PURE__ */ (0, Y.jsx)("span", {
		className: `${t}-badge ${t}-badge--${$(e).toLowerCase().replace(/[^a-z0-9]+/g, "-") || "unknown"}`,
		children: n
	});
}
function LB({ cards: e, label: t, loading: n = !1 }) {
	return /* @__PURE__ */ (0, Y.jsx)("section", {
		className: "operational-summary-grid",
		"aria-label": t,
		children: e.map(({ label: e, value: t, caption: r, help: i, icon: a }) => /* @__PURE__ */ (0, Y.jsxs)("article", {
			className: "operational-summary-card",
			children: [
				/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsxs)("span", { children: [/* @__PURE__ */ (0, Y.jsx)(a, {
					size: 17,
					"aria-hidden": "true"
				}), e] }), /* @__PURE__ */ (0, Y.jsx)(ZI, {
					label: `About ${e.toLowerCase()}`,
					children: i
				})] }),
				/* @__PURE__ */ (0, Y.jsx)("strong", { children: n ? "-" : t }),
				/* @__PURE__ */ (0, Y.jsx)("small", { children: n ? "Loading snapshot" : r })
			]
		}, e))
	});
}
function RB({ state: e }) {
	let [t, n] = (0, C.useState)(e.filters);
	return (0, C.useEffect)(() => n(e.filters), [e.filters]), /* @__PURE__ */ (0, Y.jsx)("section", {
		className: "operational-filter-card",
		"aria-label": "Decision filters",
		children: /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "operational-filter-grid decisions-filter-grid",
			children: [
				/* @__PURE__ */ (0, Y.jsx)(qI, {
					id: "decisionFilter",
					label: "Decision",
					options: OB,
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
						onClick: () => NB(yB, {
							type: "apply_filters",
							filters: t
						}),
						children: "Apply Filters"
					}), /* @__PURE__ */ (0, Y.jsx)("button", {
						id: "decisionClearFiltersBtn",
						className: `${JI} operational-secondary-action`,
						onClick: () => NB(yB, { type: "clear_filters" }),
						children: "Clear"
					})]
				})
			]
		})
	});
}
function zB({ row: e }) {
	return /* @__PURE__ */ (0, Y.jsx)($I, { children: /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "operational-detail-grid",
		children: [
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Queue rank" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: kB(e.queue_rank) })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Posted at" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: AB(e.posted_at) })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Winner resume" }), /* @__PURE__ */ (0, Y.jsx)("strong", {
				title: $(e.winner_resume),
				children: kB(e.winner_resume)
			})] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Runner-up resume" }), /* @__PURE__ */ (0, Y.jsx)("strong", {
				title: $(e.runner_up_resume),
				children: kB(e.runner_up_resume)
			})] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Selected resume" }), /* @__PURE__ */ (0, Y.jsx)("strong", {
				title: $(e.selected_resume),
				children: kB(e.selected_resume)
			})] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Note" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: kB(e.note, "No note recorded") })] })
		]
	}) });
}
function BB() {
	return [
		{
			id: "expand",
			header: "",
			size: 42,
			minSize: 42,
			maxSize: 42,
			enableSorting: !1,
			enableResizing: !1,
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)(YI, {
				expanded: e.getIsExpanded(),
				label: `${e.getIsExpanded() ? "Collapse" : "Expand"} decision details for ${kB(e.original.job_title, "job")}`,
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
				children: AB(e.original.decision_timestamp)
			})
		},
		{
			id: "decision",
			header: "Decision",
			accessorFn: (e) => $(e.decision),
			size: 118,
			cell: ({ row: e }) => IB(e.original.decision, "operational")
		},
		{
			id: "job",
			header: "Job",
			accessorFn: (e) => $(e.job_title),
			size: 270,
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsxs)("span", {
				className: "operational-job-cell",
				children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: kB(e.original.job_title, "Untitled job") }), /* @__PURE__ */ (0, Y.jsx)("span", { children: kB(e.original.job_company, "Company unavailable") })]
			})
		},
		{
			id: "planning_action",
			header: "Planning action",
			accessorFn: (e) => $(e.planning_action),
			size: 150,
			cell: ({ row: e }) => kB(e.original.planning_action)
		},
		{
			id: "selected_resume",
			header: "Selected resume",
			accessorFn: (e) => $(e.selected_resume),
			size: 220,
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)("span", {
				className: "operational-truncate",
				title: $(e.original.selected_resume),
				children: kB(e.original.selected_resume)
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
				onClick: () => NB(yB, {
					type: "open_application",
					row: e.original
				}),
				children: "Open job"
			})
		}
	];
}
function VB({ state: e }) {
	let [t, n] = (0, C.useState)(() => PB(wB)), [r, i] = (0, C.useState)(""), a = (0, C.useMemo)(BB, []), o = (0, C.useMemo)(() => MB(e.sort), [e.sort]);
	(0, C.useEffect)(() => i(""), [
		e.resultKey,
		e.pagination.page,
		e.sort
	]);
	let s = WI({
		data: e.rows,
		columns: a,
		state: {
			sorting: o,
			columnSizing: t,
			expanded: r ? { [r]: !0 } : {}
		},
		getRowId: jB,
		getCoreRowModel: RI(),
		getSortedRowModel: zI(),
		getRowCanExpand: () => !0,
		enableSortingRemoval: !1,
		columnResizeMode: "onChange",
		onSortingChange: (e) => {
			let t = (typeof e == "function" ? e(o) : e)[0];
			t && NB(yB, {
				type: "sort_change",
				key: t.id,
				direction: t.desc ? "desc" : "asc"
			});
		},
		onColumnSizingChange: (e) => n((t) => {
			let n = typeof e == "function" ? e(t) : e;
			return FB(wB, n), n;
		}),
		onExpandedChange: (e) => {
			let t = r ? { [r]: !0 } : {}, n = typeof e == "function" ? e(t) : e, a = n === !0 ? t : n;
			i(Object.keys(a).find((e) => a[e] && e !== r) || Object.keys(a).find((e) => a[e]) || "");
		}
	});
	return /* @__PURE__ */ (0, Y.jsx)(rL, {
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
		renderDetails: (e) => /* @__PURE__ */ (0, Y.jsx)(zB, { row: e.original }),
		empty: /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "operational-empty",
			children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: "No operator decisions match the current filters." }), /* @__PURE__ */ (0, Y.jsx)("button", {
				className: JI,
				onClick: () => NB(yB, { type: "clear_filters" }),
				children: "Clear filters"
			})]
		}),
		onPageChange: (e) => NB(yB, {
			type: "page_change",
			page: e
		}),
		onRetry: () => NB(yB, { type: "retry" }),
		fillAvailableWidth: !0,
		deferPaginationWhileLoading: !0
	});
}
function HB({ state: e }) {
	let t = e.rows, n = new Set(t.map((e) => $(e.job_doc_id || e.job_url || `${e.job_company}|${e.job_title}`)).filter(Boolean));
	return /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "operational-dashboard",
		children: [
			/* @__PURE__ */ (0, Y.jsx)(LB, {
				cards: [
					{
						label: "Total decisions",
						value: e.pagination.totalCount,
						caption: "Across filtered results",
						help: "All recorded decisions matching the applied filters.",
						icon: re
					},
					{
						label: "Jobs touched",
						value: n.size,
						caption: "On this page",
						help: "Distinct jobs represented on the current page.",
						icon: j
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
						icon: de
					}
				],
				label: "Decision summary",
				loading: e.status === "loading"
			}),
			/* @__PURE__ */ (0, Y.jsx)(RB, { state: e }),
			/* @__PURE__ */ (0, Y.jsx)(VB, { state: e })
		]
	});
}
function UB({ state: e }) {
	let [t, n] = (0, C.useState)(e.filters);
	(0, C.useEffect)(() => n(e.filters), [e.filters]);
	let r = (t) => {
		t !== e.activeTab && NB(SB, {
			type: "tab_change",
			tab: t
		});
	}, i = (e, t) => {
		e.key !== "ArrowLeft" && e.key !== "ArrowRight" || (e.preventDefault(), r(t === "APPLIED" ? "SAVED" : "APPLIED"));
	}, a = (e) => `${JI} applications-tab ${e ? "is-active" : "is-inactive"}`;
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
						onClick: () => NB(SB, {
							type: "apply_filters",
							filters: t
						}),
						children: "Apply Filters"
					}), /* @__PURE__ */ (0, Y.jsx)("button", {
						id: "applicationClearFiltersBtn",
						className: `${JI} operational-secondary-action`,
						onClick: () => NB(SB, { type: "clear_filters" }),
						children: "Clear"
					})]
				})
			]
		})]
	});
}
function WB({ row: e }) {
	return /* @__PURE__ */ (0, Y.jsx)($I, { children: /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "operational-detail-grid",
		children: [
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Complete timestamp" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: AB(e.action_timestamp) })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Source view" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: kB(e.source_view) })] }),
			/* @__PURE__ */ (0, Y.jsxs)("div", {
				className: "is-wide",
				children: [/* @__PURE__ */ (0, Y.jsx)("span", { children: "Note" }), /* @__PURE__ */ (0, Y.jsx)("strong", { children: kB(e.note, "No note recorded") })]
			})
		]
	}) });
}
function GB() {
	return [
		{
			id: "expand",
			header: "",
			size: 42,
			minSize: 42,
			maxSize: 42,
			enableSorting: !1,
			enableResizing: !1,
			cell: ({ row: e }) => e.getCanExpand() ? /* @__PURE__ */ (0, Y.jsx)(YI, {
				expanded: e.getIsExpanded(),
				label: `${e.getIsExpanded() ? "Collapse" : "Expand"} application details for ${kB(e.original.job_title, "job")}`,
				controls: `application-detail-${e.id}`,
				onClick: e.getToggleExpandedHandler()
			}) : null
		},
		{
			id: "action_timestamp",
			header: "Date / time",
			accessorFn: (e) => $(e.action_timestamp),
			size: 156,
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)("time", { children: AB(e.original.action_timestamp) })
		},
		{
			id: "job",
			header: "Job",
			accessorFn: (e) => $(e.job_title),
			size: 300,
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsxs)("span", {
				className: "operational-job-cell",
				children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: kB(e.original.job_title, "Untitled job") }), /* @__PURE__ */ (0, Y.jsx)("span", { children: kB(e.original.job_company, "Company unavailable") })]
			})
		},
		{
			id: "application_status",
			header: "Status",
			accessorFn: (e) => $(e.application_status),
			size: 130,
			cell: ({ row: e }) => IB(e.original.application_status, "application")
		},
		{
			id: "source_view",
			header: "Source view",
			accessorFn: (e) => $(e.source_view),
			size: 140,
			cell: ({ row: e }) => kB(e.original.source_view)
		},
		{
			id: "note",
			header: "Note",
			accessorFn: (e) => $(e.note),
			size: 230,
			cell: ({ row: e }) => /* @__PURE__ */ (0, Y.jsx)("span", {
				className: "operational-truncate",
				title: $(e.original.note),
				children: kB(e.original.note, "No note")
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
function KB({ state: e }) {
	let [t, n] = (0, C.useState)(() => PB(TB)), [r, i] = (0, C.useState)(""), a = (0, C.useMemo)(GB, []), o = (0, C.useMemo)(() => MB(e.sort), [e.sort]);
	(0, C.useEffect)(() => i(""), [
		e.resultKey,
		e.activeTab,
		e.pagination.page,
		e.sort
	]);
	let s = WI({
		data: e.rows,
		columns: a,
		state: {
			sorting: o,
			columnSizing: t,
			expanded: r ? { [r]: !0 } : {}
		},
		getRowId: jB,
		getCoreRowModel: RI(),
		getSortedRowModel: zI(),
		getRowCanExpand: (e) => !!$(e.original.note),
		enableSortingRemoval: !1,
		columnResizeMode: "onChange",
		onSortingChange: (e) => {
			let t = (typeof e == "function" ? e(o) : e)[0];
			t && NB(SB, {
				type: "sort_change",
				key: t.id,
				direction: t.desc ? "desc" : "asc"
			});
		},
		onColumnSizingChange: (e) => n((t) => {
			let n = typeof e == "function" ? e(t) : e;
			return FB(TB, n), n;
		}),
		onExpandedChange: (e) => {
			let t = r ? { [r]: !0 } : {}, n = typeof e == "function" ? e(t) : e, a = n === !0 ? t : n;
			i(Object.keys(a).find((e) => a[e] && e !== r) || Object.keys(a).find((e) => a[e]) || "");
		}
	}), c = e.activeTab === "APPLIED" ? "Applied Jobs" : "Saved for Later", l = e.activeTab === "APPLIED" ? "No applied jobs yet." : "No jobs have been saved for later.";
	return /* @__PURE__ */ (0, Y.jsx)(rL, {
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
		renderDetails: (e) => /* @__PURE__ */ (0, Y.jsx)(WB, { row: e.original }),
		empty: /* @__PURE__ */ (0, Y.jsxs)("div", {
			className: "operational-empty",
			children: [/* @__PURE__ */ (0, Y.jsx)("strong", { children: l }), /* @__PURE__ */ (0, Y.jsx)("span", { children: e.activeTab === "APPLIED" ? "Applied jobs will appear after an explicit manual status update." : "Jobs explicitly saved for later will appear here." })]
		}),
		onPageChange: (e) => NB(SB, {
			type: "page_change",
			page: e
		}),
		onRetry: () => NB(SB, { type: "retry" }),
		fillAvailableWidth: !0,
		deferPaginationWhileLoading: !0
	});
}
function qB({ state: e }) {
	return /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "operational-dashboard",
		children: [
			/* @__PURE__ */ (0, Y.jsx)(LB, {
				cards: [
					{
						label: "Current view",
						value: e.pagination.totalCount,
						caption: e.activeTab === "APPLIED" ? "Applied jobs" : "Saved jobs",
						help: "All jobs in the active view matching the applied filters.",
						icon: fe
					},
					{
						label: "Current page",
						value: e.rows.length,
						caption: "Visible jobs",
						help: "Jobs returned on the current server page.",
						icon: j
					},
					{
						label: "With notes",
						value: e.rows.filter((e) => $(e.note)).length,
						caption: "On this page",
						help: "Current-page jobs with a recorded operator note.",
						icon: de
					},
					{
						label: "Companies",
						value: new Set(e.rows.map((e) => $(e.job_company)).filter(Boolean)).size,
						caption: "On this page",
						help: "Distinct companies represented on the current page.",
						icon: Oe
					}
				],
				label: "Application summary",
				loading: e.status === "loading"
			}),
			/* @__PURE__ */ (0, Y.jsx)(UB, { state: e }),
			/* @__PURE__ */ (0, Y.jsx)(KB, { state: e })
		]
	});
}
//#endregion
//#region src/main.tsx
var JB = "applylens:executive-kpi-state", YB = { status: "loading" };
function XB() {
	let [e, t] = (0, C.useState)(() => window.__APPLYLENS_SOURCE_YIELD_STATE__ || fF);
	return (0, C.useEffect)(() => {
		let e = (e) => {
			let n = e.detail;
			n != null && n.status && t(n);
		};
		return window.addEventListener(dF, e), () => window.removeEventListener(dF, e);
	}, []), /* @__PURE__ */ (0, Y.jsx)(CF, { state: e });
}
function ZB() {
	let [e, t] = (0, C.useState)(() => window.__APPLYLENS_EXECUTIVE_KPI_STATE__ || YB);
	return (0, C.useEffect)(() => {
		let e = (e) => {
			let n = e.detail;
			n != null && n.status && t(n);
		};
		return window.addEventListener(JB, e), () => window.removeEventListener(JB, e);
	}, []), /* @__PURE__ */ (0, Y.jsx)(uF, { state: e });
}
function QB() {
	let [e, t] = (0, C.useState)(() => window.__APPLYLENS_EXECUTIVE_QUEUE_STATE__ || cL);
	return (0, C.useEffect)(() => {
		let e = (e) => {
			let n = e.detail;
			n != null && n.status && t(n);
		};
		return window.addEventListener(iL, e), () => window.removeEventListener(iL, e);
	}, []), /* @__PURE__ */ (0, Y.jsx)(DL, { state: e });
}
function $B({ view: e }) {
	let [t, n] = (0, C.useState)(() => window.__APPLYLENS_PLANNING_WORKLIST_STATE__ || Jz);
	return (0, C.useEffect)(() => {
		let e = (e) => {
			let t = e.detail;
			t != null && t.status && n(t);
		};
		return window.addEventListener(Gz, e), () => window.removeEventListener(Gz, e);
	}, []), e === "filters" ? /* @__PURE__ */ (0, Y.jsx)(mB, { state: t }) : e === "summary" ? /* @__PURE__ */ (0, Y.jsx)(_B, { state: t }) : /* @__PURE__ */ (0, Y.jsx)(hB, { state: t });
}
function eV() {
	let [e, t] = (0, C.useState)(() => window.__APPLYLENS_DECISIONS_STATE__ || EB);
	return (0, C.useEffect)(() => {
		let e = (e) => t(e.detail);
		return window.addEventListener(vB, e), window.__APPLYLENS_DECISIONS_REACT_READY__ = !0, window.__APPLYLENS_DECISIONS_STATE__ && t(window.__APPLYLENS_DECISIONS_STATE__), window.dispatchEvent(new CustomEvent(bB)), () => window.removeEventListener(vB, e);
	}, []), /* @__PURE__ */ (0, Y.jsx)(HB, { state: e });
}
function tV() {
	let [e, t] = (0, C.useState)(() => window.__APPLYLENS_APPLICATIONS_STATE__ || DB);
	return (0, C.useEffect)(() => {
		let e = (e) => t(e.detail);
		return window.addEventListener(xB, e), window.__APPLYLENS_APPLICATIONS_REACT_READY__ = !0, window.__APPLYLENS_APPLICATIONS_STATE__ && t(window.__APPLYLENS_APPLICATIONS_STATE__), window.dispatchEvent(new CustomEvent(CB)), () => window.removeEventListener(xB, e);
	}, []), /* @__PURE__ */ (0, Y.jsx)(qB, { state: e });
}
var nV = document.getElementById("executiveKpiRoot");
nV && (0, nF.createRoot)(nV).render(/* @__PURE__ */ (0, Y.jsx)(C.StrictMode, { children: /* @__PURE__ */ (0, Y.jsx)(ZB, {}) }));
var rV = document.getElementById("executiveQueueRoot");
rV && (0, nF.createRoot)(rV).render(/* @__PURE__ */ (0, Y.jsx)(C.StrictMode, { children: /* @__PURE__ */ (0, Y.jsx)(QB, {}) }));
var iV = document.getElementById("sourceYieldRoot");
iV && (0, nF.createRoot)(iV).render(/* @__PURE__ */ (0, Y.jsx)(C.StrictMode, { children: /* @__PURE__ */ (0, Y.jsx)(XB, {}) }));
var aV = document.getElementById("pipelineDashboardRoot");
aV && (0, nF.createRoot)(aV).render(/* @__PURE__ */ (0, Y.jsx)(C.StrictMode, { children: /* @__PURE__ */ (0, Y.jsx)(sR, {}) }));
var oV = document.getElementById("planningSummaryRoot");
oV && (0, nF.createRoot)(oV).render(/* @__PURE__ */ (0, Y.jsx)(C.StrictMode, { children: /* @__PURE__ */ (0, Y.jsx)($B, { view: "summary" }) }));
var sV = document.getElementById("planningFiltersRoot");
sV && (0, nF.createRoot)(sV).render(/* @__PURE__ */ (0, Y.jsx)(C.StrictMode, { children: /* @__PURE__ */ (0, Y.jsx)($B, { view: "filters" }) }));
var cV = document.getElementById("planningWorklistRoot");
cV && (0, nF.createRoot)(cV).render(/* @__PURE__ */ (0, Y.jsx)(C.StrictMode, { children: /* @__PURE__ */ (0, Y.jsx)($B, { view: "worklist" }) }));
var lV = document.getElementById("decisionsDashboardRoot");
lV && (0, nF.createRoot)(lV).render(/* @__PURE__ */ (0, Y.jsx)(C.StrictMode, { children: /* @__PURE__ */ (0, Y.jsx)(eV, {}) }));
var uV = document.getElementById("applicationsDashboardRoot");
uV && (0, nF.createRoot)(uV).render(/* @__PURE__ */ (0, Y.jsx)(C.StrictMode, { children: /* @__PURE__ */ (0, Y.jsx)(tV, {}) }));
var dV = document.getElementById("schedulerHealthDashboardRoot");
dV && (0, nF.createRoot)(dV).render(/* @__PURE__ */ (0, Y.jsx)(C.StrictMode, { children: /* @__PURE__ */ (0, Y.jsx)(YR, {}) }));
var fV = document.getElementById("agenticOperationsRoot");
fV && (0, nF.createRoot)(fV).render(/* @__PURE__ */ (0, Y.jsx)(C.StrictMode, { children: /* @__PURE__ */ (0, Y.jsx)(Wz, {}) }));
var pV = document.getElementById("advancedDiagnosticsRoot");
pV && (0, nF.createRoot)(pV).render(/* @__PURE__ */ (0, Y.jsx)(C.StrictMode, { children: /* @__PURE__ */ (0, Y.jsx)(_z, { state: window.__APPLYLENS_ADVANCED_DIAGNOSTICS_STATE__ || XR }) }));
//#endregion
