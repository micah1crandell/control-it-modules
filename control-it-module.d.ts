/**
 * Control-It Community Module Driver TypeScript Definitions
 * Version: 2.1.0
 * 
 * Use this definition file in your IDE (e.g. VS Code) to author,
 * typecheck, and validate custom hardware driver scripts for Control-It.
 */

export interface ModuleConfig {
  host: string;
  port: number;
  [key: string]: any;
}

export interface HTTPResponse {
  status: number;
  data: string;
  json: any;
  headers: Record<string, string>;
  ok: boolean;
}

export interface JSONStreamParser {
  /** Pushes incoming stream data and returns an array of successfully parsed JSON objects */
  push(chunk: string | number[] | Buffer): any[];
  /** Clears the internal stream buffer */
  clear(): void;
  /** Returns current unparsed residual buffer */
  getBuffer(): string;
}

export interface Transport {
  /** Sends raw UTF-8 text down the persistent connection */
  send(text: string): boolean;
  /** Sends an array of raw bytes down the persistent connection */
  sendBytes(bytes: number[] | Uint8Array | Buffer): boolean;
  /** Sends a hex string (e.g. "81 01 04 00 02 FF") as raw binary */
  sendHex(hexString: string): boolean;
  /** Serializes an object to JSON and sends it over the transport */
  sendJSON(object: Record<string, any>): boolean;
  /**
   * Sends a payload and awaits a matching response from the remote device.
   * @param payload Text string, byte array, or JSON object to transmit
   * @param matcher Expected substring or custom matching function
   * @param timeoutMs Timeout in milliseconds (default: 5000)
   */
  sendAndAwait<T = string>(
    payload: string | number[] | Record<string, any> | Buffer,
    matcher: string | ((text: string, bytes: number[]) => boolean | T),
    timeoutMs?: number
  ): Promise<T>;
}

export interface EngineBuffer {
  create(size: number): number[];
  fromHex(hexStr: string): number[];
  toHex(bufferOrBytes: number[] | Buffer): string;
  
  readUInt8(buffer: number[] | Buffer, offset?: number): number;
  readInt8(buffer: number[] | Buffer, offset?: number): number;
  writeUInt8(buffer: number[] | Buffer, offset: number, value: number): number[];
  writeInt8(buffer: number[] | Buffer, offset: number, value: number): number[];

  readUInt16BE(buffer: number[] | Buffer, offset?: number): number;
  readUInt16LE(buffer: number[] | Buffer, offset?: number): number;
  readInt16BE(buffer: number[] | Buffer, offset?: number): number;
  readInt16LE(buffer: number[] | Buffer, offset?: number): number;
  writeUInt16BE(buffer: number[] | Buffer, offset: number, value: number): number[];
  writeUInt16LE(buffer: number[] | Buffer, offset: number, value: number): number[];
  writeInt16BE(buffer: number[] | Buffer, offset: number, value: number): number[];
  writeInt16LE(buffer: number[] | Buffer, offset: number, value: number): number[];

  readUInt32BE(buffer: number[] | Buffer, offset?: number): number;
  readUInt32LE(buffer: number[] | Buffer, offset?: number): number;
  readInt32BE(buffer: number[] | Buffer, offset?: number): number;
  readInt32LE(buffer: number[] | Buffer, offset?: number): number;
  writeUInt32BE(buffer: number[] | Buffer, offset: number, value: number): number[];
  writeUInt32LE(buffer: number[] | Buffer, offset: number, value: number): number[];
  writeInt32BE(buffer: number[] | Buffer, offset: number, value: number): number[];
  writeInt32LE(buffer: number[] | Buffer, offset: number, value: number): number[];

  readBigUInt64BE(buffer: number[] | Buffer, offset?: number): string;
  readBigUInt64LE(buffer: number[] | Buffer, offset?: number): string;
  readBigInt64BE(buffer: number[] | Buffer, offset?: number): string;
  readBigInt64LE(buffer: number[] | Buffer, offset?: number): string;
  writeBigUInt64BE(buffer: number[] | Buffer, offset: number, value: string | bigint): number[];
  writeBigUInt64LE(buffer: number[] | Buffer, offset: number, value: string | bigint): number[];
  writeBigInt64BE(buffer: number[] | Buffer, offset: number, value: string | bigint): number[];
  writeBigInt64LE(buffer: number[] | Buffer, offset: number, value: string | bigint): number[];

  readFloatBE(buffer: number[] | Buffer, offset?: number): number;
  readFloatLE(buffer: number[] | Buffer, offset?: number): number;
  writeFloatBE(buffer: number[] | Buffer, offset: number, value: number): number[];
  writeFloatLE(buffer: number[] | Buffer, offset: number, value: number): number[];

  readDoubleBE(buffer: number[] | Buffer, offset?: number): number;
  readDoubleLE(buffer: number[] | Buffer, offset?: number): number;
  writeDoubleBE(buffer: number[] | Buffer, offset: number, value: number): number[];
  writeDoubleLE(buffer: number[] | Buffer, offset: number, value: number): number[];

  readString(buffer: number[] | Buffer, offset: number, length: number): string;
  writeString(buffer: number[] | Buffer, offset: number, string: string): number[];
  subdata(buffer: number[] | Buffer, start: number, end: number): number[];
  slice(buffer: number[] | Buffer, start: number, end: number): number[];
  concat(buf1: number[] | Buffer, buf2: number[] | Buffer): number[];
}

export interface EngineCrypto {
  sha256(text: string): string;
  sha1(text: string): string;
  md5(text: string): string;
  hmacSHA256(key: string, message: string): string;
  base64Encode(text: string): string;
  base64Decode(base64Str: string): string;
}

export interface EngineChecksum {
  crc16(bytes: number[] | Buffer, poly: number, initial: number, refIn: boolean, refOut: boolean, xorOut: number): number;
  crc16Modbus(bytes: number[] | Buffer): number;
  crc16CCITT(bytes: number[] | Buffer): number;
  crc16XMODEM(bytes: number[] | Buffer): number;
  xor(bytes: number[] | Buffer): number;
  sum8(bytes: number[] | Buffer): number;
  twosComplement(bytes: number[] | Buffer): number;
}

export interface EngineOSC {
  encode(address: string, args: (string | number | boolean | number[])[]): number[];
  decode(bytes: number[] | Buffer): { address: string; args: any[] } | null;
}

export interface EngineBinary {
  pack(format: string, values: any[]): number[];
  unpack(format: string, bytes: number[] | Buffer): any[];
}

export interface EngineHTTP {
  /** Asynchronous HTTP GET returning a Promise */
  get(url: string, headers?: Record<string, string>): Promise<HTTPResponse>;
  /** Asynchronous HTTP POST returning a Promise */
  post(url: string, body?: string | Record<string, any>, headers?: Record<string, string>): Promise<HTTPResponse>;
}

export interface EngineTelnet {
  /** Strips Telnet IAC control escape sequences (0xFF ...) from raw byte stream */
  stripIAC(bytes: number[] | Buffer): number[];
  /** Auto-generates WONT/DONT rejection responses to Telnet DO/WILL negotiations */
  negotiate(bytes: number[] | Buffer): number[];
}

export interface EngineStream {
  /** Creates an accumulator parser for continuous, delimiter-less JSON socket streams */
  createJSONParser(): JSONStreamParser;
}

export interface Engine {
  buffer: EngineBuffer;
  crypto: EngineCrypto;
  checksum: EngineChecksum;
  osc: EngineOSC;
  binary: EngineBinary;
  http: EngineHTTP;
  telnet: EngineTelnet;
  stream: EngineStream;

  /** Updates a dynamic variable in Control-It for live button colors, titles, and tally feedback */
  setVariable(key: string, value: string | number | boolean): void;
  /** Bulk updates multiple dynamic variables */
  setVariables(variables: Record<string, string | number | boolean>): void;
  /** Reads current value of a dynamic variable */
  getVariable(key: string): string;

  /** Updates the driver connection state badge */
  setStatus(status: 'connected' | 'connecting' | 'authenticating' | 'failed' | 'disconnected', message: string): void;
  /** Requests an immediate connection retry */
  reconnect(): void;
  /** Reports a fatal driver error */
  fail(errorMessage: string): void;

  /** Retrieves metadata for current session (host, port, transportType, driverId) */
  getConnectionInfo(): { host: string; port: number; transportType: string; driverId: string; displayName: string };
  /** Securely retrieves a secret from iOS Keychain */
  secret(fieldKey: string): string;
  /** Logs an entry in the Driver Diagnostics console */
  log(message: string): void;
}

export interface DriverModuleExports {
  /** Invoked when socket connection is established */
  onConnect?(transport: Transport, config: ModuleConfig): void | Promise<void>;
  /** Invoked when raw data/text arrives over transport */
  onMessage?(transport: Transport, messageText: string, messageBytes: number[]): void | Promise<void>;
  /** Periodic timer hook (frequency configured in module connectionConfig) */
  onHeartbeat?(transport: Transport): void | Promise<void>;
  /** Invoked when user taps a button bound to this module's action */
  onAction?(transport: Transport, actionId: string, parameters: Record<string, any>): string | void | Promise<string | void>;
  /** Invoked when connection is closed gracefully */
  onDisconnect?(): void;
  /** Invoked when an unrecoverable error occurs */
  onError?(error: string): void;
  /** Invoked when driver session is stopped */
  onStop?(): void;
  /** Invoked immediately upon transport socket readiness */
  onTransportReady?(transport: Transport, endpoint: { host: string; port: number }): void;
}

declare global {
  const engine: Engine;
  const transport: Transport;
  const module: { exports: DriverModuleExports };
  const exports: DriverModuleExports;

  class Buffer {
    length: number;
    data: number[];
    constructor(arg: number | number[] | string, encoding?: string);
    static from(value: any, encoding?: string): Buffer;
    static alloc(size: number, fill?: number): Buffer;
    static concat(list: (Buffer | number[])[], totalLength?: number): Buffer;
    static isBuffer(obj: any): boolean;
    static byteLength(string: string, encoding?: string): number;
    readUInt8(offset?: number): number;
    readInt8(offset?: number): number;
    writeUInt8(val: number, offset?: number): number;
    writeInt8(val: number, offset?: number): number;
    readUInt16BE(offset?: number): number;
    readUInt16LE(offset?: number): number;
    writeUInt16BE(val: number, offset?: number): number;
    writeUInt16LE(val: number, offset?: number): number;
    readInt16BE(offset?: number): number;
    readInt16LE(offset?: number): number;
    writeInt16BE(val: number, offset?: number): number;
    writeInt16LE(val: number, offset?: number): number;
    readUInt32BE(offset?: number): number;
    readUInt32LE(offset?: number): number;
    writeUInt32BE(val: number, offset?: number): number;
    writeUInt32LE(val: number, offset?: number): number;
    readInt32BE(offset?: number): number;
    readInt32LE(offset?: number): number;
    writeInt32BE(val: number, offset?: number): number;
    writeInt32LE(val: number, offset?: number): number;
    readBigUInt64BE(offset?: number): string | bigint;
    readBigUInt64LE(offset?: number): string | bigint;
    writeBigUInt64BE(val: string | bigint, offset?: number): number;
    writeBigUInt64LE(val: string | bigint, offset?: number): number;
    readFloatBE(offset?: number): number;
    readFloatLE(offset?: number): number;
    writeFloatBE(val: number, offset?: number): number;
    writeFloatLE(val: number, offset?: number): number;
    readDoubleBE(offset?: number): number;
    readDoubleLE(offset?: number): number;
    writeDoubleBE(val: number, offset?: number): number;
    writeDoubleLE(val: number, offset?: number): number;
    toString(encoding?: string, start?: number, end?: number): string;
    slice(start?: number, end?: number): Buffer;
    toJSON(): { type: 'Buffer'; data: number[] };
  }

  class TextEncoder {
    encode(input?: string): number[];
  }
  class TextDecoder {
    constructor(encoding?: string);
    decode(bytes?: number[] | Uint8Array | Buffer): string;
  }
  class URLSearchParams {
    constructor(init?: string | Record<string, any>);
    get(name: string): string | null;
    set(name: string, value: string): void;
    has(name: string): boolean;
    toString(): string;
  }

  function setTimeout(fn: (...args: any[]) => void, delayMs: number): string;
  function clearTimeout(id: string): void;
  function setInterval(fn: (...args: any[]) => void, intervalMs: number): string;
  function clearInterval(id: string): void;
}
