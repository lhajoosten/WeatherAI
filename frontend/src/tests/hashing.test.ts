// Tests for hashing utilities

import { describe, it, expect } from 'vitest';

import { sha256, shortHash, hashValues, simpleHash } from '@/shared/lib/hashing';

describe('Hashing Utilities', () => {
  describe('simpleHash', () => {
    it('should generate consistent hash for same input', () => {
      const text = 'Hello, World!';
      const hash1 = simpleHash(text);
      const hash2 = simpleHash(text);
      
      expect(hash1).toBe(hash2);
      expect(typeof hash1).toBe('number');
    });

    it('should generate different hashes for different inputs', () => {
      const hash1 = simpleHash('Hello');
      const hash2 = simpleHash('World');
      
      expect(hash1).not.toBe(hash2);
    });

    it('should handle empty string', () => {
      const hash = simpleHash('');
      expect(typeof hash).toBe('number');
      expect(hash).toBe(0);
    });
  });

  describe('sha256', () => {
    it('should generate SHA-256 hash', async () => {
      const text = 'Hello, World!';
      const hash = await sha256(text);
      
      expect(typeof hash).toBe('string');
      expect(hash).toHaveLength(64); // SHA-256 produces 64-character hex string
      expect(hash).toMatch(/^[a-f0-9]+$/); // Should be valid hex
    });

    it('should generate consistent hash for same input', async () => {
      const text = 'Test message';
      const hash1 = await sha256(text);
      const hash2 = await sha256(text);
      
      expect(hash1).toBe(hash2);
    });

    it('should generate different hashes for different inputs', async () => {
      const hash1 = await sha256('Input 1');
      const hash2 = await sha256('Input 2');
      
      expect(hash1).not.toBe(hash2);
    });

    it('should handle empty string', async () => {
      const hash = await sha256('');
      expect(typeof hash).toBe('string');
      expect(hash).toHaveLength(64);
    });
  });

  describe('shortHash', () => {
    it('should generate 8-character hash', async () => {
      const text = 'Hello, World!';
      const hash = await shortHash(text);
      
      expect(typeof hash).toBe('string');
      expect(hash).toHaveLength(8);
      expect(hash).toMatch(/^[a-f0-9]+$/);
    });

    it('should be consistent', async () => {
      const text = 'Test message';
      const hash1 = await shortHash(text);
      const hash2 = await shortHash(text);
      
      expect(hash1).toBe(hash2);
    });
  });

  describe('hashValues', () => {
    it('should hash multiple values consistently', async () => {
      const hash1 = await hashValues('user123', 'session456', true);
      const hash2 = await hashValues('user123', 'session456', true);
      
      expect(hash1).toBe(hash2);
      expect(typeof hash1).toBe('string');
      expect(hash1).toHaveLength(64);
    });

    it('should produce different hashes for different value combinations', async () => {
      const hash1 = await hashValues('user123', 'session456');
      const hash2 = await hashValues('user123', 'session789');
      
      expect(hash1).not.toBe(hash2);
    });

    it('should handle mixed types', async () => {
      const hash = await hashValues('string', 123, true, false);
      
      expect(typeof hash).toBe('string');
      expect(hash).toHaveLength(64);
    });

    it('should handle empty values', async () => {
      const hash = await hashValues();
      
      expect(typeof hash).toBe('string');
      expect(hash).toHaveLength(64);
    });
  });
});